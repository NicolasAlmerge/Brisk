#!/usr/bin/env python3


import discord
from discord.ext import commands
import typing
from . import utils


class Mod(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    @commands.command()
    @utils.has_guild_permissions(kick_members=True)
    @utils.bot_has_guild_permissions(kick_members=True)
    @utils.set_cooldown()
    async def kick(self, ctx, members: commands.Greedy[discord.Member]=None, *, reason=None):
        if not members:
            await ctx.send(":point_right: **Error: you didn't input users you want to kick from this server!**")
            return

        members = utils.remove_duplicates(members)
        kickhimself = False
        goodbyebot = False
        botisowner = False
        userisowner = False
        botrolehigher = False
        botowner = None
        kicks = []
        noperms = []
        othererrors = []
        userrolehigher = []
        guild_owner = ctx.guild.owner

        if reason:
            reason += (", " + utils.get_reason(ctx, capitalise=False))
        else:
            reason = utils.get_reason(ctx)

        for user in members:
            if ctx.author == user:
                kickhimself = True
                continue

            if user == guild_owner:
                if user == self.bot.user:
                    botisowner = True
                    continue
                userisowner = True
                continue

            usermention = user.mention

            if (ctx.author.id in self.bot.developers) or (ctx.author == guild_owner) or (ctx.author.top_role.position > user.top_role.position):
                if user == self.bot.user:
                    goodbyebot = True
                    continue
                if user.id == self.bot.owner_id:
                    if not (ctx.author.guild_permissions.kick_members or ctx.guild_permissions.ban_members) or (ctx.author != guild_owner and ctx.author.top_role.position <= user.top_role.position):
                        botowner = usermention
                        continue
                try:
                    await ctx.guild.kick(user, reason=reason)
                except discord.Forbidden:
                    noperms.append(usermention)
                    continue
                except:
                    othererrors.append(usermention)
                    continue
                kicks.append(usermention)
                continue

            if user == self.bot.user:
                botrolehigher = True
                continue
            userrolehigher.append(usermention)

        if len(kicks) == len(members):
            if len(kicks) == 1:
                await ctx.send(":boot: {}** has been successfully kicked from the server!**".format(*kicks))
                return
            await ctx.send(":boot: {}** have been successfully kicked from the server!**".format("**, **".join(kicks)[::-1].replace(" ,", " dna ", 1)[::-1]))
            return

        if len(userrolehigher) == len(members):
            if len(userrolehigher) == 1:
                await ctx.send(":no_entry_sign: **You do not have permission to kick **{}**, as this user's highest role is the same or higher than yours!**".format(*userrolehigher))
                return
            await ctx.send(":no_entry_sign: **You couldn't kick any members specified as each of them's highest role is the same or higher than yours!")
            return

        if len(noperms) == len(members):
            if len(noperms) == 1:
                await ctx.send(":no_good: **I do not have permission to kick **{}**!**".format(*noperms))
                return
            await ctx.send(":no_good: **I do not have permission to kick any of the members specified!**")
            return

        if len(othererrors) == len(members):
            if len(othererrors) == 1:
                await ctx.send(":thumbsdown: **Kicking **{}** failed!** Please retry later!".format(*othererrors))
                return
            await ctx.send(":thumbsdown: **Kicking failed for every member specified!** Please retry later!")
            return

        msg1 = msg2 = msg3 = msg4 = msg5 = msg6 = msg7 = msg8 = ""

        if kicks:
            if len(kicks) == 1:
                msg1 = ":boot: {}** has been successfully kicked from the server!**".format(*kicks)
            else:
                msg1 = ":boot: {}** have been successfully kicked from the server!**".format("**, **".join(kicks)[::-1].replace(" ,", " dna ", 1)[::-1])

        if kickhimself:
            msg2 = "\n:point_right: **You cannot kick yourself from a server!**"

        if userrolehigher:
            if len(userrolehigher) == 1:
                msg3 = "\n:no_entry_sign: **You do not have permission to kick **{}** as this user's highest role is the same or higher than yours!**".format(*userrolehigher)
            else:
                msg3 = "\n:no_entry_sign: **You do not have permission to kick **{}** as each of them's highest role is the same or higher than yours!**".format("**, **".join(userrolehigher)[::-1].replace(" ,", " dna ", 1)[::-1])

        if userisowner:
            msg4 = "\n:no_entry_sign: **You do not have permission to kick **{}**, as this user owns the server!**".format(str(guild_owner))

        if botowner:
            msg8 = "\n:no_entry_sign: **You do not have permission to kick **{}**!**".format(botowner)

        if botisowner:
            msg5 = "\n:point_right: **You could not kick me as I own the server!**"
        elif botrolehigher:
            msg5 = "\n:point_right: **You could not kick me as my highest role is the same or higher than yours!**"

        if noperms:
            if len(noperms) == 1:
                msg6 = "\n:no_good: **I do not have permission to kick **{}**!**".format(*noperms)
            else:
                msg6 = "\n:no_good: **I do not have permission to kick **{}**!**".format("**, **".join(noperms)[::-1].replace(" ,", " dna ", 1)[::-1])

        if othererrors:
            if len(othererrors) == 1:
                msg7 = "\n:thumbsdown: **Kicking **{}** failed!** Please retry later!".format(*othererrors)
            else:
                msg7 = "\n:thumbsdown: **Kicking **{}** failed!** Please retry later!".format("**, **".join(othererrors)[::-1].replace(" ,", " dna ", 1)[::-1])

        try:
            await ctx.send(msg1+msg2+msg3+msg4+msg8+msg5+msg6+msg7)
        except:
            pass

        if goodbyebot:
            try:
                await ctx.guild.leave()
            except:
                await ctx.send(":point_right: **Error: I could not leave this server!** Please retry later!")
                return
            try:
                await ctx.author.send(":thumbsup: I have successfully left the server **{}**!".format(ctx.guild.name))
            except:
                return

    @commands.command()
    @utils.has_guild_permissions(ban_members=True)
    @utils.bot_has_guild_permissions(ban_members=True)
    @utils.set_cooldown()
    async def ban(self, ctx, members: commands.Greedy[discord.Member]=None, msgdelete: typing.Optional[int]=0, *, reason=None):
        if not members:
            await ctx.send(":point_right: **Error: you didn't input users you want to ban from this server!**")
            return
        members = utils.remove_duplicates(members)
        banhimself = False
        goodbyebot = False
        botisowner = False
        userisowner = False
        botrolehigher = False
        botowner = None
        bans = []
        noperms = []
        othererrors = []
        userrolehigher = []
        guild_owner = ctx.guild.owner

        if reason:
            reason += (", " + utils.get_reason(ctx, capitalise=False))
        else:
            reason = utils.get_reason(ctx)

        if msgdelete < 0:
            msgdelete = 0
        elif msgdelete > 7:
            msgdelete = 7

        for user in members:
            if ctx.author == user:
                banhimself = True
                continue

            if user == guild_owner:
                if user == self.bot.user:
                    botisowner = True
                    continue
                userisowner = True
                continue

            usermention = user.mention

            if (ctx.author.id in self.bot.developers) or (ctx.author == guild_owner) or (ctx.author.top_role.position > user.top_role.position):
                if user == self.bot.user:
                    goodbyebot = True
                    continue
                if user.id == self.bot.owner_id:
                    if not ctx.guild_permissions.ban_members or (ctx.author != guild_owner and ctx.author.top_role.position <= user.top_role.position):
                        botowner = usermention
                        continue
                try:
                    await ctx.guild.ban(user, reason=reason, delete_message_days=msgdelete)
                except discord.Forbidden:
                    noperms.append(usermention)
                    continue
                except:
                    othererrors.append(usermention)
                    continue
                bans.append(usermention)
                continue

            if user == self.bot.user:
                botrolehigher = True
                continue
            userrolehigher.append(usermention)

        if len(bans) == len(members):
            if len(bans) == 1:
                await ctx.send(":hammer: {}** has been successfully banned from the server!**".format(*bans))
                return
            await ctx.send(":hammer: {}** have been successfully banned from the server!**".format("**, **".join(bans)[::-1].replace(" ,", " dna ", 1)[::-1]))
            return

        if len(userrolehigher) == len(members):
            if len(userrolehigher) == 1:
                await ctx.send(":no_entry_sign: **You do not have permission to ban **{}**, as this user's highest role is the same or higher than yours!**".format(*userrolehigher))
                return
            await ctx.send(":no_entry_sign: **You couldn't ban any members specified as each of them's highest role is the same or higher than yours!")
            return

        if len(noperms) == len(members):
            if len(noperms) == 1:
                await ctx.send(":no_good: **I do not have permission to ban **{}**!**".format(*noperms))
                return
            await ctx.send(":no_good: **I do not have permission to ban any of the members specified!**")
            return

        if len(othererrors) == len(members):
            if len(othererrors) == 1:
                await ctx.send(":thumbsdown: **Banning **{}** failed!** Please retry later!".format(*othererrors))
                return
            await ctx.send(":thumbsdown: **Banning failed for every member specified!** Please retry later!")
            return

        msg1 = msg2 = msg3 = msg4 = msg5 = msg6 = msg7 = msg8 = msg9 = ""

        if bans:
            if len(bans) == 1:
                msg1 = ":hammer: {}** has been successfully banned from the server!**".format(*bans)
            else:
                msg1 = ":hammer: {}** have been successfully banned from the server!**".format("**, **".join(bans)[::-1].replace(" ,", " dna ", 1)[::-1])

        if banhimself:
            msg2 = "\n:point_right: **You cannot ban yourself from a server!**"

        if userrolehigher:
            if len(userrolehigher) == 1:
                msg3 = "\n:no_entry_sign: **You do not have permission to ban **{}** as this user's highest role is the same or higher than yours!**".format(*userrolehigher)
            else:
                msg3 = "\n:no_entry_sign: **You do not have permission to ban **{}** as each of them's highest role is the same or higher than yours!**".format("**, **".join(userrolehigher)[::-1].replace(" ,", " dna ", 1)[::-1])

        if userisowner:
            msg4 = "\n:no_entry_sign: **You do not have permission to ban **{}**, as this user owns the server!**".format(str(guild_owner))

        if botowner:
            msg9 = "\n:no_entry_sign: **You do not have permission to ban **{}**!**".format(botowner)

        if botisowner:
            msg5 = "\n:no_entry_sign: **You could not ban me as I own the server!**"
        elif botrolehigher:
            msg5 = "\n:no_entry_sign: **You could not ban me as my highest role is the same or higher than yours!**"

        if noperms:
            if len(noperms) == 1:
                msg6 = "\n:no_good: **I do not have permission to ban **{}**!**".format(*noperms)
            else:
                msg6 = "\n:no_good: **I do not have permission to ban **{}**!**".format("**, **".join(noperms)[::-1].replace(" ,", " dna ", 1)[::-1])

        if goodbyebot:
            msg7 = "\n:point_right: **I cannot ban myself from a server!**"

        if othererrors:
            if len(othererrors) == 1:
                msg8 = "\n:thumbsdown: **Banning **{}** failed!** Please retry later!".format(*othererrors)
            else:
                msg8 = "\n:thumbsdown: **Banning **{}** failed!** Please retry later!".format("**, **".join(othererrors)[::-1].replace(" ,", " dna ", 1)[::-1])

        try: await ctx.send(msg1+msg2+msg3+msg4+msg9+msg5+msg6+msg7+msg8)
        finally: return

    @commands.command()
    @utils.has_guild_permissions(ban_members=True)
    @utils.bot_has_guild_permissions(ban_members=True)
    @utils.set_cooldown()
    async def unban(self, ctx, *memberlist):
        if not memberlist:
            await ctx.send(":point_right: **Error: you didn't input users you want to unban from this server!**")
            return

        try:
            bans = tuple(ban_entry.user for ban_entry in await ctx.guild.bans())
        except discord.Forbidden:
            await ctx.send(":no_good: **Permission to continue has just been denied to me!**\nPlease make sure I have the `Ban Members` permission and retry again.")
            return
        except:
            await ctx.send(":thumbsdown: **Getting server bans failed!** Please retry later!")
            return

        if not bans:
            await ctx.send(":point_right: **No members have been banned from this server!**")
            return

        members = []
        usersnotfound = []

        for user in memberlist:
            try: userfound = await commands.UserConverter().convert(ctx, user)
            except:
                usersnotfound.append(user)
                continue
            members.append(userfound)

        members = utils.remove_duplicates(members)

        if len(usersnotfound) == len(memberlist):
            usersnotfound = utils.remove_duplicates(usersnotfound)
            if len(usersnotfound) == 1:
                await ctx.send(":point_right: **User **`{}`** could not be found!**".format(*usersnotfound))
                return
            await ctx.send(":point_right: **Users you enetered could not be found!**")
            return

        unbanhimself = False
        goodbyebot = False
        unbans = []
        noperms = []
        notfound = []
        othererrors = []

        reason = utils.get_reason(ctx)

        for user in members:
            if ctx.author == user:
                unbanhimself = True
                continue
            if user == self.bot.user:
                goodbyebot = True
                continue

            usermention = user.mention

            if user not in bans:
                notfound.append(usermention)
                continue

            try:
                await ctx.guild.unban(user, reason=reason)
            except discord.Forbidden:
                noperms.append(usermention)
                continue
            except:
                othererrors.append(usermention)
                continue
            unbans.append(usermention)
            continue

        if len(unbans) == len(members):
            if len(unbans) == 1:
                await ctx.send(":tada: {}** has been successfully unbanned from the server!**".format(*unbans))
                return
            await ctx.send(":tada: {}** have been successfully unbanned from the server!**".format("**, **".join(unbans)[::-1].replace(" ,", " dna ", 1)[::-1]))
            return

        if len(notfound) == len(members):
            if len(notfound) == 1:
                await ctx.send(":point_right: {}** has not been banned from this server!**".format(*notfound))
                return
            await ctx.send(":point_right: **None of the specified users have been banned from this server!**")
            return

        if len(noperms) == len(members):
            if len(noperms) == 1:
                await ctx.send(":no_good: **I do not have permission to unban **{}**!**".format(*noperms))
                return
            await ctx.send(":no_good: **I do not have permission to unban any of the members specified!**")
            return

        if len(othererrors) == len(members):
            if len(othererrors) == 1:
                await ctx.send(":thumbsdown: **Unbanning **{}** failed!** Please retry later!".format(*othererrors))
                return
            await ctx.send(":thumbsdown: **Unbanning failed for every member specified!** Please retry later!")
            return

        msg1 = msg2 = msg3 = msg4 = msg5 = msg6 = msg7 = ""

        if unbans:
            if len(unbans) == 1:
                msg1 = ":tada: {}** has been successfully unbanned from the server!**".format(*unbans)
            else:
                msg1 = ":tada: {}** have been successfully unbanned from the server!**".format("**, **".join(unbans)[::-1].replace(" ,", " dna ", 1)[::-1])

        if unbanhimself:
            msg2 = "\n:point_right: **You are not banned from this server!**"

        if goodbyebot:
            msg3 = "\n:point_right: **I am not banned from this server!**"

        if notfound:
            if len(notfound) == 1:
                msg4 = "\n:point_right: {}** has not been banned from this server!**".format(*notfound)
            else:
                msg4 = "\n:point_right: {}** have not been banned from this server!**".format("**, **".join(notfound)[::-1].replace(" ,", " dna ", 1)[::-1])

        if noperms:
            if len(noperms) == 1:
                msg5 = "\n:no_good: **I do not have permission to unban **{}**!**".format(*noperms)
            else:
                msg5 = "\n:no_good: **I do not have permission to unban **{}**!**".format("**, **".join(noperms)[::-1].replace(" ,", " dna ", 1)[::-1])

        if othererrors:
            if len(othererrors) == 1:
                msg6 = "\n:thumbsdown: **Unbanning **{}** failed!** Please retry later!".format(*othererrors)
            else:
                msg6 = "\n:thumbsdown: **Unbanning **{}** failed!** Please retry later!".format("**, **".join(othererrors)[::-1].replace(" ,", " dna ", 1)[::-1])

        if usersnotfound:
            usersnotfound = utils.remove_duplicates(usersnotfound)
            if len(usersnotfound) == 1:
                msg7 = "\n:point_right: **User **`{}`** could not be found!**".format(*usersnotfound)
            else:
                msg7 = "\n:point_right: **Users **`{}`** could not be found!**".format("`**, **`".join(usersnotfound)[::-1].replace(" ,", " dna ", 1)[::-1])

        try: await ctx.send(msg1+msg2+msg3+msg4+msg5+msg6+msg7)
        finally: return

    @commands.guild_only()
    @commands.command()
    @utils.has_permissions(manage_messages=True, read_message_history=True)
    @utils.bot_has_permissions(manage_messages=True, read_message_history=True)
    @utils.set_cooldown()
    async def clear(self, ctx, amount=1000):
        try:
            amount = int(amount)
            if amount <= 0:
                await ctx.send(":point_right: **You need to specify an integer > 0!**")
                return
            if amount > 1000:
                amount = 1000
        except ValueError:
            await ctx.send(":point_right: **You need to specify an integer > 0!**")
            return

        try:
            messages = await ctx.channel.purge(limit=amount+1, check=utils.check_not_pinned)
            messages = len(messages)

        except discord.Forbidden:
            if not ctx.guild.me.permissions_in(ctx.channel).manage_messages:
                if not ctx.guild.me.permissions_in(ctx.channel).read_message_history:
                    await ctx.send(":no_good: **I do not have permission to manage messages and read message history on this channel!**")
                    return
                await ctx.send(":no_good: **I do not have permission to manage messages on this channel!**")
                return
            await ctx.send(":no_good: **I do not have permission to view message history on this channel!**")
            return

        except:
            await ctx.send(":thumbsdown: **Clearing message failed!** Please try again later!")
            return

        if not messages:
            await ctx.send(":point_right: **No messages could be cleared!**", delete_after=3)
            return
        if messages == 1:
            await ctx.send(utils.CustomEmojis.GreenCheck + " **1 message has been successfully cleared!**", delete_after=3)
            return
        await ctx.send(utils.CustomEmojis.GreenCheck + " **{} messages has been successfully cleared!**".format(utils.number_format(messages)), delete_after=3)

    @commands.guild_only()
    @commands.command()
    @utils.has_permissions(manage_messages=True, read_message_history=True)
    @utils.bot_has_permissions(manage_messages=True, read_message_history=True)
    @utils.set_cooldown()
    async def clearall(self, ctx, amount=None):
        if not amount:
            amount = 1000
        else:
            try:
                amount = int(amount)
                if amount <= 0:
                    await ctx.send(":point_right: **You need to specify an integer > 0!**")
                    return
                if amount > 1000: amount = 1000
            except ValueError:
                await ctx.send(":point_right: **You need to specify an integer > 0!**")
                return

        try:
            messages = await ctx.channel.purge(limit=amount+1)
            messages = len(messages) - 1
            if messages < 0:
                messages = 0
        except discord.Forbidden:
            if not ctx.guild.me.permissions_in(ctx.channel).manage_messages:
                if not ctx.guild.me.permissions_in(ctx.channel).read_message_history:
                    await ctx.send(":no_good: **I do not have permission to manage messages and read message history on this channel!**")
                    return
                await ctx.send(":no_good: **I do not have permission to manage messages on this channel!**")
                return
            await ctx.send(":no_good: **I do not have permission to view message history on this channel!**")
            return
        except:
            await ctx.send(":thumbsdown: **Clearing message failed!** Please try again later!")
            return

        if not messages:
            await ctx.send(":point_right: **No messages could be cleared!**", delete_after=3)
            return
        if messages == 1:
            await ctx.send(utils.CustomEmojis.GreenCheck + " **1 message has been successfully cleared!**", delete_after=3)
            return
        await ctx.send(utils.CustomEmojis.GreenCheck + " **{} messages has been successfully cleared!**".format(messages), delete_after=3)

    @commands.guild_only()
    @commands.command()
    @utils.has_any_permissions(manage_messages=True, manage_roles=True)
    @utils.bot_has_permissions(manage_roles=True)
    @utils.set_cooldown()
    async def lock(self, ctx, channel=None, *, reason=None):
        if channel:
            try: channel = await commands.TextChannelConverter().convert(ctx, channel)
            except: raise utils.ConverterNotFoundError("Text Channel")
        else:
            channel = ctx.channel
        try:
            if reason:
                reason2 = reason + ", " + utils.get_reason(ctx, capitalise=False)
            else:
                reason2 = utils.get_reason(ctx)
            await channel.set_permissions(target=ctx.guild.me, reason=reason2, send_messages=True)
            await channel.set_permissions(target=ctx.guild.default_role, reason=reason2, send_messages=False, add_reactions=False)
            if reason:
                await ctx.send(":lock: **This channel has been locked by **{}** for reason: **`{}`**!**".format(ctx.author.mention, reason))
            else:
                await ctx.send(":lock: **This channel has been locked by **{}**!**".format(ctx.author.mention))
            await channel.set_permissions(target=ctx.guild.me, overwrite=None, reason=reason2)
        except discord.Forbidden:
            await ctx.send(":no_good: **I do not have permission to manage permissions on this channel!**")
        except:
            await ctx.send(":thumbsdown: **Changing channel permissions failed!**")

    @commands.guild_only()
    @commands.command()
    @utils.has_any_permissions(manage_messages=True, manage_roles=True)
    @utils.bot_has_permissions(manage_roles=True)
    @utils.set_cooldown()
    async def unlock(self, ctx, channel=None):
        if channel:
            try: channel = await commands.TextChannelConverter().convert(ctx, channel)
            except: raise utils.ConverterNotFoundError("Text Channel")
        else:
            channel = ctx.channel
        try:
            reason = utils.get_reason(ctx)
            await channel.set_permissions(target=ctx.guild.me, reason=reason, send_messages=True)
            await channel.set_permissions(target=ctx.guild.default_role, reason=reason, send_messages=None, add_reactions=None)
            await ctx.send(":unlock: **This channel has been unlocked by **{}**!**".format(ctx.author.mention))
            await channel.set_permissions(target=ctx.guild.me, overwrite=None, reason=reason)
        except discord.Forbidden:
            await ctx.send(":no_good: **I do not have permission to manage permissions on this channel!**")
        except:
            await ctx.send(":thumbsdown: **Changing channel permissions failed!**")


def setup(bot):
    bot.add_cog(Mod(bot))