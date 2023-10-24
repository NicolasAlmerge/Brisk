#!/usr/bin/env python3


from discord.ext import commands

# ------------------- LOOP -------------------
# async def purge_chat(channel, guild, timer, include_pins=False):
#     """Loop to purge chat."""
#     if include_pins:
#         while True:
#             try:
#                 messages = await channel.purge(limit=1000)
#                 if not messages:
#                     break
#             except discord.Forbidden:
#                 if not guild.me.permissions_in(channel).manage_messages:
#                     if not guild.me.permissions_in(channel).read_message_history:
#                         await channel.send(":no_good: **I do not have permission to manage messages and read message history on this channel!**")
#                         return
#                     await channel.send(":no_good: **I do not have permission to manage messages on this channel!**")
#                     return
#                 await channel.send(":no_good: **I do not have permission to view message history on this channel!**")
#                 return
#             except:
#                 await channel.send(":thumbsdown: **Clearing message failed!** Please try again later!")
#                 break

#     else:
#         def check(message):
#             """Checks if the message is not pinned."""
#             return not message.pinned

#         while True:
#             try:
#                 messages = await channel.purge(limit=1000, check=check)
#                 if not messages:
#                     break
#             except discord.Forbidden:
#                 if not guild.me.permissions_in(channel).manage_messages:
#                     if not guild.me.permissions_in(channel).read_message_history:
#                         await channel.send(":no_good: **I do not have permission to manage messages and read message history on this channel!**")
#                         return
#                     await channel.send(":no_good: **I do not have permission to manage messages on this channel!**")
#                     return
#                 await channel.send(":no_good: **I do not have permission to view message history on this channel!**")
#                 return
#             except:
#                 await channel.send(":thumbsdown: **Clearing message failed!** Please try again later!")
#                 break

#     await asyncio.sleep(timer)

# @bot.command()
# @bot.dev_only()
# async def reload(ctx, *, cogs):
#     if not cogs:
#         await ctx.send(":point_right: **No cogs specified!**")
#         return
#     cogs = cogs.split(",")
#     for cog in cogs:
#         cog = cog.strip()
#         if cog in ("dev", "devs", "developer"):
#             cog = "developers"
#         elif cog in ("mods", "moderator", "moderators"):
#             cog = "mod"
#         elif cog in ("admins", "administrator", "administrators"):
#             cog = "admin"
#         try:
#             bot.reload_extension(f"cogs.{cog}")
#         except:
#             await ctx.send(f":point_right: **{cog} could not be reloaded!**")
#             return
#     if len(cogs) is 1:
#         await ctx.send("{} Successfully reloaded cog **{}**!".format(bot.CustomEmojis.GreenCheck, *cogs))
#         return
#     await ctx.send("{} Successfully reloaded cogs **{}**!".format(bot.CustomEmojis.GreenCheck, ", ".join(cog for cog in cogs)))

def setup(bot):
    """Adds the NSFW cog to the bot."""

    class NSFW(commands.Cog):
        """The NSFW cog."""

    bot.add_cog(NSFW())