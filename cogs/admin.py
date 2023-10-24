#!/usr/bin/env python3


import discord
from discord.ext import commands
import re
from . import utils


prefixformat = re.compile(
    r"([a-z]|[,?;.:!%\-=^$+><|/])(([a-z]|[,?;.:!%\-=^$+><|/\s]){,4})",
    re.IGNORECASE
)


MOD_PERMS_VALUE = (
    525440 # View channel, view audit log and view guild insights permissions
    + discord.Permissions.membership().value
    + discord.Permissions.text().value
    + discord.Permissions.voice().value
    + discord.Permissions.stage().value
)


class Admin(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    @commands.command(aliases=["setcooldown", "cooldownset"])
    @commands.guild_only()
    @utils.bot_has_permissions(manage_channels=True)
    @utils.has_permissions(manage_channels=True)
    @utils.set_cooldown()
    async def cooldown(self, ctx, cooldown=None):
        cool = ctx.channel.slowmode_delay
        if not cooldown:
            if not cool:
                await ctx.send(":point_right: **The cooldown has been disabled on this channel!**")
                return
            await ctx.send(f":point_right: The cooldown has been set to **{utils.time_format(cool)}** on this channel!")
            return
        if cooldown.lower() in ("dis", "disable"):
            cooldown = 0
        else:
            try:
                cooldown = int(cooldown)
            except ValueError:
                await ctx.send(":point_right: **Error: cooldown must be integer value (representing the number of seconds)!**")
                return
            if cooldown < 0:
                await ctx.send(":point_right: Error: cooldown value cannot be lower than **0 seconds**!")
                return
            if cooldown > 21600:
                await ctx.send(":point_right: Error: cooldown value cannot be greater than **6 hours** (21,600 seconds)!")
                return
        try:
            await ctx.channel.edit(slowmode_delay=cooldown, reason=utils.get_reason(ctx, level="admin"))
        except discord.Forbidden:
            await ctx.send(f"{utils.CustomEmojis.RedCross} **Error: I do not have permission to manage this channel!**")
            return
        except:
            await ctx.send(":thumbsdown: **Changing channel cooldown failed!** Please try again later.")
            return
        if cooldown == cool:
            if not cool:
                await ctx.send(":point_right: **The cooldown on this channel has already been disabled.**")
                return
            await ctx.send(f":point_right: The cooldown on this channel has already been set to **{utils.time_format(cool)}**.")
            return
        if not cooldown:
            await ctx.send(f"{utils.CustomEmojis.GreenCheck} **Successfully disabled cooldown on this channel!**")
            return
        await ctx.send(f"{utils.CustomEmojis.GreenCheck} Successfully set cooldown to **{utils.time_format(cooldown)}** on that channel!")

    @commands.command(aliases=["setprefix", "prefixset"])
    @utils.has_guild_permissions(manage_guild=True)
    @utils.set_cooldown(per=900.0, alter_per=600.0)
    async def prefix(self, ctx, pref=None):
        if pref is None:
            prefix = await self.bot.fetchval("SELECT prefix FROM prefixes WHERE server_id = $1", ctx.guild.id)
            if prefix is None:
                await ctx.send(f":point_right: No custom prefix has been set! **{self.bot.commandprefix}** is the default one.")
                return
            await ctx.send(":point_right: **{0}** is the server prefix.\nExample: `{0}ping`".format(prefix[0]))
            return

        pref = pref.lstrip()
        if not prefixformat.fullmatch(pref):
            await ctx.send(":point_right: **The prefix you entered is invalid!**\nThe prefix must be from one to five characters long (the characters allowed are letters, whitespaces and `,?;.:!%-=^$+><|/`). Whitespaces are taken into account from the second character.")
            return

        prefix = await self.bot.fetchval("SELECT prefix FROM prefixes WHERE server_id = $1", ctx.guild.id)

        if prefix is None:
            if pref == self.bot.commandprefix:
                await ctx.send(f":point_right: **{self.bot.commandprefix}** is already set as the server prefix (default prefix).")
                return

            await self.bot.execute("INSERT INTO prefixes(server_id, prefix) VALUES ($1,$2)", ctx.guild.id, pref)
            await ctx.send("{0} **{1}** is now the server prefix!\nExample: `{1}ping`".format(utils.CustomEmojis.GreenCheck, pref))
            return

        if pref == prefix:
            await ctx.send(":point_right: **{0}** is already set as the server prefix.\nExample: `{0}ping`".format(prefix[0]))
            return

        if pref == self.bot.commandprefix:
            await self.bot.execute("DELETE FROM prefixes WHERE server_id = $1", ctx.guild.id)
            await ctx.send(f":point_right: The server prefix has been reset to **{self.bot.commandprefix}** (default prefix).")
            return

        await self.bot.execute("UPDATE prefixes SET prefix = $1 WHERE server_id = $2", pref, ctx.guild.id)
        await ctx.send("{0} The server prefix has been replaced with **{1}**!\nExample: `{1}ping`".format(utils.CustomEmojis.GreenCheck, pref))

    @commands.group(invoke_without_command=True, case_insensitive=True, aliases=["autoroles"])
    @utils.bot_has_guild_permissions(manage_roles=True)
    @utils.set_cooldown(per=60.0, alter_per=30.0)
    async def autorole(self, ctx, message=None):
        if message is None:
            result = await self.bot.fetch("SELECT message_id, roles_id FROM autoroles WHERE server_id = $1", ctx.guild.id)
            if not result:
                await ctx.send(":point_right: **No autoroles were set in this server!**")
                return
            
            embed = discord.Embed(
                title=":triangular_flag_on_post: Autoroles",
                description="Here are the autoroles registered in this server.\nFor more information, use the `autorole [message ID]` command.",
                colour=utils.random_colour()
            )

            for (message_id, role_id) in result:
                embed.add_field(
                    name="Message ID: " + str(message_id),
                    value="Autoroles registered: " + str(len(role_id)),
                    inline=False
                )
            
            utils.set_footer(ctx, embed)
            await ctx.send(embed=embed)
            return

        try: message = await commands.MessageConverter().convert(ctx, message)
        except: raise utils.ConverterNotFoundError("Message")

        result = await self.bot.fetchrow("SELECT * FROM autoroles WHERE message_id = $1", message.id)
        if result is None:
            await ctx.send(":point_right: **No autoroles were set for this message!**")
            return
        
        roles_id, emojis_id, restrictions, locked, inversed, msgs = result[2:]
        new_roles_ids, rolementions, new_emoji_ids, new_emojis, new_restrictions_id, new_restrictions_mention, new_locked, new_invs, new_msgs = utils.create_lists(9)
        full = True
        empty = True

        for count in range(len(roles_id)):
            role_id = roles_id[count]
            emoji_id = emojis_id[count]

            role = ctx.guild.get_role(role_id)
            try:
                emoji = int(emoji_id)
                try: emoji = await ctx.guild.fetch_emoji(emoji)
                except: emoji = None
            except ValueError:
                emoji = emoji_id

            if restrictions[count]: restr_role = ctx.guild.get_role(restrictions[count])
            else: restr_role = None

            if role is None or emoji is None:
                full = False
                continue

            empty = False

            new_roles_ids.append(role_id)
            rolementions.append(role.name)

            new_emoji_ids.append(emoji_id)
            new_emojis.append(str(emoji))

            if restr_role is None:
                new_restrictions_id.append(0)
                new_restrictions_mention.append(None)
            else:
                new_restrictions_id.append(restr_role.id)
                new_restrictions_mention.append(restr_role.mention)
            
            new_locked.append(locked[count])
            new_invs.append(inversed[count])
            new_msgs.append(msgs[count])
        
        del roles_id, emojis_id, restrictions, locked, inversed, msgs
        length = len(new_roles_ids)
        
        if empty:
            await self.bot.execute("DELETE FROM autoroles WHERE message_id = $1", message.id)
            await ctx.send(":point_right: **No autoroles were set for this message!**")
            return
        
        if not full:
            await self.bot.execute(
                """UPDATE autoroles SET roles_id = $1, emojis = $2, restrictions = $3, locks = $4, inverses = $5, msgs_sent = $6
                WHERE message_id = $7""", new_roles_ids, new_emoji_ids, new_restrictions_id, new_locked, new_invs, new_msgs, message.id
            )
        
        embed = discord.Embed(
            title=":triangular_flag_on_post: Autoroles",
            description="Here are the autoroles associated with message id **" + str(message.id) + "**.",
            colour=utils.random_colour())
        
        for (role, emoji, restriction_role, locked, inversed, message_sent) in zip(rolementions, new_emojis, new_restrictions_mention, new_locked, new_invs, new_msgs):
            embed.add_field(
                name=role,
                value="- __**Emoji**__: " + emoji +
                    "\n- __**Locked**__: " + ("Yes" if locked else "No") +
                    "\n- __**Inversed**__: " + ("Yes" if inversed else "No") +
                    "\n- __**Send Confirmation**__: " + ("Yes" if message_sent else "No") +
                    ("" if restriction_role is None else ("\n- __**Role required**__: " + restriction_role)),
                inline=False
            )
        
        utils.set_footer(ctx, embed)
        await ctx.send(embed=embed)

    @autorole.command(name="add")
    @utils.has_guild_permissions(manage_roles=True)
    @utils.bot_has_guild_permissions(manage_roles=True)
    @utils.bot_has_permissions(manage_messages=True, add_reactions=True)
    @utils.set_cooldown(per=30.0, alter_per=20.0)
    async def autorole_add(self, ctx, message=None, *, role=None):
        if message is None:
            raise utils.SpecialError(":point_right: **Error: no message provided!**")

        try: message = await commands.MessageConverter().convert(ctx, message)
        except: raise utils.ConverterNotFoundError("Message")

        if message.guild is None or message.guild.id != ctx.guild.id:
            raise utils.SpecialError(":point_right: **Error: message must be in this server!**")

        if message.id in self.bot.command_msgs_id:
            raise utils.SpecialError(":point_right: **Error: this message can't be set as an auto-role for now as the bot is already using reactions!**")
        
        desc = "Click on the reaction below if you don't want any."
        colour = utils.random_colour()

        embed = discord.Embed(title="Which role do you want to use?", colour=colour)

        if role is None:
            role = await utils.ask_userinput(ctx=ctx, bot=self.bot, embed=embed)
        try: role = await commands.RoleConverter().convert(ctx, role)
        except: raise utils.ConverterNotFoundError("Role")

        if role.is_default():
            raise utils.SpecialError(":point_right: **Error: cannot create a role reaction with **@\u200beveryone**, as this role is the default role!**")

        if (ctx.guild.owner != ctx.author) and (role.position >= ctx.author.top_role.position):
            raise utils.SpecialError(":point_right: **Error: you cannot create a role reaction with **{}**, as this role is equal or higher than your highest role!**".format(role.mention))

        if (role.position >= ctx.guild.me.top_role.position):
            raise utils.SpecialError(":point_right: **Error: I cannot create a role reaction with **{}**, as this role is equal or higher than my highest role!**".format(role.mention))
        
        if role.managed:
            raise utils.SpecialError(":point_right: **Error: role **{}** cannot be used as it is managed by an integration!**".format(role.mention))

        embed = discord.Embed(title="Which emoji do you want to use?", colour=colour)

        emoji = await utils.ask_userinput(ctx=ctx, bot=self.bot, embed=embed, emoji_only=True)
        
        if isinstance(emoji, discord.PartialEmoji):
            raise utils.SpecialError(":point_right: **Error: emoji must come from this guild!**")

        if isinstance(emoji, discord.Emoji):
            if emoji.guild_id != ctx.guild.id:
                raise utils.SpecialError(":point_right: **Error: emoji must come from this guild!**")
            emoji_id = str(emoji.id)
        
        else:
            emoji_id = emoji

        embed = discord.Embed(title="Which role requirement do you want?", description="Only users with the requirement role will be able to get the role by clicking on the reaction.\n"+desc, colour=colour)

        roles_restr_txt = await utils.ask_userinput(ctx=ctx, bot=self.bot, embed=embed, reaction=utils.CustomEmojis.RedCross)
        if roles_restr_txt is None:
            role_restr_id = 0
        else:
            try: role_restr = commands.RoleConverter().convert(ctx, roles_restr_txt)
            except: raise utils.ConverterNotFoundError("Role")

            if role_restr.is_default():
                raise utils.SpecialError(":point_right: **Error: **@\u200beveryone** cannot be a role requirement as everyone has it!**")

            if role_restr.managed:
                raise utils.SpecialError(":point_right: **Error: role **{}** cannot be a role requirement as it is managed by an integration!**".format(role_restr.mention))

            role_restr_id = role_restr.id

        embed = discord.Embed(title="Do you want the role reaction to be locked?", description="Adding/removing role will only work the first time if this is enabled.", colour=colour)
        locked = await utils.ask_userinput(ctx=ctx, bot=self.bot, embed=embed, use_reactions=True)

        embed = discord.Embed(title="Do you want the role reaction to be inversed?", description="Role will be removed when clicking instead of added if this is enabled.", colour=colour)
        inversed = await utils.ask_userinput(ctx=ctx, bot=self.bot, embed=embed, use_reactions=True)

        embed = discord.Embed(title="Do you want the bot to send a DM to the user after he reacts?", colour=colour)
        msg = await utils.ask_userinput(ctx=ctx, bot=self.bot, embed=embed, use_reactions=True)
        
        search = await self.bot.fetchrow("SELECT * FROM autoroles WHERE message_id = $1", message.id)
        if not search:
            await self.bot.execute(
                "INSERT INTO autoroles VALUES($1,$2,$3,$4,$5,$6::boolean[],$7::boolean[],$8::boolean[])",
                ctx.guild.id, message.id, [role.id], [emoji_id], [role_restr_id], [locked], [inversed], [msg]
            )
            try: await message.add_reaction(emoji)
            except discord.Forbidden: raise utils.BotMissingPermissions(on_guild=False, missing_perms=("add_reactions",))
            except (discord.NotFound, discord.InvalidArgument): raise utils.SpecialError(":point_right: **Error: I could not find this emoji!**")
            await ctx.send("{} **Successfully created role reaction with role **{}** and emoji **{}**.**".format(utils.CustomEmojis.GreenCheck, role.mention, str(emoji)))
            return
        
        roles = search[2]
        if role.id in roles:
            raise utils.SpecialError(":point_right: **Error: role already registered!**")

        emojis = search[3]
        if emoji_id in emojis:
            raise utils.SpecialError(":point_right: **Error: emoji already registered!**")
        
        if len(roles) >= 20:
            raise utils.SpecialError(":point_right: **Error: cannot create more than 20 autoroles for a message!**")

        roles.append(role.id)
        emojis.append(emoji_id)
        restrictions = search[4]+[role_restr_id]
        locks = search[5]+[locked]
        inverses = search[6]+[inversed]
        msgs = search[7]+[msg]

        await self.bot.execute(
            "UPDATE autoroles SET roles_id = $1, emojis = $2, restrictions = $3, locks = $4::boolean[], inverses = $5::boolean[], msgs_sent = $6::boolean[] WHERE message_id = $7",
            roles, emojis, restrictions, locks, inverses, msgs, message.id
        )

        try: await message.add_reaction(emoji)
        except discord.Forbidden: raise utils.BotMissingPermissions(on_guild=False, missing_perms=("add_reactions",))
        except (discord.NotFound, discord.InvalidArgument): raise utils.SpecialError(":point_right: **Error: I could not find this emoji!**")

        await ctx.send("{} **Successfully created role reaction with role **{}** and emoji **{}**.**".format(utils.CustomEmojis.GreenCheck, role.mention, str(emoji)))


    @autorole.command(name="remove")
    @utils.has_guild_permissions(manage_roles=True)
    @utils.bot_has_guild_permissions(manage_roles=True)
    @utils.bot_has_permissions(manage_messages=True)
    @utils.set_cooldown(per=30.0, alter_per=20.0)
    async def autorole_remove(self, ctx, message=None, *, role=None):
        if message is None:
            raise utils.SpecialError(":point_right: **Error: no message provided!**")

        try: message = await commands.MessageConverter().convert(ctx, message)
        except: raise utils.ConverterNotFoundError("Message")

        if message.guild is None or message.guild.id != ctx.guild.id:
            raise utils.SpecialError(":point_right: **Error: message must be in this server!**")
        
        embed = discord.Embed(
            title="Which role do you want to remove from the autorole?",
            description="This will not delete the role from the server.",
            colour=utils.random_colour()
        )

        if role is None:
            role = await utils.ask_userinput(ctx=ctx, bot=self.bot, embed=embed)
        try: role = await commands.RoleConverter().convert(ctx, role)
        except: raise utils.ConverterNotFoundError("Role")

        if role.is_default():
            raise utils.SpecialError(":point_right: **Error: cannot delete a role reaction with **@\u200beveryone**, as this role is the default role!**")

        if (ctx.guild.owner != ctx.author) and (role.position >= ctx.author.top_role.position):
            raise utils.SpecialError(":point_right: **Error: you cannot delete a role reaction with **{}**, as this role is equal or higher than your highest role!**".format(role.mention))
        
        if role.managed:
            raise utils.SpecialError(":point_right: **Error: role **{}** cannot be used as it is managed by an integration!**".format(role.mention))

        search = await self.bot.fetchrow("SELECT * FROM autoroles WHERE message_id = $1", message.id)
        if not search:
            raise utils.SpecialError(":point_right: **Error: autorole with role **{}** is not set!**".format(role.mention))

        roles_id, emojis_id, restrictions, locks, inverses, msgs = search[2:]
        try: count = roles_id.index(role.id)
        except ValueError: raise utils.SpecialError(":point_right: **Error: autorole with role **{}** is not set!**".format(role.mention))

        try:
            emoji_id = int(emojis_id[count])
        except ValueError:
            emoji = emojis_id[count]
        else:
            try: emoji = await ctx.guild.fetch_emoji(emoji_id)
            except: emoji = None
        
        if len(roles_id) == 1:
            await self.bot.execute("DELETE FROM autoroles WHERE message_id = $1", message.id)
        else:
            roles_id.pop(count)
            emojis_id.pop(count)
            restrictions.pop(count)
            locks.pop(count)
            inverses.pop(count)
            msgs.pop(count)

            await self.bot.execute(
                "UPDATE autoroles SET roles_id = $1, emojis = $2, restrictions = $3, locks = $4::boolean[], inverses = $5::boolean[], msgs_sent = $6::boolean[] WHERE message_id = $7",
                roles_id, emojis_id, restrictions, locks, inverses, msgs, message.id
            )

        if emoji:
            try: await message.clear_reaction(emoji)
            except: pass
            await ctx.send("{} **Successfully deleted role reaction with the **{}** role and **{}** emoji!**".format(utils.CustomEmojis.GreenCheck, role.mention, str(emoji)))
            return
        
        await ctx.send("{} **Successfully deleted role reaction with the **{}** role!**".format(utils.CustomEmojis.GreenCheck, role.mention))


    @commands.command()
    @utils.has_guild_permissions(administrator=True)
    @utils.bot_has_guild_permissions(administrator=True)
    @utils.set_cooldown()
    async def serverconfig(self, ctx):
        guild = ctx.guild
        top_role = guild.me.top_role

        if (top_role.is_default()) or (top_role.position < len(guild.roles)-1):
            raise utils.SpecialError(":point_right: **Error: my highest role must be the highest role in the server!**")

        embed = discord.Embed(
            title="Confirm Server Configuration",
            description="Are you sure you want to configure the server?\n**This will modify a lot of server settings!**",
            colour=utils.EmbedColours.ConfirmEmbed
        )
        
        await utils.ask_confirmation(ctx=ctx, bot=self.bot, embed=embed)

        reason = utils.get_reason(ctx, level="admin")
        owner = await guild.create_role(name="👑 Owner", permissions=discord.Permissions.all(), colour=discord.Color(value=0x4169e1), hoist=True, mentionable=True, reason=reason)
        admin = await guild.create_role(name="🌟 Administrators", permissions=discord.Permissions.all(), colour=discord.Color(value=0xff0000), hoist=True, mentionable=True, reason=reason)
        mod = await guild.create_role(name="⭐ Moderators", permissions=discord.Permissions(permissions=MOD_PERMS_VALUE), colour=discord.Color(value=0x2ecc71), hoist=True, mentionable=True, reason=reason)
        bots = await guild.create_role(name="💻 Bots", colour=discord.Color(value=0xd6680e), hoist=True, reason=reason)
        muted = await guild.create_role(name="🔒 Muted", colour=discord.Color(value=0x546e7a), hoist=True, reason=reason)
        await guild.default_role.edit(permissions=discord.Permissions(permissions=0x635de41), reason=reason)
        await guild.owner.add_roles(owner, admin, mod, reason=reason)
        await guild.me.add_roles(bots, reason=reason)

        for cat in guild.categories:
            await cat.set_permissions(target=muted, reason=reason, send_messages=False, add_reactions=False, speak=False, mute_members=False, use_voice_activation=True)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                send_messages=False, add_reactions=False, speak=False, mute_members=False, use_voice_activation=True)
        }
        infos = await guild.create_category_channel(name="Informations", overwrites=overwrites, reason=reason)
        await infos.edit(position=0, reason=reason)
        newbies = await guild.create_text_channel(name="new-members", position=0, category=infos, reason=reason)
        await guild.create_text_channel(name="rules", position=1, category=infos, reason=reason)

        overwrites2 = {
            guild.default_role: discord.PermissionOverwrite(
                send_messages=False)
        }
        ann = await guild.create_text_channel(name="announcements", position=2, category=infos, overwrites=overwrites2, reason=reason)
        await ann.set_permissions(target=muted, reason=reason, send_messages=False, add_reactions=False)
        groups = await guild.create_category_channel(name="Group Chats", reason=reason)
        await groups.set_permissions(target=muted, reason=reason, send_messages=False, add_reactions=False, speak=False, mute_members=False, use_voice_activation=True)
        await guild.create_voice_channel(name="Group #1", user_limit=3, category=groups, reason=reason)
        await guild.create_voice_channel(name="Group #2", user_limit=4, category=groups, reason=reason)
        await guild.create_voice_channel(name="Group #3", user_limit=5, category=groups, reason=reason)
        priv = await guild.create_category_channel(name="Private Chats", reason=reason)
        await priv.set_permissions(target=muted, reason=reason, send_messages=False, add_reactions=False, speak=False, mute_members=False, use_voice_activation=True)
        await guild.create_voice_channel(name="Private #1", user_limit=2, category=priv, reason=reason)
        await guild.create_voice_channel(name="Private #2", user_limit=2, category=priv, reason=reason)
        await guild.create_voice_channel(name="Private #3", user_limit=2, category=priv, reason=reason)

        overwrites3 = {
            guild.default_role: discord.PermissionOverwrite(
                send_messages=False, add_reactions=False, speak=False, mute_members=False, move_members=False, use_voice_activation=True)
        }
        afkcat = await guild.create_category_channel(name="AFK", overwrites=overwrites3, reason=reason)
        afk = await guild.create_voice_channel(name="AFK", category=afkcat, reason=reason)

        await guild.edit(reason=reason, afk_channel=afk, afk_timeout=900, system_channel=newbies)
        await ctx.send(utils.CustomEmojis.GreenCheck + " **The server has been successfully configured!**")

    @commands.command()
    @utils.has_guild_permissions(manage_guild=True)
    @utils.set_cooldown()
    async def logs(self, ctx, *, channel=None):
        if channel:
            try:
                channel = await commands.TextChannelConverter().convert(ctx, channel.replace(" ", "-"))
            except:
                raise utils.ConverterNotFoundError("Text Channel")

        result = await self.bot.fetchval("SELECT channel_id FROM logs WHERE server_id = $1", ctx.guild.id)

        if result is None:
            if not channel:
                await ctx.send(":point_right: **Logs channel has not been activated on this server!**\nIf you want to activate it, please run the command again by specifing a logs channel.")
                return
            await self.bot.execute("INSERT INTO logs(server_id, channel_id) VALUES($1,$2)", ctx.guild.id, channel.id)
            
            if channel.id == ctx.channel.id:
                await ctx.send(utils.CustomEmojis.GreenCheck + " **Logs has been successfully activated on this server!**\nThis channel is the log channel!")
                return
            await ctx.send(utils.CustomEmojis.GreenCheck + " **Logs has been activated on this server!**\nLogs channel: {}".format(channel.mention))
            return

        logschannels = self.bot.get_channel(result[0])
        if logschannels is None:
            if not channel:
                await self.bot.execute("DELETE FROM logs WHERE server_id = $1", ctx.guild.id)
                await ctx.send(":point_right: **Logs channel has not been activated on this server!**\nIf you want to activate it, please run the command again by specifing a logs channel.")
                return
            
            await self.bot.execute("UPDATE logs SET channel_id = $1 WHERE server_id = $2", channel.id, ctx.guild.id)
            if channel.id == ctx.channel.id:
                await ctx.send(utils.CustomEmojis.GreenCheck + " **Logs has been successfully activated on this server!**\nThis channel is the log channel!")
                return
            await ctx.send(utils.CustomEmojis.GreenCheck + " **Logs has been activated on this server!**\nLogs channel: {}".format(channel.mention))
            return

        if not channel:
            if result[0] == ctx.channel.id:
                await ctx.send(":point_right: **Logs has been activated on this channel!**")
                return
            await ctx.send(":point_right: **Logs has been activated in **{}**!**".format(logschannels.mention))
            return

        if channel.id == ctx.channel.id:
            await ctx.send(":point_right: **Logs has already been activated on this channel!**")
            return

        await self.bot.execute("UPDATE logs SET channel_id = $1 WHERE server_id = $2", channel.id, ctx.guild.id)
        await ctx.send(utils.CustomEmojis.GreenCheck + " **The logs channel has successfully been replaced with: **{}".format(channel.mention))

    @commands.command(aliases=["activate", "activatepremium", "premiumactivate"])
    @commands.has_guild_permissions(manage_guild=True)
    @utils.set_cooldown(per=30.0, alter_per=30.0)
    async def upgrade(self, ctx, code: str = None):
        data = await self.bot.fetchval("SELECT server_id FROM premiumservers WHERE server_id = $1", ctx.guild.id)
        if data is not None:
            raise utils.SpecialError(":point_right: **This server is already a premium server!**\n:blush: Thank you for your support!")

        if ctx.author.id in self.bot.developers:
            await self.bot.execute("INSERT INTO premiumservers(server_id, donator_id) VALUES($1,$2)", ctx.guild.id, ctx.author.id)
            
            await ctx.send("{} **This server is now a premium guild!**".format(utils.CustomEmojis.GreenCheck))
            return
        
        if code is None:
            raise utils.SpecialError(":point_right: **Error: no input code!**")

        res = await self.bot.fetchrow("SELECT * FROM premiumcodes WHERE code = $1", code)
        if res is None:
            raise utils.SpecialError("{} **Premium access denied: code has not be found!**\nIf this is unusual, please contact a bot developer.**".format(utils.CustomEmojis.RedCross))
        if not res.get("allowed"): # Number of codes allowed
            await self.bot.execute("DELETE FROM premiumcodes WHERE code = $1", code)
            raise utils.SpecialError("{} **Premium access denied: code has not be found!**\nIf this is unusual, please contact a bot developer.**".format(utils.CustomEmojis.RedCross))

        await self.bot.execute("INSERT INTO premiumservers(server_id, donator_id) VALUES($1,$2)", ctx.guild.id, res.get("creator"))
        

        num = res.get("allowed") - 1
        if num:
            await self.bot.execute("UPDATE premiumcodes SET allowed = $1 WHERE code = $2", num, code)
            
        else:
            await self.bot.execute("DELETE FROM premiumcodes WHERE code = $1", code)
            
        
        await ctx.send("{} **This server is now a premium guild!**\n:blush: Thank you for your support!".format(utils.CustomEmojis.GreenCheck))



def setup(bot):
    bot.add_cog(Admin(bot))