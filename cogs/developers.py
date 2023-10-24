#!/usr/bin/env python3


import discord
from discord.ext import commands
import string
from io import StringIO
from . import utils


class Developers(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    async def cog_check(self, ctx):
        return utils.is_bot_dev(ctx)


    @commands.command(aliases=["sd", "logout"])
    async def shutdown(self, ctx):
        try: await ctx.send(":sleeping: **Bot shutting down...**")
        except: pass
        try: utils.clear_downloads()
        except: pass
        # try:
        #     sd_channel = self.bot.get_channel(self.bot.connections_channel)
        #     if sd_channel:
        #         await sd_channel.send("@everyone :small_orange_diamond: **Discordnnected**\n*I need a restful sleep. I'll be back very soon!*:sleeping:")
        # except: pass
        try: await self.bot.change_presence(status=discord.Status.offline)
        except: pass
        await self.bot.close_connection()

    @commands.command(aliases=["logsearch"])
    async def searchlog(self, ctx, *, search: str = None):
        if not search:
            await ctx.send(":point_right: **Error: no search input!**")
            return
        with open(self.bot.logfile) as f:
            res = tuple(line for line in f.read().splitlines() if search.lower() in line.lower())
        if not res:
            await ctx.send(":point_right: No result found for search: **{}**!".format(search))
            return
        await ctx.send(
            content=":point_right: **Here is what I found!**",
            file=discord.File(
                fp=StringIO("{} result{} for search: '{}':\n\n{}".format(len(res), "s" if len(res) > 1 else "", search, "\n".join(res))),
                filename="result.log"
            )
        )

    @commands.command()
    async def reset(self, ctx, *db):
        pass

    @commands.command()
    async def disable(self, ctx):
        if self.bot.disabled:
            raise utils.SpecialError(":point_right: **Bot is already disabled!**")
        self.bot.disabled = True
        await self.bot.change_presence(activity=discord.Activity(name="Bot disabled", type=discord.ActivityType.watching), status="dnd")
        await ctx.send(":point_right: **Bot is now disabled!**\nOnly bot developers can access its commands.")

    @commands.command()
    async def enable(self, ctx):
        if not self.bot.disabled:
            raise utils.SpecialError(":point_right: **Bot is already enabled!**")
        self.bot.disabled = False
        await self.bot.change_presence(activity=self.bot.activity, status=self.bot.defaultstatus)
        await ctx.send(":point_right: **Bot is enabled again!**")

    @commands.command()
    @commands.guild_only()
    async def status(self, ctx, *, option: str = None):
        bot_status = ctx.guild.me.status
        if not option:
            optiontext = bot_status
            if optiontext == self.bot.defaultstatus:
                complement = " (default status)"
            else:
                complement = ""
            if optiontext == "dnd":
                optiontext = "do not disturb"
            optiontext = string.capwords(optiontext)
            await ctx.send(":point_right: My status has been set to **{}**{}.\nThe available bot status are `online`, `idle`, `dnd` and `invisible`.".format(optiontext, complement))
            return

        option = option.replace(" ", "").lower()
        if option == "offline":
            option = "invisible"
        elif option == "donotdisturb":
            option = "dnd"
        elif option in ("default", "defaultstatus", "reset"):
            option = self.bot.defaultstatus

        if not any(s == option for s in [e.value for e in discord.Status]):
            await ctx.send(utils.CustomEmojis.RedCross + " **Invalid Usage!** The correct usages are `online`, `idle`, `dnd` and `invisible`.")
            return
        optiontext = option
        if option == self.bot.defaultstatus:
            complement = " (default status)"
        else:
            complement = ""
        if bot_status == option:
            if option == "dnd":
                optiontext = "do not disturb"
            await ctx.send(":point_right: Status has already been set to **{}**{}.".format(string.capwords(optiontext), complement))
            return
        if option == "online":
            emoji = utils.CustomEmojis.Online
            afk = False
        elif option == "idle":
            emoji = utils.CustomEmojis.Idle
            afk = True
        elif option == "dnd":
            emoji = utils.CustomEmojis.DND
            optiontext = "do not disturb"
            afk = False
        elif option == "invisible":
            emoji = utils.CustomEmojis.Invisible
            afk = False
        else:
            emoji = utils.CustomEmojis.GreenCheck
            afk = False
        await self.bot.change_presence(activity=self.bot.activity, status=option, afk=afk)
        await ctx.send("{} Set status to **{}**{}.".format(emoji, string.capwords(optiontext), complement))


    @commands.command(aliases=["disablepremium", "premiumdisable"])
    async def downgrade(self, ctx, *, server: str = None):
        if server is None:
            if ctx.guild is None:
                raise utils.SpecialError(":point_right: **Error: server argument not found and command not invoked in a server.**")
            server = ctx.guild
        else:
            try: server = await commands.GuildConverter().convert(ctx, server)
            except: raise utils.ConverterNotFoundError("Server")
        
        guild_id = server.id
        if guild_id in (self.bot.support_guild, self.bot.dev_guild):
            raise utils.SpecialError(":point_right: **Error: cannot remove premium on a special guild!**")
        
        res = await self.bot.fetchval("SELECT server_id FROM premiumservers WHERE server_id = $1", guild_id)
        if res is None:
            raise utils.SpecialError(":point_right: **Error: server is not premium!**")

        await self.bot.execute("DELETE FROM premiumservers WHERE server_id = $1", guild_id)
        await ctx.send("{} Successfully removed server **{}** from premium guilds.".format(utils.CustomEmojis.GreenCheck, server.name))


    @commands.command()
    async def premiumservers(self, ctx):
        pass


    @commands.command(aliases=["serverleave"])
    async def leaveserver(self, ctx, *, server: str = None):
        if server is None:
            if ctx.guild is None:
                raise utils.SpecialError(":point_right: **Error: server argument not found and command not invoked in a server.**")
            server = ctx.guild
        else:
            try: server = await commands.GuildConverter().convert(ctx, server)
            except: raise utils.ConverterNotFoundError("Server")
        
        if server.id in (self.bot.support_guild, self.bot.dev_guild):
            raise utils.SpecialError(":point_right: **Error: cannot leave this special guild!**")
        
        name = server.name
        try:
            await server.leave()
        except discord.HTTPException:
            raise utils.SpecialError(":point_right: **Error: leaving the guild failed!**")
        
        await ctx.send("{} Successfully left server **{}**!".format(utils.CustomEmojis.GreenCheck, name))


    @commands.group(invoke_without_command=True, case_insensitive=True)
    async def blacklist(self, ctx):
        raise utils.SpecialError(":point_right: **This command should be used to blacklist a user or server.**")


    @blacklist.command(name="user")
    async def bl_user(self, ctx, *, user: str = None):
        if user is None:
            raise utils.SpecialError(":point_right: **Error: no user input!**")

        try: target = await commands.UserConverter().convert(ctx, user)
        except: raise utils.ConverterNotFoundError("User")

        target_id = target.id
        if target_id in self.bot.developers:
            await ctx.send(":point_right: **Error: developers cannot be blacklisted!**")
            return

        # Blacklist user
        result = await self.bot.fetchval("SELECT user_id FROM blacklistedusers WHERE user_id = $1", target_id)
        if result is None:
            await self.bot.execute("INSERT INTO blacklistedusers(user_id) VALUES ($1)", target_id)
            await ctx.send("{} Successfully blacklisted user **{}**!".format(utils.CustomEmojis.GreenCheck, str(target)))
            return
        
        await ctx.send(":point_right: User **{}** has already been blacklisted!".format(str(target)))


    @blacklist.command(name="server")
    async def bl_server(self, ctx, *, server: str = None):
        if server is None:
            if ctx.guild is None:
                raise utils.SpecialError(":point_right: **Error: server argument not found and command not invoked in a server.**")
            server = ctx.guild
        else:
            try: server = await commands.GuildConverter().convert(ctx, server)
            except: raise utils.ConverterNotFoundError("Server")
        
        server_id = server.id
        if server_id in (self.bot.support_guild, self.bot.dev_guild):
            await ctx.send(":point_right: **Error: cannot blacklist support or development guild!**")
            return

        # Blacklist server
        result = await self.bot.fetchval("SELECT server_id FROM blacklistedservers WHERE server_id = $1", server_id)
        if result is None:
            await self.bot.execute("INSERT INTO blacklistedservers(server_id) VALUES ($1)", server_id)
            await ctx.send("{} Successfully blacklisted server **{}**!".format(utils.CustomEmojis.GreenCheck, server.name))
            return
        
        await ctx.send(":point_right: Server **{}** has already been blacklisted!".format(server.name))


def setup(bot):
    bot.add_cog(Developers(bot))