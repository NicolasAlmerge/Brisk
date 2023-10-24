#!/usr/bin/env python3

import discord
from discord.ext import commands
import asyncio
from datetime import datetime
import string
import logging
from math import ceil
from random import choice
import json
import asyncpg
from discord_slash.client import SlashCommand
from cogs import utils
from discord_components import DiscordComponents


# ------------------- BOT INITIALIZER -------------------
commandprefix = "="


with open("./resources/token.txt") as f:
    TOKEN = f.read()

with open("./resources/dbtoken.txt") as f:
    DB_TOKEN = f.read()


async def get_prefix(bot, message):
    """Returns the prefix of a corresponding guild."""
    if message.guild is None:
        return commands.when_mentioned_or(commandprefix)(bot, message)
    prefix = await bot.fetchval("SELECT prefix FROM prefixes WHERE server_id = $1", message.guild.id)
    if prefix is None:
        return commands.when_mentioned_or(commandprefix)(bot, message)
    return commands.when_mentioned_or(prefix)(bot, message)


class Bot(commands.Bot):
    """Represents the Discord Bot."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, command_prefix=get_prefix, case_insensitive=True, owner_id=utils.bot_owner, status=discord.Status.offline, intents=discord.Intents.all(), **kwargs)

        self.commandprefix = commandprefix
        self.defaultstatus = "online"
        self.developers = utils.bot_developers
        self.trusteds = utils.trusteds
        self.id = 470267858119819274
        self.disabled = False
        self.command_error = ":robot: **This command is unknown!**"

        self.dev_guild = utils.dev_guild_id
        self.suggestions = 540145721152634900
        self.reports = 540253772681707533
        self.errors = 631055995128250368
        self.connections_channel = 540257299931987979
        self.support_guild = utils.support_guild_id
        self.conn_pool = None
        self.activity = discord.Activity(name="@Brisk help", type=discord.ActivityType.watching)

        self.logfile = "./resources/discord.log"
        self.logger = logging.getLogger("discord")
        self.logger.setLevel(logging.INFO)
        self.handler = logging.FileHandler(filename=self.logfile, encoding="utf-8", mode="w")
        self.handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
        self.logger.addHandler(self.handler)

        self.cooldownerror = ":stopwatch: **This command is on cooldown!** Please try again in **{}**."
        self.command_cogs = "misc", "fun", "developers", "mod", "admin" # Music cog in development
        self.confirmlist = "yes", "y", "ye", "yeah", "please", "confirm"
        self.cancellist = "no", "n", "nope", "stop", "exit", "cancel"
        self.stoplist = "exit", "stop", "gamestop", "stopgame"
        self.dbuserinfos = ("ID", "Money", "Level", "XP", "Commands", "Detective", "Codebreaker", "RPS", "Coinflipping", "Mentalist", "Mathdestroy", "Cats", "Dogs")
        self.defaultline = tuple([0]*(len(self.dbuserinfos)-1))
    

    async def create_db_pool(self, password: str):
        """Creates a connection pool to the database."""
        self.conn_pool = await asyncpg.create_pool(user="brisk_app", password=password, database="brisk")
    

    async def get_global_gdp(self):
        """Returns the global GDP."""
        return await self.fetchval("SELECT SUM(money) FROM users")


    async def trigger_achievement(self, ctx: commands.Context, name: str, destination: discord.TextChannel = None):
        """Function to trigger the achievement message. If destination is `None`, message is sent to `ctx`."""
        if not destination:
            destination = ctx
        with open(utils.Files.Achievements) as a:
            dictionary = json.load(a)[name]
        reward = dictionary["reward"]
        await self.addmoney(ctx.author, reward)
        embed = discord.Embed(title=":trophy: **Achievement unlocked**", colour=0x42b581)
        embed.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url)
        embed.add_field(name=f"{utils.CustomEmojis.GreenCheck} {name} (+ {utils.CustomEmojis.Smilo}{utils.number_format(reward)})", value="*{}*".format(dictionary["revealed"]))
        await destination.send(embed=embed)


    def achievement(self, name, dictionary, unlocked=True, progress=None):
        """Function to return the achievement."""
        if unlocked:
            return ("{} {} - {}{}".format(utils.CustomEmojis.GreenCheck, name, utils.CustomEmojis.Smilo, utils.number_format(dictionary["reward"])), "*{}*".format(dictionary["revealed"]))
        _hidden = dictionary["hidden"]
        hidden = choice(_hidden) if isinstance(_hidden, list) else _hidden
        if progress:
            return ("{} {} - {}{}".format(utils.CustomEmojis.RedCross, name, utils.CustomEmojis.Smilo, utils.number_format(dictionary["reward"])), hidden + f" ({utils.number_format(progress[0])}/{utils.number_format(progress[1])})")
        return ("{} {} - {}{}".format(utils.CustomEmojis.RedCross, name, utils.CustomEmojis.Smilo, utils.number_format(dictionary["reward"])), hidden)


    def get_uptime(self):
        """Returns bot uptime."""
        now = datetime.utcnow()
        delta = int((now - self.start_time).total_seconds())
        if not delta:
            return None
        hours, remainder = divmod(delta, 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)

        if not days:
            daytext = ""
        elif days == 1:
            daytext = "1 day"
        else:
            daytext = f"{days} days"
        if not hours:
            hourtext = ""
        elif hours == 1:
            hourtext = "1 hour"
        else:
            hourtext = f"{hours} hours"
        if not minutes:
            mintext = ""
        elif minutes == 1:
            mintext = "1 minute"
        else:
            mintext = f"{minutes} minutes"
        if not seconds:
            sectext = ""
        elif seconds == 1:
            sectext = "1 second"
        else:
            sectext = f"{seconds} seconds"

        return "{}{}{}{}{}{}{}{}{}".format(
            daytext,
            ", " if days and ((hours and minutes) or (
                hours and seconds) or (minutes and seconds)) else "",
            " and " if days and ((hours and not minutes and not seconds) or (
                minutes and not hours and not seconds) or (seconds and not hours and not minutes)) else "",
            hourtext,
            ", " if hours and minutes and seconds else "",
            " and " if hours and ((minutes and not seconds) or (
                seconds and not minutes)) else "",
            mintext,
            " and " if minutes and seconds else "",
            sectext
        )
    

    async def execute(self, query: str, *args):
        async with self.conn_pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(query, *args)


    async def fetchrow(self, query: str, *args):
        async with self.conn_pool.acquire() as conn:
            async with conn.transaction():
                values = await conn.fetchrow(query, *args)
        return values


    async def fetchval(self, query: str, *args):
        async with self.conn_pool.acquire() as conn:
            async with conn.transaction():
                value = await conn.fetchval(query, *args)
        return value
    
    async def fetch(self, query: str, *args):
        async with self.conn_pool.acquire() as conn:
            async with conn.transaction():
                values = await conn.fetch(query, *args)
        return values
    

    async def addline(
        self, user_id, money=0, level=0, xp=0, commands=0, detective=False,
        codebreaker=False, rps=0, coinflipping=0, mentalist=False, mathdestroy=False,
        cats=0, dogs=0, roll=False):
        """Adds a new line in the database."""
        detective = str(detective).lower()
        codebreaker = str(codebreaker).lower()
        mentalist = str(mentalist).lower()
        mathdestroy = str(mathdestroy).lower()
        roll = str(roll).lower()
        await self.execute(f"""
            INSERT INTO users(id, money, level, xp, commands, detective, codebreaker, rps, coinflipping, mentalist, mathdestroy, cats, dogs, roll)
            VALUES($1,$2,$3,$4,$5,{detective},{codebreaker},$6,$7,{mentalist},{mathdestroy},$8,$9,{roll})
            """, user_id, money, level, xp, commands, rps, coinflipping, cats, dogs
        )


    def is_default_line(self, line):
        """Checks empty line in database."""
        return line == self.defaultline


    async def addmoney(self, user, amount):
        """Adds `amount` of money to a user."""
        result = await self.fetchval("SELECT money FROM users WHERE id = $1", user.id)
        if result is None:
            await self.addline(user.id, money=amount)
            return
        await self.execute("UPDATE users SET money = $1 WHERE id = $2", result+amount, user.id)


    async def removemoney(self, user, amount):
        """Removes `amount` of money to a user. Raises `ValueError` if the user doesn't have enough."""
        result = await self.fetchval("SELECT money FROM users WHERE id = $1", user.id)
        if not result or result < amount:
            raise ValueError
        await self.execute("UPDATE users SET money = $1 WHERE id = $2", result-amount, user.id)
        return result


    async def resetmoney(self, user):
        """Resets someone's balance."""
        result = await self.execute("SELECT money FROM users WHERE id = $1", user.id)
        if not result:
            return
        await self.execute("UPDATE users SET money = 0 WHERE id = $1", user.id)
    

    async def close_connection(self):
        """Close the connection to Discord and database."""
        try: await self.conn_pool.close()
        except: pass
        try: await self.close()
        except: exit()


    def premium_guilds_only(self):
        """Returns `True` if the context guild is a premium guild or the context user is a bot Developer, else raises `PremiumRestricted` or `commands.NoPrivateMessage` if there is no context guild."""

        async def predicate(ctx):
            if ctx.guild is None:
                raise commands.NoPrivateMessage

            if ctx.author.id in utils.bot_developers:
                return True

            if ctx.guild.id in (self.dev_guild, self.support_guild):
                return True

            data = await self.fetchrow("SELECT * FROM premiumservers WHERE server_id = $1", ctx.guild.id)
            if data is None:
                raise utils.PremiumRestricted

            return True

        return commands.check(predicate)


