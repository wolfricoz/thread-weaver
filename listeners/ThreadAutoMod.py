import asyncio
import logging

import discord
from discord.ext.commands import Cog, Bot
from discord_py_utilities.messages import send_message

from classes.discordcontrollers.forum.AutoMod import AutoMod
from classes.kernel.ConfigData import ConfigData
from classes.kernel.Queue import Queue
from database.transactions.ForumTransactions import ForumTransactions
from resources.configs.ConfigMapping import ConfigMapping

logger = logging.getLogger(__name__)


class ThreadAutoMod(Cog) :

  def __init__(self, bot: Bot) :
   self.bot = bot

  @Cog.listener('on_thread_create')
  async def on_thread_create(self, thread: discord.Thread) :
   """
   Triggered when a thread is created.

   This only handles the ping. The starter message is NOT fetched here:
   THREAD_CREATE and MESSAGE_CREATE are separate gateway events with no
   ordering guarantee, so the starter message often does not exist yet
   from the API's point of view (404 / error code 10008). AutoMod runs
   from on_message instead, where the message is handed to us directly.
   """
   if thread.type != discord.ChannelType.public_thread :
    return
   if not ConfigData().get_toggle(thread.guild.id, ConfigMapping.PING_ON_THREAD, "ENABLED", "DISABLED") :
    return

   channel = await ConfigData().get_channel(thread.guild, ConfigMapping.PING_ON_THREAD_CHANNEL)
   if channel is None :
    return

   ping = ConfigData().get_key(thread.guild.id, ConfigMapping.PING_ON_THREAD_ROLE, 0)
   owner = thread.owner.mention if thread.owner else f"<@{thread.owner_id}>"
   parent = thread.parent.mention if thread.parent else "an unknown channel"

   payload = f"`{thread.name}` created by {owner} in {parent}"
   if ping != 0 :
    payload = f"<@{ping}>\n{payload}"

   await send_message(channel, payload)


  @Cog.listener('on_message')
  async def on_message(self, message: discord.Message) :
   """
   Triggered when a message is created.

   For a forum post, the starter message has the same ID as the thread,
   so that is how we detect it. This replaces the old fetch_message()
   race in on_thread_create.
   """
   is_thread_starter = (
    isinstance(message.channel, discord.Thread)
    and message.id == message.channel.id
   )

   if not is_thread_starter :
    await AutoMod().run(message)
    return

   thread = message.channel
   if not isinstance(thread.parent, discord.ForumChannel) :
    return

   result = await AutoMod().run(message)
   if not result :
    return
   Queue().add(self.send_reminder(thread.parent, thread))


  @Cog.listener('on_message_edit')
  async def on_message_edit(self, before, after) :
   """This event is triggered when a message is updated."""
   await AutoMod().run(after)


  async def fetch_message(self, thread: discord.Thread) -> discord.Message | bool | None :
   """
   Fetches the message that created the thread, with backoff.

   No longer used by the listeners above, but kept for callers that only
   have a Thread. Returns False for unsupported thread types, None if the
   message could not be fetched.
   """
   if thread.type != discord.ChannelType.public_thread :
    return False
   if thread.starter_message is not None :
    return thread.starter_message

   delay = 1.0
   for attempt in range(5) :
    try :
     return await thread.fetch_message(thread.id)
    except discord.NotFound :
     if attempt == 4 :
      logger.warning(
       "Starter message for thread %s (%s) could not be fetched: not found.",
       thread.id, thread.name,
      )
      return None
     await asyncio.sleep(delay)
     delay *= 2
    except discord.Forbidden :
     logger.warning("Missing permissions to read thread %s (%s).", thread.id, thread.name)
     return False
    except discord.HTTPException as error :
     logger.warning("HTTP error fetching starter message for thread %s: %s", thread.id, error)
     return None
   return None


  # == Additional features ==

  async def send_reminder(self, forum: discord.ForumChannel | None, thread: discord.Thread) :
   """
   Sends the configured reminder to the specified thread.
   """
   if forum is None :
    return None
   cfg = ForumTransactions().get(forum.id)
   if not cfg or not cfg.reminder or len(cfg.reminder) < 1 :
    return None
   embed = discord.Embed(
    title="The staff would like to remind you about",
    description=cfg.reminder,
   )
   return await send_message(thread, " ", embed=embed)


async def setup(bot: Bot) :
  await bot.add_cog(
   ThreadAutoMod(bot),
  )