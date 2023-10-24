#!/usr/bin/env python3

from discord.ext import commands


__all__ = (
    "MissingPermissions",
    "BotMissingPermissions",
    "MissingAnyPermission",
    "PremiumRestricted",
    "BotDeveloperRestricted",
    "NotGuildOwner",
    "ConverterNotFoundError",
    "SilentError",
    "UserForbidden",
    "ServerForbidden",
    "BotDisabledError",
    "SpecialError"
)


def _permission_format(perm, on_channel=False):
    """Format a permission to make it more readable."""
    permission = perm.replace("_", " ").replace("guild", "server").replace("use voice activation", "use voice activity").title().replace("Tts", "TTS")
    return permission.replace("Roles", "Permissions") if on_channel else permission


class MissingPermissions(commands.CheckFailure):
    """
    Exception raised when the context member hasn't got all of the permissions specified.

    Attributes
    -----------
    on_guild: :class:`bool`
        If lookup was done using guild permissions (else using channel permissions).
    missing_perms: :class:`list`
        The required permissions that are missing.
    """

    def __init__(self, on_guild, missing_perms, *args):
        self.on_guild = on_guild
        self.missing_perms = missing_perms

        if self.on_guild:

            missing = [_permission_format(perm) for perm in self.missing_perms]
            if len(missing) == 1:
                message = "**You do not have permission to run this command!**\n:key: __**Required permission**__: `{}`".format(*missing)
                self.message = message
                return

            fmt = "{}`** and **`{}".format("`**, **`".join(missing[:-1]), missing[-1])
            message = "**You do not have permission to run this command!**\n:key: __**Required permissions**__: `{}`".format(fmt)
            self.message = message
            return

        missing = [_permission_format(perm, on_channel=True) for perm in self.missing_perms]
        if len(missing) == 1:
            message = "**You do not have permission to run this command!**\n:key: __**Required channel permission**__: `{}`".format(*missing)
            self.message = message
            return

        fmt = "{}`** and **`{}".format("`**, **`".join(missing[:-1]), missing[-1])
        message = "**You do not have permission to run this command!**\n:key: __**Required channel permissions**__: `{}`".format(fmt)
        self.message = message


class BotMissingPermissions(commands.CheckFailure):
    """
    Exception raised when the bot hasn't got all of the permissions specified.

    Attributes
    -----------
    on_guild: :class:`bool`
        If lookup was done using guild permissions (else using channel permissions).
    missing_perms: :class:`list`
        The required permissions that are missing.
    """

    def __init__(self, on_guild, missing_perms, *args):
        self.on_guild = on_guild
        self.missing_perms = missing_perms

        if self.on_guild:

            missing = [_permission_format(perm) for perm in self.missing_perms]
            if len(missing) == 1:
                message = "**I cannot execute this command as I do not have the **`{}`** permission!**".format(*missing)
                self.message = message
                return

            fmt = "{}`** and **`{}".format("`**, **`".join(missing[:-1]), missing[-1])
            message = "**I cannot execute this command as I do not have the **`{}`** permissions!**".format(fmt)
            self.message = message
            return

        missing = [_permission_format(perm, on_channel=True) for perm in self.missing_perms]
        if len(missing) == 1:
            message = "**I cannot execute this command as I do not have the **`{}`** permission on this channel!**".format(*missing)
            self.message = message
            return

        fmt = "{}`** and **`{}".format("`**, **`".join(missing[:-1]), missing[-1])
        message = "**I cannot execute this command as I do not have the **`{}`** permissions on this channel!**".format(fmt)
        self.message = message


class MissingAnyPermission(commands.CommandError):
    """
    Exception raised when the context member hasn't got any of the permissions specified.

    Attributes
    -----------
    on_guild: :class:`bool`
        If lookup was done using guild permissions (else using channel permissions).
    missing_perms: :class:`list`
        The required permissions that are missing.
    """

    def __init__(self, on_guild, missing_perms, *args):
        self.on_guild = on_guild
        self.missing_perms = missing_perms

        missing = [perm.replace('_', ' ').replace('guild', 'server').title() for perm in missing_perms]

        if len(missing) > 2:
            fmt = '{}, and {}'.format(", ".join(missing[:-1]), missing[-1])
        else:
            fmt = ' and '.join(missing)
        message = 'You are missing all of these permission(s) to run this command: {}'.format(fmt)
        super().__init__(message, *args)


class PremiumRestricted(commands.CommandError):
    """Exception raised when a non premium and non bot Developer is trying to execute premium commands."""


class BotDeveloperRestricted(commands.CommandError):
    """Exception raised when an operation requires the context user to be a bot Developer but is not the case."""


class NotGuildOwner(commands.CommandError):
    """Exception raised when an operation requires the context member to be the guild owner, but it is not the case."""


class ConverterNotFoundError(commands.CommandError):
    """Exception raised when a converter fails."""

    def __init__(self, converter, more_info=False):
        self.converter = converter
        self.more_info = more_info


class SilentError(commands.CommandError):
    """Exception to stop the execution of a command silently, to avoid trigerring `on_command_completion` event."""


class UserForbidden(commands.CheckFailure):
    """Exception raised when a blacklisted user is attempting to execute commands."""


class ServerForbidden(commands.CheckFailure):
    """Exception raised when a user is attempting to execute commands in a blacklisted guild."""


class BotDisabledError(commands.CheckFailure):
    """Exception raised when the bot has been temporarily disabled."""


class SpecialError(commands.CommandError):
    """Special Exception."""
    def __init__(self, msg: str):
        self.msg = msg
