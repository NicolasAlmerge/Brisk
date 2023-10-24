#!/usr/bin/env python3

import webcolors
import time
import re
import asyncio
import aiohttp
import platform
import os
from operator import attrgetter
import discord
from discord.ext import commands
from random import randint
from PIL import Image
from io import BytesIO
from psutil import virtual_memory
from .data import (
    trusteds,
    defaultcolour,
    Files,
    HEX_TO_NAMES,
    CustomEmojis,
    LONG_HEX_COLOR,
    SHORT_HEX_COLOR,
    RGB_TUPLE,
    NAMES_TO_HEX
)
from .errors import (
    SpecialError,
    ConverterNotFoundError,
    BotMissingPermissions
)
from .checks import (
    check_msg
)

__all__ = (
    "set_cooldown",
    "random_colour",
    "urlrequest",
    "get_average_colour",
    "int_converter",
    "set_footer",
    "create_lists",
    "remove_duplicates",
    "time_from_seconds",
    "time_format",
    "datetime_format",
    "number_format",
    "get_reason",
    "get_ram",
    "get_system",
    "mentionrole",
    "return_guild_join_position",
    "clear_downloads",
    "validate_url",
    "key_permissions",
    "general_permissions",
    "membership_permissions",
    "text_permissions",
    "voice_permissions",
    "stage_permissions",
    "return_colour",
    "return_user",
    "ask_userinput",
    "ask_confirmation",
    "get_colour_name",
    "hex_to_rgb",
    "check_reaction"
)


class _CustomCooldown:
    def __init__(self, rate, per, alter_rate, alter_per, bucket):
        self.default_mapping = commands.CooldownMapping.from_cooldown(rate, per, bucket)
        self.altered_mapping = commands.CooldownMapping.from_cooldown(alter_rate, alter_per, bucket)

    def __call__(self, ctx):
        key = self.altered_mapping._bucket_key(ctx.message)
        if key in trusteds:
            return True
        bucket = self.default_mapping.get_bucket(ctx.message)
        # else: bucket = self.altered_mapping.get_bucket(ctx.message)
        retry_after = bucket.update_rate_limit()
        if retry_after:
            raise commands.CommandOnCooldown(bucket, retry_after)
        return True


def set_cooldown(rate=1, per=5.0, alter_rate=1, alter_per=3.0, bucket=commands.BucketType.user):
    """Adds a cooldown to a command."""
    return commands.check(_CustomCooldown(rate, per, alter_rate, alter_per, bucket))


def random_colour():
    """Returns a random number that represents a colour."""
    return randint(0x000000, 0xffffff)


