import asyncio
import hashlib
import html as html_lib
import io
import logging
import os
import re
import secrets
import shutil
import string
import time
import zipfile

import aiohttp
import discord

try:
	from PIL import Image
	PILLOW = True
except ImportError:
	PILLOW = False
	logging.warning("Pillow not installed — images will be archived without re-encoding.")

# Max pixel dimension for re-encoded images. Bump this if you care about fidelity.
MAX_IMAGE_DIM = 1600
WEBP_QUALITY = 80

# Formats we never touch (animation / transparency-sensitive / already tiny).
SKIP_REENCODE = {"image/gif", "image/svg+xml", "image/webp"}


class ThreadArchive():
	def __init__(self, name: str, channel: discord.Thread | discord.ForumChannel | discord.TextChannel):
		self.threads = None
		self.name = self.sanitize_filename(name)
		self.channel = channel
		self.archives = []
		self.zip_path = None

		# Each run gets its own working root so parallel archives can't collide
		# and so we have one place to dedupe assets and drop a single style.css.
		self.run_id = secrets.token_hex(8)
		self.root = os.path.join("archives", f"_run_{self.run_id}")
		self.assets_dir = os.path.join(self.root, "assets")

		# sha256(original bytes) -> filename inside assets/
		self.assets: dict[str, str] = {}

		self.stats = {
			"threads": 0,
			"messages": 0,
			"embeds": 0,
			"attachments": 0,        # every attachment, image or not
			"links": 0,              # non-image attachments left as CDN links
			"images_seen": 0,        # image attachments encountered (incl. repeats)
			"images_unique": 0,      # distinct images actually written to assets/
			"bytes_seen": 0,         # sum of every image occurrence, original size
			"bytes_unique": 0,       # sum of distinct images, original size
			"bytes_stored": 0,       # what actually landed in assets/ after re-encode
			"authors": set(),
			"first_message": None,
			"last_message": None,
			"raw_bytes": 0,          # uncompressed size of everything in the zip
			"zip_bytes": 0,          # size of the zip on disk
			"elapsed": 0.0,
		}

		os.makedirs(self.assets_dir, exist_ok=True)

	def sanitize_filename(self, filename: str) -> str:
		return re.sub(r'[\\/*?:"<>|]', "", filename).strip()

	async def run(self):
		"""Main entrypoint: build the per-thread HTML, then zip it all up."""
		started = time.monotonic()

		await self.get_threads()
		await self.write_stylesheet()

		targets = list(self.threads)
		if isinstance(self.channel, discord.TextChannel) and self.channel not in targets:
			targets.append(self.channel)

		for thread in targets:
			# ensure we never lock the bot, as well as logging the process (for debugging)
			logging.info(f"Processed {self.stats['threads']} threads")
			await asyncio.sleep(0)

			archive_dir, file_path = await self.create_dir(thread)
			html = await self.thread_to_html(thread, archive_dir)
			await self.create_file(thread, html, file_path)
			self.stats["threads"] += 1

		await self.create_zip()

		self.stats["images_unique"] = len(self.assets)
		self.stats["elapsed"] = time.monotonic() - started
		logging.info(f"Finished creating archive! {self.summary_line()}")

	async def get_threads(self) -> None:
		self.threads = [self.channel]
		if self.channel.type == discord.ChannelType.forum:
			logging.info(f"Getting threads for {self.channel.name}")
			self.threads = self.channel.threads + [
				thread async for thread in self.channel.archived_threads(limit=None)
			]

	async def write_stylesheet(self) -> None:
		"""One stylesheet for the whole archive instead of a copy inlined per thread."""
		with open('resources/css/export.css', 'r') as f:
			css = f.read()
		with open(os.path.join(self.root, "style.css"), 'w', encoding='utf-8') as f:
			f.write(css)

	async def create_dir(self, thread) -> tuple[str, str]:
		name = self.sanitize_filename(thread.name.replace(" ", "_")) or str(thread.id)
		path = os.path.join(self.root, str(thread.id))
		os.makedirs(path, exist_ok=True)
		return path, os.path.join(path, f"{name}.html")

	# ------------------------------------------------------------------
	# Image handling
	# ------------------------------------------------------------------

	async def store_image(self, attachment: discord.Attachment) -> str:
		"""
		Download an image, dedupe it by content hash, optionally re-encode it,
		and return the archive-relative href to use in the HTML.
		"""
		data = await attachment.read()
		digest = hashlib.sha256(data).hexdigest()[:16]

		self.stats["images_seen"] += 1
		self.stats["bytes_seen"] += len(data)

		if digest in self.assets:
			# Already have it — this occurrence costs us nothing.
			return f"../assets/{self.assets[digest]}"

		self.stats["bytes_unique"] += len(data)

		content_type = (attachment.content_type or "").split(";")[0].lower()
		ext = os.path.splitext(attachment.filename)[1].lower() or ".bin"
		out_bytes = data
		out_name = f"{digest}{ext}"

		if PILLOW and content_type not in SKIP_REENCODE:
			try:
				out_bytes, out_name = self.optimize(data, digest)
			except Exception as e:
				# A corrupt or exotic image shouldn't kill the whole archive.
				logging.warning(f"Could not optimize {attachment.filename}: {e}")

		with open(os.path.join(self.assets_dir, out_name), 'wb') as f:
			f.write(out_bytes)

		self.stats["bytes_stored"] += len(out_bytes)
		self.assets[digest] = out_name
		return f"../assets/{out_name}"

	def optimize(self, data: bytes, digest: str) -> tuple[bytes, str]:
		"""Downscale to MAX_IMAGE_DIM and re-encode as WebP. Keeps whichever is smaller."""
		with Image.open(io.BytesIO(data)) as img:
			img = img.convert("RGBA" if img.mode in ("RGBA", "LA", "P") else "RGB")
			img.thumbnail((MAX_IMAGE_DIM, MAX_IMAGE_DIM), Image.LANCZOS)

			buf = io.BytesIO()
			img.save(buf, format="WEBP", quality=WEBP_QUALITY, method=6)
			encoded = buf.getvalue()

		if len(encoded) < len(data):
			return encoded, f"{digest}.webp"
		# Re-encoding made it bigger (happens with small PNGs / line art) — keep the original.
		return data, f"{digest}.bin"

	# ------------------------------------------------------------------
	# HTML
	# ------------------------------------------------------------------

	async def thread_to_html(self, thread, archive_path: str) -> str:
		esc = html_lib.escape

		if isinstance(thread, discord.Thread):
			header = (
				f"<h1>{esc(thread.name)}</h1>"
				f"<p>Created at: {thread.created_at.strftime('%m/%d/%Y %H:%M')}</p>"
				f"<p>Author: {esc(str(thread.owner))}</p><hr>"
			)
			sleep = 0
		else:
			header = f"<h1>{esc(thread.name)}</h1><hr>"
			sleep = 0.01

		parts = [
			"<!DOCTYPE html><html><head><meta charset='utf-8'>",
			f"<title>{esc(thread.name)}</title>",
			"<link rel='stylesheet' href='../style.css'>",
			f"</head><body>{header}",
		]

		async for message in thread.history(limit=None, oldest_first=True):
			if self.stats["messages"] % 100 == 0:
				logging.info(f"Processed {self.stats["messages"]}")
				await asyncio.sleep(0)
			if sleep:
				await asyncio.sleep(sleep)

			self.stats["messages"] += 1
			self.stats["authors"].add(message.author.id)

			created = message.created_at
			if self.stats["first_message"] is None or created < self.stats["first_message"]:
				self.stats["first_message"] = created
			if self.stats["last_message"] is None or created > self.stats["last_message"]:
				self.stats["last_message"] = created

			parts.append(
				f"<div class='message'><p><strong>{esc(str(message.author))}</strong> "
				f"at {message.created_at.strftime('%m/%d/%Y %H:%M')}:</p>"
			)

			if message.content:
				parts.append(f"<p>{esc(message.content)}</p>")

			for embed in message.embeds:
				self.stats["embeds"] += 1
				color = f"#{embed.color.value:06x}" if embed.color else "#202225"
				parts.append(f"<div class='embed' style='border-left: 4px solid {color};'>")

				if embed.author and embed.author.name:
					parts.append(f"<div class='embed-author'><strong>{esc(embed.author.name)}</strong></div>")
				if embed.title:
					parts.append(f"<div class='embed-title'>{esc(embed.title)}</div>")
				if embed.description:
					parts.append(f"<div class='embed-description'>{esc(embed.description)}</div>")

				if embed.fields:
					parts.append("<div class='embed-fields'>")
					for field in embed.fields:
						cls = "inline" if field.inline else "full"
						parts.append(
							f"<div class='embed-field {cls}'>"
							f"<strong>{esc(field.name)}</strong><br>{esc(field.value)}</div>"
						)
					parts.append("</div>")

				if embed.image and embed.image.url:
					parts.append(f"<img class='embed-image' src='{esc(embed.image.url)}' loading='lazy'>")
				if embed.footer and embed.footer.text:
					parts.append(f"<div class='embed-footer'>{esc(embed.footer.text)}</div>")

				parts.append("</div>")

			if message.attachments:
				parts.append("<div class='attachment-container'>")
				for attachment in message.attachments:
					self.stats["attachments"] += 1
					ct = (attachment.content_type or "").lower()
					if ct.startswith("image/"):
						href = await self.store_image(attachment)
						parts.append(
							f"<a href='{href}' target='_blank'>"
							f"<img src='{href}' class='attachment' loading='lazy'></a>"
						)
					else:
						self.stats["links"] += 1
						parts.append(
							f"<p><a href='{esc(attachment.url)}' target='_blank'>"
							f"{esc(attachment.filename)}</a></p>"
						)
				parts.append("</div>")

			parts.append("</div><hr>")

		parts.append("</body></html>")
		return "".join(parts)

	async def create_file(self, thread, html: str, file_path: str):
		with open(file_path, 'w', encoding='utf-8') as f:
			f.write(html)
		self.archives.append(thread.id)

	# ------------------------------------------------------------------
	# Zip
	# ------------------------------------------------------------------

	async def create_zip(self):
		"""DEFLATE the text, store the images (already compressed — deflating them wastes CPU for ~0 gain)."""
		zip_path = os.path.join("archives", f"{self.name}.zip")
		stored_ext = {".webp", ".png", ".jpg", ".jpeg", ".gif", ".bin"}

		raw = 0
		with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
			for foldername, _subfolders, filenames in os.walk(self.root):
				for filename in filenames:
					full = os.path.join(foldername, filename)
					arcname = os.path.relpath(full, self.root)
					ext = os.path.splitext(filename)[1].lower()
					ctype = zipfile.ZIP_STORED if ext in stored_ext else zipfile.ZIP_DEFLATED
					zf.write(full, arcname, compress_type=ctype)
					raw += os.path.getsize(full)

		self.zip_path = zip_path
		self.stats["raw_bytes"] = raw
		self.stats["zip_bytes"] = os.stat(zip_path).st_size

	async def clean_up(self):
		shutil.rmtree(self.root, ignore_errors=True)
		if self.zip_path and os.path.exists(self.zip_path):
			os.remove(self.zip_path)



	@staticmethod
	def human_bytes(n: int) -> str:
		for unit in ("B", "KB", "MB", "GB"):
			if abs(n) < 1024 or unit == "GB":
				return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
			n /= 1024
		return f"{n:.1f} GB"

	def report(self) -> dict:
		"""Everything a caller might want, with the derived numbers already worked out."""
		s = self.stats
		dedup_saved = s["bytes_seen"] - s["bytes_unique"]
		reencode_saved = s["bytes_unique"] - s["bytes_stored"]
		zip_saved = s["raw_bytes"] - s["zip_bytes"]

		return {
			"threads": s["threads"],
			"messages": s["messages"],
			"authors": len(s["authors"]),
			"embeds": s["embeds"],
			"attachments": s["attachments"],
			"images": s["images_seen"],
			"images_unique": s["images_unique"],
			"links": s["links"],
			"first_message": s["first_message"],
			"last_message": s["last_message"],
			"elapsed": s["elapsed"],
			"zip_bytes": s["zip_bytes"],
			"raw_bytes": s["raw_bytes"],
			"dedup_saved": dedup_saved,
			"reencode_saved": reencode_saved,
			"zip_saved": zip_saved,
			"total_saved": dedup_saved + reencode_saved + zip_saved,
			"compression_ratio": (s["zip_bytes"] / s["raw_bytes"]) if s["raw_bytes"] else 0.0,
		}

	def summary_line(self) -> str:
		"""One-liner for the logs."""
		r = self.report()
		return (
			f"{r['threads']} threads, {r['messages']} messages, "
			f"{r['images_unique']}/{r['images']} unique images, "
			f"{self.human_bytes(r['zip_bytes'])} zip "
			f"(saved {self.human_bytes(r['total_saved'])}) in {r['elapsed']:.1f}s"
		)

	def summary_embed(self) -> discord.Embed:
		"""Drop-in embed for replying to whoever asked for the archive."""
		r = self.report()
		embed = discord.Embed(
			title=f"Archive: {self.name}",
			colour=discord.Colour.green(),
		)
		embed.add_field(name="Threads", value=f"{r['threads']:,}", inline=True)
		embed.add_field(name="Messages", value=f"{r['messages']:,}", inline=True)
		embed.add_field(name="Authors", value=f"{r['authors']:,}", inline=True)
		embed.add_field(name="Images", value=f"{r['images']:,} ({r['images_unique']:,} unique)", inline=True)
		embed.add_field(name="Embeds", value=f"{r['embeds']:,}", inline=True)
		embed.add_field(name="Other files", value=f"{r['links']:,}", inline=True)

		embed.add_field(
			name="Size",
			value=(
				f"**{self.human_bytes(r['zip_bytes'])}** "
				f"(from {self.human_bytes(r['raw_bytes'] + r['dedup_saved'] + r['reencode_saved'])})\n"
				f"dedup: −{self.human_bytes(r['dedup_saved'])} · "
				f"re-encode: −{self.human_bytes(r['reencode_saved'])} · "
				f"zip: −{self.human_bytes(r['zip_saved'])}"
			),
			inline=False,
		)

		if r["first_message"] and r["last_message"]:
			embed.add_field(
				name="Covers",
				value=(
					f"<t:{int(r['first_message'].timestamp())}:D> → "
					f"<t:{int(r['last_message'].timestamp())}:D>"
				),
				inline=False,
			)

		embed.set_footer(text=f"Archived in {r['elapsed']:.1f}s")
		return embed

	# ------------------------------------------------------------------
	# Upload (unchanged apart from path handling)
	# ------------------------------------------------------------------

	async def upload(self) -> dict | None:
		base_url = os.getenv('DOWNLOAD_URL_BACKEND')
		url = f"{base_url}/register/{self.channel.guild.id}"

		website_details = {}
		if not self.zip_path or not os.path.exists(self.zip_path):
			return None

		mb = os.stat(self.zip_path).st_size / (1024 * 1024)
		logging.info(f"File is: {mb} MB")
		# if mb < 24:
		# 	logging.info("under 24 MB")
		# 	return None

		password = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
		with open(self.zip_path, 'rb') as f:
			payload = aiohttp.FormData()
			payload.add_field("name", self.name)
			payload.add_field("password", password)
			payload.add_field("max_downloads", "1")
			payload.add_field("reference", str(self.channel.id))
			payload.add_field(
				"file",
				f,
				filename=os.path.basename(self.zip_path),
				content_type="application/zip",
			)

			headers = {"Authorization": f"Bearer {os.getenv('DOWNLOAD_API')}"}

			try:
				async with aiohttp.ClientSession() as session:
					async with session.post(
						url,
						headers=headers,
						data=payload,
						timeout=aiohttp.ClientTimeout(total=300),
					) as response:
						if not response.ok:
							error_text = await response.text()
							logging.error(f"Server group update failed: {response.status}: {error_text}")
							return None

						results = await response.json()
						guid = results.get("guid")
						if not guid:
							logging.error(f"Upload response missing 'guid': {results}")
							return None

						website_details["link"] = (
							f"{os.getenv('DOWNLOAD_URL_FRONTEND')}/download/"
							f"{self.channel.guild.id}/{guid}"
						)
						website_details["password"] = password

			except aiohttp.ClientConnectorError as e:
				logging.info(f"Connection details: {base_url}")
				logging.warning(f"Could not connect to the download API server. Is it running? Error: {e}")
				return None
			except asyncio.TimeoutError:
				logging.warning("The download API request timed out.")
				return None
			except Exception as e:
				logging.error(f"Error uploading download file: {e}", exc_info=True)
				return None

		return website_details