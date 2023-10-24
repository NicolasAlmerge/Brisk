#!/usr/bin/env python3

import discord
from discord.ext import commands
from .data import (
    bot_developers
)
from .errors import (
    MissingPermissions,
    BotMissingPermissions,
    MissingAnyPermission,
    BotDeveloperRestricted,
    NotGuildOwner
)

__all__ = (
    "has_permissions",
    "bot_has_permissions",
    "has_guild_permissions",
    "bot_has_guild_permissions",
    "has_any_permissions",
    "is_bot_dev",
    "dev_only",
    "guild_owner_only",
    "check_msg",
    "check_channel",
    "check_pm",
    "check_pm_with",
    "check_not_pinned"
)


# ------------------- PERMISSION CHECKS -------------------

def has_permissions(**perms):
    """Check to see if the user has all of the channel permissions listed."""

    def predicate(ctx):
        if ctx.author.id in bot_developers:
            return True

        ch = ctx.channel
        permissions = ch.permissions_for(ctx.author)

        missing = [perm for perm, value in perms.items() if getattr(permissions, perm) != value]

        if not missing:
            return True

        raise MissingPermissions(on_guild=False, missing_perms=missing)

    return commands.check(predicate)


def bot_has_permissions(**perms):
    """Check to see if the bot has all of the channel permissions listed."""

    def predicate(ctx):
        guild = ctx.guild
        me = guild.me if guild is not None else ctx.bot.user
        permissions = ctx.channel.permissions_for(me)

        missing = [perm for perm, value in perms.items() if getattr(permissions, perm) != value]

        if not missing:
            return True

        raise BotMissingPermissions(on_guild=False, missing_perms=missing)

    return commands.check(predicate)


def has_guild_permissions(**perms):
    """
    Check to see if the user has all of the guild permissions listed.
    
    Raises `NoPrivateMessage` if no context guild found.
    """

    def predicate(ctx):
        if not ctx.guild:
            raise commands.NoPrivateMessage

        if ctx.author.id in bot_developers:
            return True

        permissions = ctx.author.guild_permissions
        missing = [perm for perm, value in perms.items() if getattr(permissions, perm) != value]

        if not missing:
            return True

        raise MissingPermissions(on_guild=True, missing_perms=missing)

    return commands.check(predicate)


def bot_has_guild_permissions(**perms):
    """
    Check to see if the bot has all of the guild permissions listed.
    
    Raises `NoPrivateMessage` if no context guild found.
    """

    def predicate(ctx):
        if not ctx.guild:
            raise commands.NoPrivateMessage

        permissions = ctx.me.guild_permissions
        missing = [perm for perm, value in perms.items() if getattr(permissions, perm) != value]

        if not missing:
            return True

        raise BotMissingPermissions(on_guild=True, missing_perms=missing)

    return commands.check(predicate)


def has_any_permissions(**perms):
    """Check to see if the user has any of the channel permissions listed."""

    def predicate(ctx):
        if ctx.author.id in bot_developers:
            return True

        ch = ctx.channel
        permissions = ch.permissions_for(ctx.author)

        has_any = any(perm for perm, value in perms.items() if getattr(permissions, perm) == value)

        if has_any:
            return True

        raise MissingAnyPermission(on_guild=False, missing_perms=perms.keys())

    return commands.check(predicate)


def is_bot_dev(ctx):
    """Returns `True` if the context user is a bot developer, else raises `BotDeveloperRestricted`."""
    if ctx.author.id in bot_developers:
        return True
    raise BotDeveloperRestricted


def dev_only():
    """Checks to see if the context user is a bot developer, else raises `BotDeveloperRestricted`."""
    return commands.check(lambda ctx: is_bot_dev(ctx))


def guild_owner_only():
    """Returns `True` if the context member is the server owner, else raises `NotGuildOwner` or `commands.NoPrivateMessage` if there is no context guild."""

    def predicate(ctx):
        if ctx.guild is None:
            raise commands.NoPrivateMessage

        if ctx.author.id in bot_developers:
            return True

        owner = ctx.guild.owner
        if owner is None:
            raise NotGuildOwner

        if ctx.author.id == owner.id:
            return True

        raise NotGuildOwner

    return commands.check(predicate)


# ------------------- MESSAGE CHECKS -------------------

def check_msg(context):
    """Checks the message author and channel."""
    def check(message):
        return context.author == message.author and context.channel == message.channel
    return check


def check_channel(context):
    """Checks the message channel."""
    def check(message):
        return message.channel == context.channel and not message.author.bot
    return check


def check_pm(context):
    """Checks if message in the author's PM channel."""
    def check(message):
        return isinstance(message.channel, discord.DMChannel) and message.author == context.author
    return check


def check_pm_with(user):
    """Checks if message in the author's PM channel."""
    def check(message):
        return isinstance(message.channel, discord.DMChannel) and message.author == user
    return check


def check_not_pinned(message):
    """Checks if the message is not pinned."""
    return not message.pinned