async def urlrequest(url, as_json=False):
    """Requests a url using `aiohttp`, and returns content. This can raise `discord.HTTPException`."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            if r.status != 200:
                raise discord.HTTPException
            if as_json:
                return await r.json()
            return await r.read()


async def get_average_colour(image_url, default=None):
    """Returns the average colour of a picture. If not found, returns the default value."""
    try:
        content = await urlrequest(str(image_url))
        img = Image.open(BytesIO(content))
        colour = img.resize((1, 1), Image.ANTIALIAS).getpixel((0, 0))
        return int("{:02x}{:02x}{:02x}".format(*colour), 16)
    except:
        return defaultcolour if default is None else default


def int_converter(x):
    """Returns the integer converted value of a floating point number or integer if it has the same value than the integer converted value of it, else returns the number itself."""
    return int(x) if x == int(x) else x


def set_footer(ctx, embed, user=None):
    """Sets the embed footer, if context guild exists and `ctx.author`!= `user`."""
    if ctx.guild and (ctx.author != user or not user):
        embed.set_footer(text="Requested by {}".format(str(ctx.author)), icon_url=ctx.author.avatar_url)


def create_lists(n):
    """Creates `n` lists."""
    tmp = []
    for _ in range(n):
        tmp.append([])
    return tuple(tmp)


def remove_duplicates(x):
    """Returns a tuple without all duplicate elements from a list or tuple."""
    return tuple(dict.fromkeys(x))


def time_from_seconds(x):
    """Returns a string formatted version of time from seconds."""
    hours, remainder = divmod(int(x), 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return "{}:{}:{}".format(hours, minutes if minutes >= 10 else "0" + str(minutes), seconds if seconds >= 10 else "0" + str(seconds))
    return "{}:{}".format(minutes, seconds if seconds >= 10 else "0" + str(seconds))


def time_format(seconds):
    """Returns a proper time format based from seconds. Maximum: 86399 seconds."""
    gmt = time.gmtime(seconds)
    hours, minutes, seconds = int(time.strftime("%H", gmt)), int(time.strftime("%M", gmt)), int(time.strftime("%S", gmt))
    return "{}{}{}{}{}{}{}{}{}{}{}{}".format(
        hours if hours else "",
        " hour" if hours == 1 else "",
        " hours" if hours > 1 else "",
        ", " if hours and minutes and seconds else "",
        " and " if (hours and minutes and not seconds) or (
            hours and seconds and not minutes) else "",
        minutes if minutes else "",
        " minute" if minutes == 1 else "",
        " minutes" if minutes > 1 else "",
        " and " if minutes and seconds else "",
        seconds if seconds else "",
        " second" if seconds == 1 else "",
        " seconds" if seconds > 1 else ""
    )


def datetime_format(datetime_obj):
    """Returns a nicely formatted datetime."""
    date = int(datetime_obj.strftime("%d"))
    hour = int(datetime_obj.strftime("%I"))
    if date == 1 or date == 21 or date == 31:
        complement = "st"
    elif date == 2 or date == 22:
        complement = "nd"
    elif date == 3 or date == 23:
        complement = "rd"
    else:
        complement = "th"
    return datetime_obj.strftime("%A, %B {}{} %Y, {}:%M:%S %p".format(date, complement, hour))


def number_format(num):
    """Returns a string number with `,` separator."""
    return f"{num:,}"


def get_reason(ctx, level="mod", capitalise=True):
    """Returns reason text."""
    string = str(ctx.author)
    if level == "mod":
        if capitalise:
            return "Responsible moderator: {}".format(string)
        return "responsible moderator: {}".format(string)
    if level == "admin":
        if capitalise:
            return "Responsible administrator: {}".format(string)
        return "responsible administrator: {}".format(string)
    if capitalise:
        return "Responsible: {}".format(string)
    return "responsible: {}".format(string)


def get_ram():
    """Get the bot's RAM."""
    memory = virtual_memory()
    return "{}/{} GB ({}%)".format(int_converter((memory.used*100//0x40_000_000)/100), int_converter((memory.total*100//0x40_000_000)/100), int_converter(memory.percent))


def get_system():
    """Get system information."""
    system = platform.system()
    if not system:
        return "Unknown"
    if system == "Darwin":
        system = "macOS"
    release = platform.release()
    return system + " " + release if release else system


def mentionrole(role):
    """Returns role mention (`@everyone` for the default role)."""
    return "@everyone" if role.is_default() else role.mention


def return_guild_join_position(user, guild):
    """Returns the guild join position of a user."""
    try:
        joins = tuple(sorted(guild.members, key=attrgetter("joined_at")))
        if None in joins:
            return None
        for key, elem in enumerate(joins):
            if elem == user:
                return key + 1, len(joins)
        return None
    except:
        return None


def clear_downloads():
    """Clear downloaded audios. Exceptions are silently ignored."""
    for osfile in os.listdir(Files.Downloads):
        osfilepath = os.path.join(Files.Downloads, osfile)
        try:
            if os.path.isfile(osfilepath):
                os.remove(osfilepath)
        except:
            continue


url_regex = re.compile(
    r"^(?:http|ftp)s?://"  # http:// or https://
    r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|" # Domain
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # Or IP
    r"(?::\d+)?"  # Optional
    r"(?:/?|[/?]\S+)$", re.IGNORECASE
)


def validate_url(url):
    """Returns `True` if the input is in a correct URL format. `False` otherwise."""
    return bool(url_regex.fullmatch(url))

def key_permissions(member):
    """Generator to yield all key permissions for a member."""
    permissions: discord.Permissions = member.guild_permissions

    # General
    yield "Manage Channels", permissions.manage_channels
    yield "Manage Roles", permissions.manage_roles
    yield "Manage Emojis", permissions.manage_emojis
    yield "Manage Webhooks", permissions.manage_webhooks
    yield "Manage Server", permissions.manage_guild

    # Membership
    yield "Manage Nicknames", permissions.manage_nicknames
    yield "Kick Members", permissions.kick_members
    yield "Ban Members", permissions.ban_members

    # Text
    yield "Manage Messages", permissions.manage_messages

    # Voice
    yield "Mute Members", permissions.mute_members
    yield "Deafen Members", permissions.deafen_members
    yield "Move Members", permissions.move_members


def general_permissions(role):
    """Generator to compute tuples concerning general permissions for a role."""
    permissions: discord.Permissions = role.permissions
    yield "View Channels", permissions.read_messages
    yield "Manage Channels", permissions.manage_channels
    yield "Manage Roles", permissions.manage_roles
    yield "Manage Emojis", permissions.manage_emojis
    yield "View Audit Log", permissions.view_audit_log
    yield "View Server Insights", permissions.view_guild_insights
    yield "Manage Webhooks", permissions.manage_webhooks
    yield "Manage Server", permissions.manage_guild


def membership_permissions(role):
    """Generator to compute tuples concerning membership permissions for a role."""
    permissions: discord.Permissions = role.permissions
    yield "Create Invite", permissions.create_instant_invite
    yield "Change Nickname", permissions.change_nickname
    yield "Manage Nicknames", permissions.manage_nicknames
    yield "Kick Members", permissions.kick_members
    yield "Ban Members", permissions.ban_members


def text_permissions(role):
    """Generator to compute tuples concerning text permissions for a role."""
    permissions: discord.Permissions = role.permissions
    yield "Send Messages", permissions.send_messages
    yield "Embed Links", permissions.embed_links
    yield "Attach Files", permissions.attach_files
    yield "Add Reactions", permissions.add_reactions
    yield "Use External Emoji", permissions.external_emojis
    yield "Mention @everyone, @here and All Roles", permissions.mention_everyone
    yield "Manage Messages", permissions.manage_messages
    yield "Read Message History", permissions.read_message_history
    yield "Send Text-to-Speech Messages", permissions.send_tts_messages
    yield "Use Slash Commands", permissions.use_slash_commands


def voice_permissions(role):
    """Generator to compute tuples concerning voice permissions for a role."""
    permissions: discord.Permissions = role.permissions
    yield "Connect", permissions.connect
    yield "Speak", permissions.speak
    yield "Video", permissions.stream
    yield "Use Voice Activity", permissions.use_voice_activation
    yield "Priority Speaker", permissions.priority_speaker
    yield "Mute Members", permissions.mute_members
    yield "Deafen Members", permissions.deafen_members
    yield "Move Members", permissions.move_members


def stage_permissions(role):
    """Generator to compute tuples concerning stage permissions for a role."""
    yield "Request to Speak", role.permissions.request_to_speak


def return_colour(color):
    """Returns a random colour integer."""
    color = color.lower()

    # Random colour
    if color == "random":
        return random_colour()
    
    rgb_match = RGB_TUPLE.fullmatch(color)

    # 6 digits hex code match
    if LONG_HEX_COLOR.fullmatch(color):
        hexcode = color.lstrip("#")
        return int(hexcode, 16)

    # 3 digits hex code match
    if SHORT_HEX_COLOR.fullmatch(color):
        hexcode = "".join(char*2 for char in color.lstrip("#"))
        return int(hexcode, 16)

    # RGB format match
    if rgb_match:
        try:
            rgb = tuple(int(x) for x in rgb_match.groups()) # Convert strings to numbers
            if not all(0 <= x <= 255 for x in rgb): # Numbers must be betwwen 0 and 255
                raise ValueError
        except: # If RGB tuple was not valid
            raise SpecialError(":point_right: **Error: RGB format must include numbers between 0 and 255.**")
        
        hexcode = "".join("{0:0{1}X}".format(comp, 2) for comp in rgb)
        return int(hexcode, 16)

    # Colour name
    hexcode = NAMES_TO_HEX.get(color.replace(" ", ""), "").lstrip("#") # Get colour hex from name, if possible
    if not hexcode: # If not found, stop here
        raise SpecialError(":point_right: **Error: colour could not be found!**")
    return int(hexcode, 16)


async def return_user(ctx, user):
    """Returns a user."""
    if user is None:
        return ctx.author
    try:
        return await commands.MemberConverter().convert(ctx, user)
    except:
        raise ConverterNotFoundError("Member")


async def ask_userinput(ctx, bot, embed, timeout=30, use_reactions=False, reaction=None, emoji_only=False):
    """Waits for a userinput before continuing the command."""
    
    if use_reactions: embed.set_footer(text="Please click on the green check or red cross below.")
    elif reaction: embed.set_footer(text="Please click on the reaction below or type your answer.")
    elif emoji_only: embed.set_footer(text="Please add a reaction to this message.")
    else: embed.set_footer(text="Please type your answer.")
    
    qu = await ctx.send(embed=embed)
    
    if use_reactions:
        try:
            await qu.add_reaction(CustomEmojis.GreenCheck)
            await qu.add_reaction(CustomEmojis.RedCross)
        except discord.Forbidden:
            raise BotMissingPermissions(on_guild=False, missing_perms=("add_reactions",))
        
        try:
            conf, _ = await bot.wait_for("reaction_add", check=check_reaction(ctx, qu, (CustomEmojis.GreenCheck, CustomEmojis.RedCross)), timeout=timeout)
        except asyncio.TimeoutError:
            try: await qu.delete()
            finally: raise SpecialError("{} **The {} menu has closed due to inactivity!**".format(CustomEmojis.RedCross, ctx.command.name))
        
        try: await qu.delete()
        finally: return str(conf.emoji) == CustomEmojis.GreenCheck
    
    if reaction:
        try: await qu.add_reaction(reaction)
        except discord.Forbidden: raise BotMissingPermissions(on_guild=False, missing_perms=("add_reactions",))

        tasks = [
            asyncio.create_task(bot.wait_for("reaction_add", check=check_reaction(ctx, qu, (reaction,)))),
            asyncio.create_task(bot.wait_for("message", check=check_msg(ctx)))
        ]
        done_tasks, pending_tasks = await asyncio.wait(tasks, timeout=timeout, return_when=asyncio.FIRST_COMPLETED)

        try: await qu.delete()
        except: pass

        for ptask in pending_tasks:
            ptask.cancel()
        
        if not done_tasks:
            raise SpecialError("{} **The {} menu has closed due to inactivity!**".format(CustomEmojis.RedCross, ctx.command.name))

        if tasks[0] in done_tasks:
            return None
        
        msg = await tasks[1]
        ret = msg.content
        try: await msg.delete()
        finally: return ret
    
    if emoji_only:
        try:
            conf, _ = await bot.wait_for("reaction_add", check=check_reaction(ctx, qu), timeout=timeout)
        except asyncio.TimeoutError:
            try: await qu.delete()
            finally: raise SpecialError("{} **The {} menu has closed due to inactivity!**".format(CustomEmojis.RedCross, ctx.command.name))
        
        try: await qu.delete()
        finally: return conf.emoji
    
    try:
        conf = await bot.wait_for("message", timeout=timeout, check=check_msg(ctx))
    except asyncio.TimeoutError:
        try: await qu.delete()
        finally: raise SpecialError("{} **The {} menu has closed due to inactivity!**".format(CustomEmojis.RedCross, ctx.command.name))
    
    ret = conf.content
    try: await conf.delete()
    except: pass
    try: await qu.delete()
    finally: return ret


async def ask_confirmation(ctx, bot, embed, timeout=30):
    """Waits for a confirmation before continuing the command."""
    
    embed.set_footer(text="Please confirm by clicking on the green check below.")
    qu = await ctx.send(embed=embed)
    try:
        await qu.add_reaction(CustomEmojis.GreenCheck)
        await qu.add_reaction(CustomEmojis.RedCross)
    except discord.Forbidden:
        raise BotMissingPermissions(on_guild=False, missing_perms=("add_reactions",))
    
    try:
        conf, _ = await bot.wait_for("reaction_add", check=check_reaction(ctx, qu, (CustomEmojis.GreenCheck, CustomEmojis.RedCross)), timeout=timeout)
    except asyncio.TimeoutError:
        try: await qu.delete()
        finally: raise SpecialError("{} **The {} menu has closed due to inactivity!**".format(CustomEmojis.RedCross, ctx.command.name))
    
    if str(conf.emoji) == CustomEmojis.GreenCheck:
        try: await qu.delete()
        finally: return
    
    try: await qu.delete()
    finally: raise SpecialError(":point_right: **Successfully exit the {} menu!**".format(ctx.command.name))


def _closest_colour(requested_colour):
    """Gets closest colour."""
    min_colours = {}

    for key, name in HEX_TO_NAMES.items():
        r_c, g_c, b_c = webcolors.hex_to_rgb(key)
        rd = (r_c - requested_colour[0]) ** 2
        gd = (g_c - requested_colour[1]) ** 2
        bd = (b_c - requested_colour[2]) ** 2
        min_colours[(rd + gd + bd)] = name

    return min_colours[min(min_colours.keys())]


def get_colour_name(colour):
    """Gets colour name. If not found, returns closest colour."""
    try:
        return webcolors.rgb_to_name(colour, spec=HEX_TO_NAMES)
    except ValueError:
        return _closest_colour(colour)


def hex_to_rgb(hexcode):
    """Hex code to RGB tuple."""
    return tuple(int(hexcode[i:i+2], 16) for i in (0, 2, 4))


def check_reaction(context, message, reactions=None):
    """Checks reaction."""
    def check(reaction, u):
        if reaction.message.id != message.id or u.id != context.author.id:
            return False
        if reactions is None or str(reaction.emoji) in reactions:
            return True
        return False
    return check