bot = Bot()
slash = SlashCommand(bot, sync_commands=True)
DiscordComponents(bot)


# ------------------- GLOBAL CHECK -------------------
@bot.check
async def verify_user_and_server(ctx):
    """Returns `True` if the context user and guild, if any, are authorized to use commands. Raises `UserForbidden` or `ServerForbidden` if not the case."""
    if ctx.author.bot:
        raise utils.SilentError
    if ctx.author.id in bot.developers:
        return True
    if bot.disabled:
        raise utils.BotDisabledError

    res = await bot.fetchrow("SELECT * FROM blacklistedusers WHERE user_id = $1", ctx.author.id)
    if res is not None:
        raise utils.UserForbidden

    if ctx.guild:
        res2 = await bot.fetchrow("SELECT * FROM blacklistedservers WHERE server_id = $1", ctx.guild.id)
        if res2 is not None:
            raise utils.ServerForbidden
    
    return True


def is_level_up(curr_xp):
    """Returns `True` if level should increment. `False` otherwise."""
    return curr_xp >= round((4*(curr_xp**3))/5)


# ------------------- EVENTS -------------------
@bot.event
async def on_ready():
    """Event triggered when the bot is ready and connected to Discord."""
    await bot.change_presence(activity=bot.activity, status=bot.defaultstatus, afk=False)
    print("The bot is ready!")
    # rstg_channel = bot.get_channel(bot.connections_channel)
    # if rstg_channel:
    #     await rstg_channel.send("@everyone :small_blue_diamond: **Connected**\n*Hi, there! I'm ready to execute commands!*:wave:")

