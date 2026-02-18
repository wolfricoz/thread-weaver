import logging
import os.path
import re
import shutil

import discord


class ThreadArchive():
	def __init__(self, name: str, channel: discord.Thread | discord.ForumChannel) :
		self.threads = None
		self.name = self.sanitize_filename(name)
		self.channel = channel
		self.archives = [] # Incase multiple threads are being archived, we can make one file for all of them.
		self.zip_path = None

		os.path.exists('archives') or os.makedirs('archives')

	def sanitize_filename(self, filename: str) :
		# Replace any character that isn't a letter, number, space, hyphen, or underscore
		# This removes ?, :, *, etc.
		return re.sub(r'[\\/*?:"<>|]', "", filename).strip()

	async def run(self):
		"""This is the main function that will call the other functions to validate and create the archive"""
		# Setup Variables

		# Check if its a thread of a forum.
		await self.get_threads()

		for thread in self.threads:
			archive_dir, file_path = await self.create_dir(thread)
			html = await self.thread_to_html(thread, archive_dir)
			await self.create_file(thread, html, file_path)
			await self.create_zip()




	async def get_threads(self) -> None:
		"""Checks if the channel is a thread or a forum, and fills the threads variable accordingly."""
		self.threads = [self.channel]
		if self.channel.type == discord.ChannelType.forum:
			logging.info(f"Getting threads for {self.channel.name}")
			self.threads = self.channel.threads + [thread async for thread in self.channel.archived_threads(limit=None)]


	async def create_dir(self, thread:discord.Thread) -> tuple[str, str] :
		"""Creates a directory for the thread and returns the path."""
		name = self.sanitize_filename(thread.name.replace(" ", "_"))
		path = f"archives/{thread.id}"
		image_path = f"{path}/images"
		os.path.exists(path) or os.makedirs(path)
		os.path.exists(image_path) or os.makedirs(image_path)

		filename = f"{name}.html"
		file_path = f"{path}/{filename}"

		return path, file_path


	async def thread_to_html(self, thread, archive_path: str) -> str:
		"""This will convert a thread to a html file. Returns HTML as a string."""
		with open('resources/css/export.css', 'r') as f:
			css = f.read()

		html = f"<html><head><title>{thread.name}</title></head><body><h1>{thread.name}</h1><p>Created at: {thread.created_at.strftime("%m/%d/%Y %H:%M")}</p><p>Author: {thread.owner}</p><hr><style>{css}</style></head><body>"
		async for message in thread.history(limit=None, oldest_first=True) :
			# For each message, we will create a div with the message content and attachments.
			html += f"<div class='message'><p><strong>{message.author}</strong> at {message.created_at.strftime("%m/%d/%Y %H:%M")}:</p><p>{message.content}</p>"
			if not message.attachments :
				continue
			html += '<div class="attachment-container">'
			for attachment in message.attachments :
				if attachment.content_type and attachment.content_type.startswith("image/") :
					# If the attachment is an image, we will download it and add it to the html.
					image_path = f"images/{attachment.filename}"
					await attachment.save(f"{archive_path}/{image_path}")
					html += f"<a href='{image_path}' title='Click to view full image' target='_blank'><img src='{image_path}' alt='{attachment.filename}' class='attachment'></a>"
				else :
					# If the attachment is not an image, we will just add a link to it.
					html += f"<p><a href='{attachment.url}' target='_blank'>{attachment.filename}</a></p>"
			html += '</div></div><hr>'

		# close the html tags
		html += f"</body></html>"
		return html.replace(">", ">\n")

	async def create_file(self, thread, html, file_path: str) :
		"""This will create a .html command for the thread and save it to the archives folder."""

		with open(file_path, 'w', encoding='utf-8') as f:
			f.write(html)
		self.archives.append(thread.id)

	async def create_zip(self):
		"""This will create the zip file, including image files."""
		import zipfile
		zip_path = f"archives/{self.name}.zip"
		with zipfile.ZipFile(zip_path, 'w') as zip_file:
			for directory in os.listdir("archives"):
				if directory.isnumeric() and (int(directory) in self.archives):
					dir_path = f"archives/{directory}"
					for foldername, subfolders, filenames in os.walk(dir_path):
						for filename in filenames:
							file_path = os.path.join(foldername, filename)
							zip_file.write(file_path, os.path.relpath(file_path, "archives"))

		self.zip_path = zip_path

	async def clean_up(self):
		"""This will remove the temporary files created during the archive process."""
		for directory in os.listdir("archives"):
			if directory.isnumeric() and (int(directory) in self.archives):
				dir_path = f"archives/{directory}"
				shutil.rmtree(dir_path)
		os.remove(self.zip_path)