@bot.event
async def on_command_completion(ctx):
    """Event triggered when a command has been successfully completed."""
    count = await bot.fetchval("SELECT commands FROM users WHERE id = $1", ctx.author.id)
    if count is None:
        await bot.addline(ctx.author.id, commands=1)
        return
    
    count += 1
    await bot.execute("UPDATE users SET commands = $1 WHERE id = $2", count, ctx.author.id)

    if count == 50:
        await bot.trigger_achievement(ctx, "First Step")
        return
    if count == 250:
        await bot.trigger_achievement(ctx, "Shy Guy")
        return
    if count == 1000:
        await bot.trigger_achievement(ctx, "Geek")
        return
    if count == 5000:
        await bot.trigger_achievement(ctx, "Addicted")
        return
    if count == 10000:
        await bot.trigger_achievement(ctx, "Robot")
        return
    if count == 20000:
        await bot.trigger_achievement(ctx, "Legend")


@bot.event
async def on_command_error(ctx, error):
    """Event triggered when a command error was raised."""
    if isinstance(error, utils.SilentError):
        return
    
    if isinstance(error, utils.SpecialError):
        await ctx.send(error.msg)
        return

    if isinstance(error, commands.CommandNotFound):
        await ctx.send(bot.command_error)
        return

    if isinstance(error, utils.UserForbidden):
        await ctx.send(":flag_black: **You have been blacklisted, meaning you cannot use any of my commands in any server!**")
        return

    if isinstance(error, utils.ServerForbidden):
        await ctx.send(":flag_black: **This server has been blacklisted, meaning every command has been disabled on this server!**")
        return

    if isinstance(error, utils.BotDisabledError):
        await ctx.send(":warning: **The bot is currently facing problems and has been temporarily disabled!**")
        return

    if isinstance(error, commands.NotOwner):
        await ctx.send(":no_entry_sign: **You do not have permission to run this command!**\n:lock: **Only the **`Bot Owner`** can run it!**")
        return

    if isinstance(error, utils.BotDeveloperRestricted):
        await ctx.send(":no_entry_sign: **You do not have permission to run this command!**\n:lock: **Only the **`Bot Developers`** can run it!**")
        return

    if isinstance(error, utils.PremiumRestricted):
        await ctx.send(":star: **This command is Premium-Only!**")
        return

    if isinstance(error, commands.NoPrivateMessage):
        await ctx.send(":point_right: **This command can only be used in servers!**")
        return

    if isinstance(error, utils.MissingPermissions):
        await ctx.send(":no_entry_sign: " + error.message)
        return

    if isinstance(error, utils.MissingAnyPermission):
        if error.on_guild:
            missing_perms = tuple(string.capwords(str(missing_perm).replace("_", " ").replace("guild", "server").replace("use voice activation", "use voice activity")).replace("Tts", "TTS") for missing_perm in error.missing_perms)
            await ctx.send(":no_entry_sign: **You do not have permission to run this command!**\n:key: __**Required permission**__: `{}`".format("`**, **`".join(missing_perms)[::-1].replace(" ,", " ro ", 1)[::-1]))
            return
        missing_perms = tuple(string.capwords(str(missing_perm).replace("_", " ").replace("guild", "server").replace("roles", "permissions").replace("use voice activation", "use voice activity")).replace("Tts", "TTS") for missing_perm in error.missing_perms)
        await ctx.send(":no_entry_sign: **You do not have permission to run this command!**\n:key: __**Required channel permission**__: `{}`".format("`**, **`".join(missing_perms)[::-1].replace(" ,", " ro ", 1)[::-1]))
        return

    if isinstance(error, utils.BotMissingPermissions):
        await ctx.send(":no_good: " + error.message)
        return

    if isinstance(error, commands.CommandOnCooldown):
        timeremaining = ceil(error.retry_after)
        if timeremaining <= 1:
            await ctx.send(bot.cooldownerror.format("1 second"))
            return
        if timeremaining == 86400:
            await ctx.send(bot.cooldownerror.format("24 hours"))
            return
        await ctx.send(bot.cooldownerror.format(utils.time_format(timeremaining)))
        return

    if isinstance(error, utils.NotGuildOwner):
        await ctx.send(":no_entry_sign: **You do not have permission to run this command!**\n:lock: **Only the **`Server Owner`** can run it!**")
        return

    if isinstance(error, utils.ConverterNotFoundError):
        if error.more_info:
            await ctx.send(":point_right: {} could not be found!".format(error.converter))
            return
        await ctx.send(":point_right: **{} could not be found!**".format(error.converter))
        return

    await on_error(ctx, error)


@bot.event
async def on_error(ctx, error):
    try:
        if ctx.guild:
            errorcode = hex(ctx.author.id)[2:] + ":" + hex(ctx.channel.id)[2:] + ":" + ctx.message.created_at.strftime("%d%m%Y%H%M%S")
        else:
            errorcode = hex(ctx.author.id)[2:] + ":" + ctx.message.created_at.strftime("%d%m%Y%H%M%S")
        
        error_ch = bot.get_channel(bot.errors)
        if error_ch:
            #await error_ch.send(f"{utils.CustomEmojis.RedCross} **An unexpected error occured when trying to run function **`{ctx.command.name}` (error code: `{errorcode}`).```fix\n{error}```")
            await ctx.send(f"{utils.CustomEmojis.RedCross} **An unexpected error occured!**\nPlease contact a bot developer about this issue, with error code: `{errorcode}`.")
            print(error)
        else:
            await ctx.send(f"{utils.CustomEmojis.RedCross} **An unexpected error occured!**\nPlease try again later.")
    except:
        return


@bot.event
async def on_message_delete(message):
    """Event triggered on a message deletion."""
    if message.guild is None:
        return
    result = await bot.fetchval("SELECT channel_id FROM logs WHERE server_id = $1", message.guild.id)
    if result is None:
        await bot.execute("DELETE FROM logs WHERE server_id = $1", message.guild.id)
        return
    
    channel = await bot.fetch_channel(result)
    if channel is None:
        await bot.execute("DELETE FROM logs WHERE server_id = $1", message.guild.id)
        return
    try:
        embed = discord.Embed(color=bot.embedcolours["MessageDeletion"], timestamp=datetime.utcnow())
        embed.set_author(name="Message deleted", icon_url=message.author.avatar_url)
        #embed.set_thumbnail(url=message.author.avatar_url)
        #embed.add_field(name="Author", value="**{}**\n*ID: {}*".format(str(message.author), message.author.id), inline=True)
        embed.add_field(name="Author", value=message.author.mention)
        #embed.add_field(name="Channel", value="{}\n*ID: {}*".format(message.channel.mention, message.channel.id), inline=True)
        embed.add_field(name="Channel", value=message.channel.mention)
        #embed.add_field(name="TTS", value="Yes" if message.tts else "No")
        #embed.add_field(name="Pinned", value="Yes" if message.pinned else "No", inline=False)
        embed.add_field(name="Message ID", value=message.id, inline=False)
        try:
            embed.add_field(name="Content", value=message.content, inline=False)
        except:
            pass
        await channel.send(embed=embed)
    except:
        return


@bot.event
async def on_message_edit(before, after):
    """Event triggered on a message edition."""
    if (after.guild is None) or (before.content == after.content) or (after.author.bot):
        return
    
    result = await bot.fetchval("SELECT channel_id FROM logs WHERE server_id = $1", after.guild.id)
    if result is None:
        await bot.execute("DELETE FROM logs WHERE server_id = $1", after.guild.id)
        return
    
    channel = await bot.fetch_channel(result)
    if channel is None:
        await bot.execute("DELETE FROM logs WHERE server_id = $1", after.guild.id)
        return
    
    try:
        embed = discord.Embed(description=f"[Jump to message]({after.jump_url})", color=bot.embedcolours["MessageEdition"], timestamp=datetime.utcnow())
        embed.set_author(name="Message edited", icon_url=after.author.avatar_url)
        # embed.set_thumbnail(url=after.author.avatar_url)
        embed.add_field(name="Author", value=after.author.mention)
        embed.add_field(name="Channel", value=after.channel.mention)
        embed.add_field(name="Message ID", value=after.id, inline=False)
        embed.add_field(name="Before", value=before.content, inline=False)
        embed.add_field(name="After", value=after.content, inline=False)
        await channel.send(embed=embed)
    except:
        return


@bot.event
async def on_raw_reaction_add(payload):
    """Event triggered when a reaction has been added."""
    member = payload.member
    if member is None: return

    if member.bot: return

    emoji_id = str(payload.emoji) if payload.emoji.id is None else str(payload.emoji.id)
    result = await bot.fetchrow("SELECT * FROM autoroles WHERE message_id = $1", payload.message_id)
    if result is None:
        return
    
    try: guild = await bot.fetch_guild(payload.guild_id)
    except: return
    
    roles_id, emojis_id, restrictions, _, inverses, msgs = result[2:]

    try: list_index = emojis_id.index(emoji_id)
    except ValueError: return

    inversed = inverses[list_index]

    role = guild.get_role(roles_id[list_index])
    if role is None: return

    if (inversed and role not in member.roles) or (not inversed and role in member.roles): return

    restriction = restrictions[list_index]
    if restriction:
        restriction = guild.get_role(restriction)
        if restriction is None: return
    else:
        restriction = None
    
    if restriction and restriction not in member.roles: return

    if inversed:
        try: await member.remove_roles(role, reason="Autorole")
        except: return
    else:
        try: await member.add_roles(role, reason="Autorole")
        except: return
    
    if msgs[list_index]:
        try: await member.send("{0} I successfully {1} the role **{2}**{3}".format(utils.CustomEmojis.GreenCheck, ("removed" if inversed else "gave you"), role.name, (" from you." if inversed else ".")))
        except: return


@bot.event
async def on_raw_reaction_remove(payload):
    """Event triggered when a reaction has been removed."""    
    if payload.guild_id is None: return

    try: guild = await bot.fetch_guild(payload.guild_id)
    except: return

    try: member = await guild.fetch_member(payload.user_id)
    except: return

    if member.bot: return
    
    emoji_id = str(payload.emoji) if payload.emoji.id is None else str(payload.emoji.id)
    result = await bot.fetchrow("SELECT * FROM autoroles WHERE message_id = $1", payload.message_id)
    if result is None:
        return
    
    try: guild = await bot.fetch_guild(payload.guild_id)
    except: return
    
    roles_id, emojis_id, restrictions, locks, inverses, msgs = result[2:]

    try: list_index = emojis_id.index(emoji_id)
    except ValueError: return

    if locks[list_index]: return
    
    inversed = inverses[list_index]

    role = guild.get_role(roles_id[list_index])
    if role is None: return

    if (not inversed and role not in member.roles) or (inversed and role in member.roles): return

    restriction = restrictions[list_index]
    if restriction:
        restriction = guild.get_role(restriction)
        if restriction is None: return
    else:
        restriction = None
    
    if restriction and restriction not in member.roles: return

    if inversed:
        try: await member.add_roles(role, reason="Autorole")
        except: return
    else:
        try: await member.remove_roles(role, reason="Autorole")
        except: return
    
    if msgs[list_index]:
        try: await member.send("{} I successfully {} the role **{}**{}".format(utils.CustomEmojis.GreenCheck, ("gave you" if inversed else "removed"), role.name, ("." if inversed else " from you.")))
        except: return


@bot.command()
@commands.is_owner()
async def refresh(ctx, *, cog=None):
    if cog is None:
        await ctx.send(":point_right: **No cog to refresh!**")
        return
    cog = cog.lower()
    try:
        bot.reload_extension(f"cogs.{cog}")
    except:
        await ctx.send(f":point_right: Cog **{cog}** could not be reloaded!")
        return
    await ctx.send(f":point_right: Cog **{cog}** has been successfully reloaded!")


@bot.command()
@commands.is_owner()
async def execute(ctx, *, query: str = None):
    if query is None:
        raise utils.SpecialError(":point_right: **Error: no query input!**")

    try:
        await bot.execute(query)
    except Exception as e:
        raise utils.SpecialError(e)

    await ctx.send("{} **Successfully executed the query!**".format(utils.CustomEmojis.GreenCheck))


@bot.command()
@commands.is_owner()
async def fetch(ctx, *, query: str = None):
    if query is None:
        raise utils.SpecialError(":point_right: **Error: no query input!**")

    try:
        res = await bot.fetch(query)
    except Exception as e:
        raise utils.SpecialError(e)
    
    if res is None:
        await ctx.send(":point_right: **No value retrieved!**")
        return
    
    await ctx.send("{} Value fetched: **{}**.".format(utils.CustomEmojis.GreenCheck, res))


async def run_app():
    try:
        await bot.create_db_pool(DB_TOKEN)
        await bot.start(TOKEN)
    except KeyboardInterrupt:
        await bot.close_connection()


# ------------------- RUNNING BOT -------------------
if __name__ == "__main__":
    for cog in bot.command_cogs:
        bot.load_extension(f"cogs.{cog}")
    
    bot.start_time = datetime.utcnow()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_app())
