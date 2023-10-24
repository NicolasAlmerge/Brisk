#!/usr/bin/env python3


import discord
from discord.ext import commands
from discord_slash import cog_ext, SlashContext
import asyncio
from discord_slash.model import ButtonStyle
from discord_slash.utils.manage_commands import create_option
from discord_slash.utils.manage_components import create_actionrow, create_button, wait_for_component
import random
from io import BytesIO
from os import linesep
import string
from datetime import datetime
from urllib.parse import urlencode
from fpdf import FPDF
from PIL import Image

from . import utils
from .utils import Options

# r"0*([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])" - number in range(0, 256)


async def eval_operation(ctx, bot, parser, operation, loop):
    try:
        result = parser.evaluate(operation)
        if parser.var_assignment and loop:
            return
    except ZeroDivisionError:
        await ctx.send(":red_circle: **An error occured!**\n*You've just destroyed math by dividing by zero!*")
        result = await bot.fetchval("SELECT mathdestroy FROM users WHERE id = $1", ctx.author.id)
        if result is None:
            await bot.addline(ctx.author.id, mathdestroy=True)
            await bot.trigger_achievement(ctx, "Math Destroyer")
            return
        if result:
            return
        await bot.execute("UPDATE users SET mathdestroy = true WHERE id = $1", ctx.author.id)
        await bot.trigger_achievement(ctx, "Math Destroyer")
        return
    except SyntaxError:
        await ctx.send(":red_circle: **An error occured!**\n*The syntax you used is invalid.*")
        return
    except TypeError:
        await ctx.send(":red_circle: **An error occured!**\n*The format you used is invalid.*")
        return
    except ValueError as e:
        await ctx.send(f":red_circle: **An error occured!**\n*{e}.*")
        return
    except OverflowError:
        await ctx.send(":red_circle: **An error occured!**\n*The result has too many digits to be represented.*")
        return
    except NameError as e:
        if parser.var_assignment and loop:
            return
        await ctx.send(f":red_circle: **An error occured!**\n*{e}.*")
        return
    except utils.TooManyVariablesException as e:
        await ctx.send(f":red_circle: **An error occured!**\n*{e}.*")
        return
    except utils.SilentException as e:
        if e.msg:
            await ctx.send("```{}```".format(e.msg))
            return
        if loop:
            return
        
        await ctx.send("{} **Command successfully executed!**".format(utils.CustomEmojis.GreenCheck))
        return
    except:
        await ctx.send(":red_circle: **An error occured!**\n*I could not calculate this expression! If this is unexpected, please report it on the bot support server (use the `invites` command to get the link).*")
        return

    # Displaying
    await ctx.send(":1234: Your expression evaluated to **{}**.".format(utils.number_format(result) if isinstance(result, (int, float)) and not isinstance(result, bool) else str(result)))


math_desc = """Calculates an expression, aliases are `math` and `solve`.\n
            Calculations:
            `x + y` - adds `x` and `y`
            `x - y` - substracts `x` by `y`
            `x × y` / `x * y` - multiplies `x` and `y`
            `x / y` / `x ÷ y` / `x : y` - divides `x` by `y`
            `x ^ y` / `x ×× y` - raises `x` to the power `y` (`xʸ`)
            `x // y` - gets the quotient of the euclidean division of `x` by `y` (same as `floor(x / y)`)
            `x mod y` - gets the remainder of the euclidean division of `x` by `y`
            `abs(x)` - gets the absolute value of `x` (equal to `x` if `x` is positive, `-x` otherwise)
            `sqrt(x)` - takes the square root of `x`
            `round(x[, ndigits])` - rounds `x` to `ndigits` decimals, or to an integer if not specified
            `floor(x)` - rounds to the biggest integer `a`, such as `a` ⩽ `x`
            `ceil(x)` / `ceiling(x)` - rounds to the smallest integer `a`, such as `a` ⩾ `x`
            `trunc(x)` / `truncate(x)` - truncates `x` (equal to `floor(x)` if `x` is positive, `ceil(x)` otherwise)
            `fact(x)` / `factorial(x)` - gets the factorial of `x` (equal to `x` × (`x`-1) × (`x`-2) × (`x`-3)... until 1, if `x` is a positive integer)
            `gamma(x)` / `Γ(x)` / `γ(x)` - computes Γ(`x`), equivalent to `fact(x-1)`
            `lgamma(x)` / `lngamma(x)` - computes the natural logarithm of `Γ(x)`
            `log(x[, base])` - gets the logarithm of `x` in the given base, or base 10 if not specified
            `log2(x)` - gets the logarithm of `x` in base 2, can be more precise than `log(x, 2)`
            `log10(x)` - gets the logarithm of `x` in base 10, can be more precise than `log(x, 10)`
            `log1p(x)` - equivalent to `log(x+1)`, accurate for `x` close to 0
            `exp(x)` - equivalent to `eˣ`
            `expm1(x)` - equivalent to `(eˣ)-1`, accurate for small `x`
            `frexp(x)` - calculates (`M`, `N`) such as `x` = `M × 2ᴺ` (if `x` is 0, `M` and `N` are both 0, else 0.5 ⩽ `abs(m)` < 1)
            `ldexp(x, y)` - equivalent to `x × 2ʸ`
            `cos(x)` - computes the cosine of `x` (radians)
            `sin(x)` - computes the sine of `x` (radians)
            `tan(x)` - computes the tangent of `x` (radians)\n
            Checks:
            `x = y` - checks if `x` is equal to `y`
            `x != y` - checks if `x` different to `y`
            `x <= y` - checks if `x` is inferior or equal to `y`
            `x >= y` - checks if `x` is superior or equal to `y`
            `x < y` - checks if `x` is strictly inferior to `y`
            `x > y` - checks if `x` is strictly superior to `y`\n
            Special numbers:
            `pi` - π (≈ 3.14)
            `tau` - τ, equal to 2π (≈ 6.28)
            `e` - e (≈ 2.78)
            `phi` - ϕ, equal to (1+`sqrt(5)`)/2 (≈ 1.62)"""


UDHR = (
    "All human beings are born free and equal in dignity and rights. They are endowed with reason and conscience and should act towards one another in a spirit of brotherhood.", "Everyone is entitled to all the rights and freedoms set forth in this Declaration, without distinction of any kind, such as race, colour, sex, language, religion, political or other opinion, national or social origin, property, birth or other status. Furthermore, no distinction shall be made on the basis of the political, jurisdictional or international status of the country or territory to which a person belongs, whether it be independent, trust, non-self-governing or under any other limitation of sovereignty.",
    "Everyone has the right to life, liberty and security of person.",
    "No one shall be held in slavery or servitude; slavery and the slave trade shall be prohibited in all their forms.",
    "No one shall be subjected to torture or to cruel, inhuman or degrading treatment or punishment.",
    "Everyone has the right to recognition everywhere as a person before the law.",
    "All are equal before the law and are entitled without any discrimination to equal protection of the law. All are entitled to equal protection against any discrimination in violation of this Declaration and against any incitement to such discrimination.", "Everyone has the right to an effective remedy by the competent national tribunals for acts violating the fundamental rights granted him by the constitution or by law.",
    "No one shall be subjected to arbitrary arrest, detention or exile.", "Everyone is entitled in full equality to a fair and public hearing by an independent and impartial tribunal, in the determination of his rights and obligations and of any criminal charge against him.",
    "(1) Everyone charged with a penal offence has the right to be presumed innocent until proved guilty according to law in a public trial at which he has had all the guarantees necessary for his defence.\n(2) No one shall be held guilty of any penal offence on account of any act or omission which did not constitute a penal offence, under national or international law, at the time when it was committed. Nor shall a heavier penalty be imposed than the one that was applicable at the time the penal offence was committed.",
    "No one shall be subjected to arbitrary interference with his privacy, family, home or correspondence, nor to attacks upon his honour and reputation. Everyone has the right to the protection of the law against such interference or attacks.",
    "(1) Everyone has the right to freedom of movement and residence within the borders of each state.\n(2) Everyone has the right to leave any country, including his own, and to return to his country.",
    "(1) Everyone has the right to seek and to enjoy in other countries asylum from persecution.\n(2) This right may not be invoked in the case of prosecutions genuinely arising from non-political crimes or from acts contrary to the purposes and principles of the United Nations.",
    "(1) Everyone has the right to a nationality.(2) No one shall be arbitrarily deprived of his nationality nor denied the right to change his nationality.",
    "(1) Men and women of full age, without any limitation due to race, nationality or religion, have the right to marry and to found a family. They are entitled to equal rights as to marriage, during marriage and at its dissolution.\n(2) Marriage shall be entered into only with the free and full consent of the intending spouses.\n(3) The family is the natural and fundamental group unit of society and is entitled to protection by society and the State.",
    "(1) Everyone has the right to own property alone as well as in association with others.\n(2) No one shall be arbitrarily deprived of his property.",
    "Everyone has the right to freedom of thought, conscience and religion; this right includes freedom to change his religion or belief, and freedom, either alone or in community with others and in public or private, to manifest his religion or belief in teaching, practice, worship and observance.",
    "Everyone has the right to freedom of opinion and expression; this right includes freedom to hold opinions without interference and to seek, receive and impart information and ideas through any media and regardless of frontiers.",
    "(1) Everyone has the right to freedom of peaceful assembly and association.\n(2) No one may be compelled to belong to an association.",
    "(1) Everyone has the right to take part in the government of his country, directly or through freely chosen representatives.\n(2) Everyone has the right of equal access to public service in his country.\n(3) The will of the people shall be the basis of the authority of government; this will shall be expressed in periodic and genuine elections which shall be by universal and equal suffrage and shall be held by secret vote or by equivalent free voting procedures.",
    "Everyone, as a member of society, has the right to social security and is entitled to realization, through national effort and international co-operation and in accordance with the organization and resources of each State, of the economic, social and cultural rights indispensable for his dignity and the free development of his personality.",
    "(1) Everyone has the right to work, to free choice of employment, to just and favourable conditions of work and to protection against unemployment.\n(2) Everyone, without any discrimination, has the right to equal pay for equal work.\n(3) Everyone who works has the right to just and favourable remuneration ensuring for himself and his family an existence worthy of human dignity, and supplemented, if necessary, by other means of social protection.\n(4) Everyone has the right to form and to join trade unions for the protection of his interests.",
    "Everyone has the right to rest and leisure, including reasonable limitation of working hours and periodic holidays with pay.",
    "(1) Everyone has the right to a standard of living adequate for the health and well-being of himself and of his family, including food, clothing, housing and medical care and necessary social services, and the right to security in the event of unemployment, sickness, disability, widowhood, old age or other lack of livelihood in circumstances beyond his control.\n(2) Motherhood and childhood are entitled to special care and assistance. All children, whether born in or out of wedlock, shall enjoy the same social protection.",
    "(1) Everyone has the right to education. Education shall be free, at least in the elementary and fundamental stages. Elementary education shall be compulsory. Technical and professional education shall be made generally available and higher education shall be equally accessible to all on the basis of merit.\n(2) Education shall be directed to the full development of the human personality and to the strengthening of respect for human rights and fundamental freedoms. It shall promote understanding, tolerance and friendship among all nations, racial or religious groups, and shall further the activities of the United Nations for the maintenance of peace.\n(3) Parents have a prior right to choose the kind of education that shall be given to their children.",
    "(1) Everyone has the right freely to participate in the cultural life of the community, to enjoy the arts and to share in scientific advancement and its benefits.\n(2) Everyone has the right to the protection of the moral and material interests resulting from any scientific, literary or artistic production of which he is the author.",
    "Everyone is entitled to a social and international order in which the rights and freedoms set forth in this Declaration can be fully realized.",
    "(1) Everyone has duties to the community in which alone the free and full development of his personality is possible.\n(2) In the exercise of his rights and freedoms, everyone shall be subject only to such limitations as are determined by law solely for the purpose of securing due recognition and respect for the rights and freedoms of others and of meeting the just requirements of morality, public order and the general welfare in a democratic society.\n(3) These rights and freedoms may in no case be exercised contrary to the purposes and principles of the United Nations.",
    "Nothing in this Declaration may be interpreted as implying for any State, group or person any right to engage in any activity or to perform any act aimed at the destruction of any of the rights and freedoms set forth herein."
)


class Misc(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.symbols = string.ascii_letters+string.digits+string.punctuation


    @cog_ext.cog_slash(name="ping", description="Check bot latency.")
    async def ping(self, ctx: SlashContext):
        await ctx.send(embed = discord.Embed(title=":ping_pong: Pong!", description=f"Latency: **{int(self.bot.latency*1000):,} ms**", colour=utils.random_colour()))

    @cog_ext.cog_slash(
        name="isbotdev",
        description="Check if user is a bot developer.",
        options=[
            create_option(
                name="user",
                description="User to check.",
                required=False,
                option_type=Options.USER
            )
        ]
    )
    async def isbotdev(self, ctx: SlashContext, user: discord.Member = None):
        if user is None: user = ctx.author
        if user.id == self.bot.user.id:
            await ctx.send(":point_right: **I cannot be a developer myself!**")
            return
        if user.bot:
            await ctx.send(":point_right: **{} is not a bot developer, as it is a bot user!**".format(str(user)))
            return
        if user.id in self.bot.developers:
            title = "{} is a bot developer!".format(str(user))
            embed = discord.Embed(colour=0x00ff00).set_author(name=title, icon_url=user.avatar_url)
            await ctx.send(embed=embed)
            return
        title = "{} is not a bot developer!".format(str(user))
        embed = discord.Embed(colour=0xff0000).set_author(name=title, icon_url=user.avatar_url)
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(name="uptime", description="Get bot uptime.")
    async def uptime(self, ctx: SlashContext):
        up_time = self.bot.get_uptime()
        if up_time:
            await ctx.send(":desktop: The bot has been up for **{}**.".format(up_time))
            return
        await ctx.send(":point_right: **The bot has just been switched on!**")

    @cog_ext.cog_slash(
        name="avatar",
        description="Get a user's avatar.",
        options=[
            create_option(
                name="user",
                description="User to get the avatar from.",
                required=False,
                option_type=Options.USER
            )
        ]
    )
    async def profilepicture(self, ctx: SlashContext, user: discord.Member = None):
        if user is None: user = ctx.author
        colour = await utils.get_average_colour(user.avatar_url)
        embed = discord.Embed(title=str(user), color=colour)
        #embed.set_author(name=str(user), icon_url=user.avatar_url)
        embed.set_image(url=user.avatar_url_as(size=256))
        #utils.set_footer(ctx, embed, user)
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(
        name="password",
        description="Generate password of a chosen length.",
        options=[
            create_option(
                name="length",
                description="Length of the password to generate, between 1 and 50.",
                required=True,
                option_type=Options.INTEGER
            )
        ]
    )
    async def password(self, ctx: SlashContext, length: int):
        if length <= 0:
            await ctx.send(":point_right: **Error: password must have a strictly positive length!**")
            raise utils.SilentError
        if length > 50:
            await ctx.send(":point_right: **Error: password length cannot be greater than 30.**")
            raise utils.SilentError
        srandom = random.SystemRandom()
        password = "".join(srandom.choice(self.symbols) for _ in range(length))
        embed = discord.Embed(title="Password Generator", description=password, colour=utils.random_colour())
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(
        name="userinfo",
        description="Get a user's information.",
        options=[
            create_option(
                name="user",
                description="User to get the information from.",
                required=False,
                option_type=Options.USER
            )
        ]
    )
    async def userinfo(self, ctx: SlashContext, user: discord.Member = None):
        if user is None: user = ctx.author
        colour = await utils.get_average_colour(user.avatar_url)
        acknolegments = []
        secret_link = False
        
        if user == ctx.guild.owner:
            acknolegments.append("Server Owner")
        
        if user.bot:
            title = utils.EmojiLinks.BotLogo
        elif user.id in self.bot.developers:
            title = utils.EmojiLinks.BotDeveloper
            secret_link = True
            acknolegments.append("Bot Developer")
        elif user.id in self.bot.trusteds:
            title = utils.EmojiLinks.TrustedUser
            acknolegments.append("Trusted User")
        else:
            title = utils.EmojiLinks.DefaultUserLogo
        embed = discord.Embed(color=colour)
        if secret_link:
            embed.set_author(name=str(user), url=utils.Links.SecretLink, icon_url=title)
        else:
            embed.set_author(name=str(user), icon_url=title)
        embed.set_thumbnail(url=user.avatar_url)
        utils.set_footer(ctx, embed, user)
        embed.add_field(name="ID", value=user.id, inline=True)

        us = str(user.status).capitalize()
        if us == "Dnd":
            us = "Do Not Disturb"
        embed.add_field(name="Status", value=us, inline=True)

        embed.add_field(name="Account Type", value="Bot" if user.bot else "Human", inline=False)

        pos = utils.return_guild_join_position(user, ctx.guild)
        embed.add_field(name="Join Position", value=f"{utils.number_format(pos[0])}/{utils.number_format(pos[1])}" if pos else "Unknown", inline=True)

        if user.nick:
            embed.add_field(name="Server Nickname", value=user.nick, inline=False)

        embed.add_field(name="Account Created", value=utils.datetime_format(user.created_at), inline=False)

        try:
            embed.add_field(name="Server Join Date", value=utils.datetime_format(user.joined_at), inline=False)
        except:
            embed.add_field(name="Server Join Date", value="Unknown", inline=False)
        
        roleslist = [role.mention for role in user.roles][1:] # Suppress @everyone role
        try:
            if len(roleslist) == 1:
                embed.add_field(name="Role", value="{}".format(roleslist[0]), inline=False)
            elif len(roleslist) > 1:
                roleslist.reverse()
                embed.add_field(name="Roles ({})".format(len(roleslist)), value="{}".format(", ".join(roleslist)), inline=False)
        except:
            embed.add_field(name="Roles", value=str(len(roleslist)), inline=False)
        
        if user.guild_permissions.administrator:
            embed.add_field(name="Key Permission", value="Administrator", inline=False)
        else:
            perms = [name for (name, perm) in utils.key_permissions(user) if perm]
            if len(perms) == 1:
                embed.add_field(name="Key Permission", value=perms[0], inline=False)
            elif len(perms) > 1:
                embed.add_field(name="Key Permissions ({})".format(len(perms)), value=", ".join(perms), inline=False)
        
        if len(acknolegments) == 1:
            embed.add_field(name="Acknowledgement", value="{}".format(acknolegments[0]), inline=False)
        elif len(acknolegments) == 2:
            embed.add_field(name="Acknowledgements (2)", value="{}".format(", ".join(acknolegments)), inline=False)
        
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(name="serverinfo", description="Get server information.")
    async def serverinfo(self, ctx):
        guild = ctx.guild
        colour = await utils.get_average_colour(guild.icon_url)
        embed = discord.Embed(color=colour)
        embed.set_author(name=guild.name, icon_url=guild.icon_url)
        embed.set_thumbnail(url=guild.icon_url)
        utils.set_footer(ctx, embed)
        embed.add_field(name="ID", value=guild.id)

        try: embed.add_field(name="Owner", value=guild.owner)
        except: embed.add_field(name="Owner", value="Unknown")

        shard = guild.shard_id
        if shard is not None:
            embed.add_field(name="Shard", value=shard)

        members = guild.members
        embed.add_field(name="Members", value=len(members))

        humans = len(tuple(member for member in members if not member.bot))
        bots = len(tuple(member for member in members if member.bot))
        embed.add_field(name="Humans", value=humans)
        embed.add_field(name="Bots", value=bots)

        cats = len(guild.categories)
        if cats:
            embed.add_field(name="Categories", value=cats)

        embed.add_field(name="Text Channels", value=len(guild.text_channels))

        vcs = len(guild.voice_channels)
        if vcs:
            embed.add_field(name="Voice Channels", value=vcs)

        afkchannel = guild.afk_channel
        if afkchannel:
            embed.add_field(name="AFK Channel", value=afkchannel.name)
            afktimeout = guild.afk_timeout
            hours, remainder = divmod(afktimeout, 3600)
            minutes, remainder = divmod(remainder, 60)

            if hours == 1:
                hourtext = "hour"
            else:
                hourtext = "hours"
            if minutes == 1:
                mintext = "minute"
            else:
                mintext = "minutes"

            if hours:
                if minutes:
                    fmt = "{h} {h1} and {m} {m1}".format(h=hours, h1=hourtext, m=minutes, m1=mintext)
                else:
                    fmt = "{h} {h1}".format(h=hours, h1=hourtext)
            else:
                fmt = "{m} {m1}".format(m=minutes, m1=mintext)

            embed.add_field(name="AFK Timeout", value=fmt)

        syschannel = guild.system_channel
        if syschannel:
            embed.add_field(name="New Members Channel", value=syschannel.mention)

        verlvl = str(guild.verification_level).capitalize().replace("_", " ")
        if verlvl == "Extreme":
            embed.add_field(name="Verification Level", value="Very High")
        else:
            embed.add_field(name="Verification Level", value=verlvl)

        explvl = str(guild.explicit_content_filter).capitalize().replace("_", " ").replace("CONTENTFILTER.", "")
        if explvl == "No role":
            embed.add_field(name="Explicit Content Filter", value="Members without any roles")
        else:
            embed.add_field(name="Explicit Content Filter", value=explvl)
        
        embed.add_field(name="Roles", value=len(guild.roles), inline=True)

        emojis = len(tuple(emoji for emoji in guild.emojis if not emoji.animated))
        if emojis:
            embed.add_field(name="Emojis", value=emojis, inline=True)
        
        animated_emojis = len(tuple(emoji for emoji in guild.emojis if emoji.animated))
        if animated_emojis:
            embed.add_field(name="Animated Emojis", value=animated_emojis, inline=True)

        embed.add_field(name="Created on", value=utils.datetime_format(guild.created_at), inline=False)

        await ctx.send(embed=embed)

    @cog_ext.cog_slash(name="botinfo", description="Get bot information.")
    async def botinfo(self, ctx):
        fmt = self.bot.get_uptime()
        devnames = []

        owner_name = self.bot.get_user(self.bot.owner_id)
        
        for dev in self.bot.developers:
            dev_name = self.bot.get_user(dev)
            if dev_name is None:
                devnames.append("Unknown")
            else:
                devnames.append(str(dev_name))

        bot_avatar = self.bot.user.avatar_url
        embed = discord.Embed(color=await utils.get_average_colour(bot_avatar))
        embed.set_author(name=str(self.bot.user), icon_url=bot_avatar)
        embed.set_thumbnail(url=bot_avatar)
        utils.set_footer(ctx, embed)
        embed.add_field(name="ID", value=self.bot.id, inline=True)
        embed.add_field(name="Owner", value="Unknown" if owner_name is None else str(owner_name), inline=True)
        embed.add_field(name="Developers", value=", ".join(devnames), inline=False)
        embed.add_field(name="OS", value=utils.get_system(), inline=True)
        embed.add_field(name="RAM", value=utils.get_ram(), inline=True)
        embed.add_field(name="Uptime", value=fmt if fmt else "Just started", inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    @utils.set_cooldown(per=10.0, alter_per=5.0)
    async def tinyurl(self, ctx, url=None):
        if not url:
            await ctx.send(":point_right: **Error: no url input!**")
            return

        if not utils.validate_url(url):
            await ctx.send(":point_right: **Error: url not in valid format!**")
            return

        embed = discord.Embed(colour=0x06c258, title="URL Shortener")
        if len(url) <= 1000:
            embed.add_field(name="Original URL", value=url, inline=False)

        try:
            request_url = "http://tinyurl.com/api-create.php?" + urlencode({"url": url})
            resp = await utils.urlrequest(request_url)
            embed.add_field(name="Shortened URL", value=resp.decode("utf-8"), inline=False)
            await ctx.send(embed=embed)
        except:
            await ctx.send(":thumbsdown: **Accessing tinyurl failed!**")

    @cog_ext.cog_slash(
        name="colour",
        description="Get colour information.",
        options=[
            create_option(
                name="colour",
                description="Colour to get information from (can be haxadecimal, RGB or a name), or random if not specified.",
                required=False,
                option_type=Options.STRING
            )
        ]
    )
    async def colour(self, ctx: SlashContext, colour: str = "random"):
        # Random colour
        if colour.lower() == "random":
            int_colour = utils.random_colour()
            hexcode = "{0:0{1}X}".format(int_colour, 6)
            rgb = utils.hex_to_rgb(hexcode)

        else:
            rgb_match = utils.RGB_TUPLE.fullmatch(colour)

            # 6 digits hex code match
            if utils.LONG_HEX_COLOR.fullmatch(colour):
                hexcode = colour.upper().lstrip("#")
                rgb = utils.hex_to_rgb(hexcode)

            # 3 digits hex code match
            elif utils.SHORT_HEX_COLOR.fullmatch(colour):
                hexcode = "".join(char*2 for char in colour.upper().lstrip("#"))
                rgb = utils.hex_to_rgb(hexcode)

            # RGB format match
            elif rgb_match:
                try:
                    rgb = tuple(int(x) for x in rgb_match.groups()) # Convert strings to numbers
                    if not all(0 <= x <= 255 for x in rgb): # Numbers must be betwwen 0 and 255
                        raise ValueError

                except: # If RGB tuple was not valid
                    await ctx.send(":point_right: **Error: RGB format must include numbers between 0 and 255.**")
                    return

                hexcode = "".join("{0:0{1}X}".format(comp, 2) for comp in rgb)

            # Colour name
            else:
                hexcode = utils.NAMES_TO_HEX.get(colour.lower().replace(" ", ""), "").lstrip("#") # Get colour hex from name, if possible
                if not hexcode: # If not found, stop here
                    await ctx.send(":point_right: **Error: colour could not be found!**")
                    return
                rgb = utils.hex_to_rgb(hexcode)

            int_colour = int(hexcode, 16)

        # Create new virtual colour image
        img = Image.new("RGB", (200, 200), rgb)
        temp = BytesIO()
        img.save(temp, format="png")
        temp.seek(0)

        # Set up embed
        embed = discord.Embed(title=utils.get_colour_name(rgb).title(), colour=int_colour)
        embed.add_field(name="Hex", value="#"+hexcode)
        embed.add_field(name="RGB", value=str(rgb))
        embed.set_thumbnail(url="attachment://colour.png")

        # Send embed
        await ctx.send(embed=embed, file=discord.File(fp=temp, filename="colour.png"))

    @commands.command(aliases=["requestinfos", "storedinfos", "mydata", "requestdata", "storeddata"])
    @utils.set_cooldown(per=3600, alter_per=2400)
    async def myinfos(self, ctx):
        result = await self.bot.fetchrow("SELECT * FROM users WHERE id = $1", ctx.author.id)
        if result is None:
            await ctx.send(":point_right: **No informations has been stored on you!**")
            return
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", "B", 20)
            pdf.cell(0, 10, "Informations stored on user with id: {}".format(ctx.author.id), align="C")
            pdf.set_font("", "", 14)
            pdf.write(10,
                linesep*2 +
                linesep.join(
                    ["- {}: {}".format(elem, score if isinstance(score, bool) else utils.number_format(score))
                    for elem, score in zip(self.bot.dbuserinfos[1:], list(result.values())[1:])]
                ) + linesep*2 +
                "Data request: {}".format(utils.datetime_format(ctx.message.created_at))
            )
            await ctx.author.send(
                content=":point_right: **Here are your informations!**",
                file=discord.File(
                    fp=BytesIO(pdf.output()),
                    filename="informations.pdf")
                )
        except discord.Forbidden:
            await ctx.send(":point_right: **I do not have permission to message you privately!**")
            return
        if ctx.guild:
            await ctx.send(utils.CustomEmojis.GreenCheck + " **Successfully sent your informations in DM!**")

    @commands.command(aliases=["deleteinfos", "deletedata", "deletemydata", "deletemyinfos", "myinfosdelete", "datadelete", "mydatadelete"])
    @commands.guild_only()
    @commands.bot_has_permissions(add_reactions=True)
    @utils.set_cooldown(per=3600, alter_per=2400)
    async def infosdelete(self, ctx):
        embed = discord.Embed(
            title="Confirm Data Deletion",
            description="Are you sure you want to delete all your stored informations?\n**This action is irreversible!**",
            colour=utils.EmbedColours.ConfirmEmbed
        )
        
        await utils.ask_confirmation(ctx=ctx, bot=self.bot, embed=embed)
        
        users_table = await self.bot.fetchrow("SELECT * FROM users WHERE id = $1", ctx.author.id)
        privacy_table = await self.bot.fetchrow("SELECT * FROM privacysettings WHERE user_id = $1", ctx.author.id)
        if users_table is None and privacy_table is None:
            await ctx.send(":point_right: **No informations has been stored on you!**")
            return
        if users_table is not None:
            await self.bot.execute("DELETE FROM users WHERE id = $1", ctx.author.id)
        if privacy_table is not None:
            await self.bot.execute("DELETE FROM privacysettings WHERE user_id = $1", ctx.author.id)
        
        await ctx.send(utils.CustomEmojis.GreenCheck + " **Successfully cleared all your informations in the database.**")
        raise utils.SilentError

    @cog_ext.cog_slash(name="links", description="Get useful bot links.")
    async def invite(self, ctx: SlashContext):
        embed = discord.Embed(colour=utils.random_colour())
        embed.set_author(name="Useful links", icon_url=self.bot.user.avatar_url)
        embed.set_thumbnail(url=self.bot.user.avatar_url)
        utils.set_footer(ctx, embed)
        embed.add_field(name="Add bot", value="[Click here]({})".format(utils.Links.Invite), inline=True)
        embed.add_field(name="Join Support Server", value="[Click here]({})".format(utils.Links.Server), inline=True)
        embed.add_field(name="See some bot code", value="[Click here]({})".format(utils.Links.GitHub), inline=False)
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(
        name="math",
        description="Calculates a mathematical operation.",
        options=[
            create_option(
                name="operation",
                description="Operation to evaluate.",
                required=True,
                option_type=Options.STRING
            )
        ]
    )
    async def calculate(self, ctx: SlashContext, operation: str):
        # Parsing
        is_session = (operation.lower() == "session")
        parser = utils.BriskParser(10 if is_session else 0)
        
        if not is_session:
            if operation in ("EXIT", "QUIT"):
                await ctx.send(":point_right: **Error: cannot close session that has not started!**")
                return
            
            await eval_operation(ctx, self.bot, parser, operation, loop=False)
            return
        
        await ctx.send(":point_right: **New session has been launched!**\n*Enter your expressions directly as a message. To close the session, simply type `EXIT` or `QUIT`.*")
        
        while True:
            try:
                operation = await self.bot.wait_for("message", timeout=60, check=utils.check_msg(ctx))
                operation = operation.content
            except asyncio.TimeoutError:
                await ctx.send(":point_right: **The math session menu has been ended due to inactivity!**")
                return
            
            if operation in ("EXIT", "QUIT"):
                await ctx.send("{} **Session has been closed!**".format(utils.CustomEmojis.GreenCheck))
                return
            
            await eval_operation(ctx, self.bot, parser, operation, loop=True)
    

    @staticmethod
    def __create_main_buttons(input_str: str, result):
        return [
            create_actionrow(
                create_button(label="F1", custom_id="F1", style=ButtonStyle.green),
                create_button(label="(", custom_id="(", style=ButtonStyle.gray, disabled=(len(input_str) >= 104)),
                create_button(label=")", custom_id=")", style=ButtonStyle.gray, disabled=(len(input_str) >= 104)),
                create_button(label="^", custom_id="^", style=ButtonStyle.blue, disabled=(len(input_str) >= 104)),
                create_button(emoji="🛑", custom_id="STOP", style=ButtonStyle.red)
            ),
            create_actionrow(
                create_button(label="7", custom_id="7", style=ButtonStyle.gray, disabled=(len(input_str) >= 104)),
                create_button(label="8", custom_id="8", style=ButtonStyle.gray, disabled=(len(input_str) >= 104)),
                create_button(label="9", custom_id="9", style=ButtonStyle.gray, disabled=(len(input_str) >= 104)),
                create_button(label="÷", custom_id="/", style=ButtonStyle.blue, disabled=(len(input_str) >= 104)),
                create_button(label="AC", custom_id="AC", style=ButtonStyle.red, disabled=(input_str == "" and result is None))
            ),
            create_actionrow(
                create_button(label="4", custom_id="4", style=ButtonStyle.gray, disabled=(len(input_str) >= 104)),
                create_button(label="5", custom_id="5", style=ButtonStyle.gray, disabled=(len(input_str) >= 104)),
                create_button(label="6", custom_id="6", style=ButtonStyle.gray, disabled=(len(input_str) >= 104)),
                create_button(label="×", custom_id="×", style=ButtonStyle.blue, disabled=(len(input_str) >= 104)),
                create_button(label="C", custom_id="C", style=ButtonStyle.red, disabled=(input_str == ""))
            ),
            create_actionrow(
                create_button(label="1", custom_id="1", style=ButtonStyle.gray, disabled=(len(input_str) >= 104)),
                create_button(label="2", custom_id="2", style=ButtonStyle.gray, disabled=(len(input_str) >= 104)),
                create_button(label="3", custom_id="3", style=ButtonStyle.gray, disabled=(len(input_str) >= 104)),
                create_button(label="-", custom_id="-", style=ButtonStyle.blue, disabled=(len(input_str) >= 104)),
                create_button(label="⌫", custom_id="DEL", style=ButtonStyle.red, disabled=(input_str == ""))
            ),
            create_actionrow(
                create_button(label="F2", custom_id="F2", style=ButtonStyle.green),
                create_button(label="0", custom_id="0", style=ButtonStyle.gray, disabled=(len(input_str) >= 104)),
                create_button(label=".", custom_id=".", style=ButtonStyle.gray, disabled=(len(input_str) >= 104)),
                create_button(label="+", custom_id="+", style=ButtonStyle.blue, disabled=(len(input_str) >= 104)),
                create_button(label="=", custom_id="=", style=ButtonStyle.green)
            )
        ]
    
    @staticmethod
    def __create_func_buttons(input_str: str, result):
        return [
            create_actionrow(
                create_button(label="←", custom_id="BACK", style=ButtonStyle.green),
                create_button(label="√", custom_id="√(", style=ButtonStyle.gray, disabled=(len(input_str) > 102)),
                create_button(label="Γ", custom_id="gamma(", style=ButtonStyle.gray, disabled=(len(input_str) > 98)),
                create_button(label=",", custom_id=", ", style=ButtonStyle.blue, disabled=(len(input_str) > 102)),
                create_button(emoji="🛑", custom_id="STOP", style=ButtonStyle.red)
            ),
            create_actionrow(
                create_button(label="exp", custom_id="exp(", style=ButtonStyle.gray, disabled=(len(input_str) > 100)),
                create_button(label="ln", custom_id="ln(", style=ButtonStyle.gray, disabled=(len(input_str) > 101)),
                create_button(label="log", custom_id="log(", style=ButtonStyle.gray, disabled=(len(input_str) > 100)),
                create_button(label="10ˣ", custom_id="×10^", style=ButtonStyle.blue, disabled=(len(input_str) > 100)),
                create_button(label="AC", custom_id="AC", style=ButtonStyle.red, disabled=(input_str == "" and result is None))
            ),
            create_actionrow(
                create_button(label="sin", custom_id="sin(", style=ButtonStyle.gray, disabled=(len(input_str) > 100)),
                create_button(label="cos", custom_id="cos(", style=ButtonStyle.gray, disabled=(len(input_str) > 100)),
                create_button(label="tan", custom_id="tan(", style=ButtonStyle.gray, disabled=(len(input_str) > 100)),
                create_button(label="x!", custom_id="!", style=ButtonStyle.blue, disabled=(len(input_str) > 103)),
                create_button(label="C", custom_id="C", style=ButtonStyle.red, disabled=(input_str == ""))
            ),
            create_actionrow(
                create_button(label="sinh", custom_id="sinh(", style=ButtonStyle.gray, disabled=(len(input_str) > 99)),
                create_button(label="cosh", custom_id="cosh(", style=ButtonStyle.gray, disabled=(len(input_str) > 99)),
                create_button(label="tanh", custom_id="tanh(", style=ButtonStyle.gray, disabled=(len(input_str) > 99)),
                create_button(label="|", custom_id="|", style=ButtonStyle.blue, disabled=(len(input_str) > 103)),
                create_button(label="⌫", custom_id="DEL", style=ButtonStyle.red, disabled=(input_str == ""))
            ),
            create_actionrow(
                create_button(label="F2", custom_id="F2", style=ButtonStyle.green),
                create_button(label="floor", custom_id="floor(", style=ButtonStyle.gray, disabled=(len(input_str) > 98)),
                create_button(label="ceil", custom_id="ceil(", style=ButtonStyle.gray, disabled=(len(input_str) > 99)),
                create_button(label="mod", custom_id=" mod ", style=ButtonStyle.blue, disabled=(len(input_str) > 99)),
                create_button(label="=", custom_id="=", style=ButtonStyle.green)
            )
        ]
    
    @staticmethod
    def __create_vars_buttons(input_str: str, result):
        return [
            create_actionrow(
                create_button(label="←", custom_id="BACK", style=ButtonStyle.green),
                create_button(label="π", custom_id="π", style=ButtonStyle.gray, disabled=(len(input_str) >= 104)),
                create_button(label="τ", custom_id="τ", style=ButtonStyle.gray, disabled=(len(input_str) >= 104)),
                create_button(label="e", custom_id="e", style=ButtonStyle.gray, disabled=(len(input_str) >= 104)),
                create_button(emoji="🛑", custom_id="STOP", style=ButtonStyle.red)
            ),
            create_actionrow(
                create_button(label="φ", custom_id="φ", style=ButtonStyle.gray, disabled=(len(input_str) >= 104)),
                create_button(label="γ", custom_id="γ", style=ButtonStyle.gray, disabled=(len(input_str) >= 104)),
                create_button(label="/", custom_id="_2", style=ButtonStyle.gray, disabled=True),
                create_button(label="/", custom_id="_3", style=ButtonStyle.gray, disabled=True),
                create_button(label="AC", custom_id="AC", style=ButtonStyle.red, disabled=(input_str == "" and result is None))
            ),
            create_actionrow(
                create_button(label="/", custom_id="_4", style=ButtonStyle.gray, disabled=True),
                create_button(label="/", custom_id="_5", style=ButtonStyle.gray, disabled=True),
                create_button(label="/", custom_id="_6", style=ButtonStyle.gray, disabled=True),
                create_button(label="/", custom_id="_7", style=ButtonStyle.gray, disabled=True),
                create_button(label="C", custom_id="C", style=ButtonStyle.red, disabled=(input_str == ""))
            ),
            create_actionrow(
                create_button(label="/", custom_id="_8", style=ButtonStyle.gray, disabled=True),
                create_button(label="/", custom_id="_9", style=ButtonStyle.gray, disabled=True),
                create_button(label="/", custom_id="_10", style=ButtonStyle.gray, disabled=True),
                create_button(label="/", custom_id="_11", style=ButtonStyle.gray, disabled=True),
                create_button(label="⌫", custom_id="DEL", style=ButtonStyle.red, disabled=(input_str == ""))
            ),
            create_actionrow(
                create_button(label="F1", custom_id="F1", style=ButtonStyle.green),
                create_button(label="/", custom_id="_12", style=ButtonStyle.gray, disabled=True),
                create_button(label="/", custom_id="_13", style=ButtonStyle.gray, disabled=True),
                create_button(label="/", custom_id="_14", style=ButtonStyle.gray, disabled=True),
                create_button(label="=", custom_id="=", style=ButtonStyle.green)
            )
        ]
    

    @cog_ext.cog_slash(name="calculator", description="Display an interactive calculator.")
    async def simple_calc(self, ctx: SlashContext):
        result = None
        input_str = ""
        new_result = False
        button_type = 0 # Main
        buttons = Misc.__create_main_buttons(input_str, result)

        output = await ctx.send(content="Loading…")
        await output.edit(content="```yaml\n0```", components=buttons)
        parser = utils.BriskParser(0)
        length_stack = []

        def pop_last_length():
            if length_stack:
                return length_stack.pop()
            return 0

        while True:
            try:
                button_ctx = await wait_for_component(
                    self.bot,
                    components=buttons,
                    messages=output,
                    timeout=30,
                    check=lambda i: i.author == ctx.author
                )
            except asyncio.TimeoutError:
                await output.edit(content=":point_right: **Calculator closed due to inactivity.**", components=[])
                raise utils.SilentError
            
            label = button_ctx.custom_id

            if label == "STOP":
                await output.edit(content=":point_right: **Calculator successfully closed.**", components=[])
                raise utils.SilentError
            
            if new_result and label not in ("+", "-", "×", "/", "^", "=", "F1", "F2", "BACK"): input_str = ""
            
            new_result = False

            if label == "=":
                length_stack.clear()
                new_result = True
                try:
                    result = parser.evaluate(input_str if input_str else "0")
                except:
                    input_str = "arm\nERROR"
                    length_stack.append(len(input_str))
                else:
                    input_str = str(result)
                    if len(input_str) > 104: input_str = "arm\nERROR"
                    length_stack.append(len(input_str))

            elif label == "F1":
                button_type = 1 # Func
            
            elif label == "F2":
                button_type = 2 # Func2

            elif label == "BACK":
                button_type = 0 # Main

            elif label == "AC":
                length_stack.clear()
                input_str = ""
                result = None
            
            elif label == "C":
                length_stack.clear()
                input_str = ""
            
            elif label == "DEL":
                input_str = input_str[0:len(input_str)-pop_last_length()]
            
            elif len(input_str) + len(label) <= 104:
                input_str += label
                length_stack.append(len(label))
            
            if button_type == 0:
                buttons = Misc.__create_main_buttons(input_str, result)
            elif button_type == 1:
                buttons = Misc.__create_func_buttons(input_str, result)
                button_type = 0
            elif button_type == 2:
                buttons = Misc.__create_vars_buttons(input_str, result)
                button_type = 0
            await button_ctx.edit_origin(content="```{0}```".format(input_str if input_str else "yaml\n0"), components=buttons)

    @commands.command()
    @commands.guild_only()
    @utils.bot_has_guild_permissions(manage_roles=True)
    @utils.set_cooldown()
    async def roleinfo(self, ctx, *, role=None):
        if not role:
            await ctx.send(":point_right: **Error: no role has been input!**")
            return

        try:
            role: discord.Role = await commands.RoleConverter().convert(ctx, role)
        except:
            raise utils.ConverterNotFoundError("Role")

        embed = discord.Embed(title="Role Information", color=role.color)
        embed.add_field(name="Name", value=role.name)
        embed.add_field(name="ID", value=role.id)

        # If role is not @everyone
        if not role.is_default():
            embed.add_field(name="Role Color", value="Default" if role.color == discord.Color(0) else str(role.color).upper(), inline=False)
            embed.add_field(name="Displayed Separately", value="Yes" if role.hoist else "No")
            embed.add_field(name="Mentionable", value="Yes" if role.mentionable else "No", inline=False)
            embed.add_field(name="Managed By Integration", value="Yes" if role.managed else "No")

        # If role has administrator permission
        if role.permissions.administrator:
            embed.add_field(name="Advanced Permissions", value="Administrator", inline=False)
            await ctx.send(embed=embed)
            return

        # General permissions
        general = [name for (name, value) in utils.general_permissions(role) if value]
        if general:
            embed.add_field(name="General Server Permissions", value=", ".join(general), inline=False)

        # Membership permissions
        membership = [name for (name, value) in utils.membership_permissions(role) if value]
        if membership:
            embed.add_field(name="Membership Permissions", value=", ".join(membership))
        
        # Text permissions
        text = [name for (name, value) in utils.text_permissions(role) if value]
        if text:
            embed.add_field(name="Text Channel Permissions", value=", ".join(text), inline=False)

        # Voice permissions
        voice = [name for (name, value) in utils.voice_permissions(role) if value]
        if voice:
            embed.add_field(name="Voice Channel Permissions", value=", ".join(voice))
        
        # Stage permissions
        stage = [name for (name, value) in utils.stage_permissions(role) if value]
        if stage:
            embed.add_field(name="Stage Channel Permissions", value=", ".join(stage))
        
        await ctx.send(embed=embed)

    @commands.command()
    @utils.bot_has_guild_permissions(manage_roles=True)
    @utils.set_cooldown()
    async def serverroles(self, ctx):
        roles = [utils.mentionrole(role) for role in ctx.guild.roles]
        colour = await utils.get_average_colour(ctx.guild.icon_url)
        embed = discord.Embed(color=colour)
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
        embed.set_thumbnail(url=ctx.guild.icon_url)
        utils.set_footer(ctx, embed)
        if len(roles) == 1:
            embed.add_field(name="Role", value="{}".format(*roles), inline=False)
            await ctx.send(embed=embed)
            return
        roles.reverse()
        embed.add_field(name="Roles ({})".format(len(roles)), value="{}".format(", ".join(roles)), inline=False)
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(
        name="say",
        description="Make me repeat what you said.",
        options=[
            create_option(
                name="message",
                description="Message to repeat.",
                required=True,
                option_type=Options.STRING
            )
        ]
    )
    async def say(self, ctx: SlashContext, message: str):
        await ctx.send(message)
    
    @cog_ext.cog_slash(name="embed", description="Make an embed.")
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def _create_embed(self, ctx: SlashContext):

        desc = "Click on the reaction below if you don't want any."
        r_colour = utils.random_colour()
        is_empty = True
        field_num = 0

        author_embed = discord.Embed(title="Which user do you want to include at the top of the embed?", description=desc, colour=r_colour)
        author = await utils.ask_userinput(ctx=ctx, bot=self.bot, embed=author_embed, reaction=utils.CustomEmojis.RedCross)
        if author is not None:
            is_empty = False
            try: author = await commands.MemberConverter().convert(ctx, author)
            except: raise utils.ConverterNotFoundError("Member")

        title_embed = discord.Embed(title="What title do you want for the embed?", description=desc, colour=r_colour)
        title = await utils.ask_userinput(ctx=ctx, bot=self.bot, embed=title_embed, reaction=utils.CustomEmojis.RedCross)
        if title is None: title = discord.Embed.Empty
        else: is_empty = False

        description_embed = discord.Embed(title="What description do you want for the embed?", description=desc, colour=r_colour)
        description = await utils.ask_userinput(ctx=ctx, bot=self.bot, embed=description_embed, reaction=utils.CustomEmojis.RedCross)
        if description is None: description = discord.Embed.Empty
        else: is_empty = False

        colour_embed = discord.Embed(title="What colour do you want for the embed?", description="Click on the reaction below if you want a random one.", colour=r_colour)
        colour_txt = await utils.ask_userinput(ctx=ctx, bot=self.bot, embed=colour_embed, reaction="🎲")
        colour = utils.random_colour() if colour_txt is None else utils.return_colour(colour_txt)

        embed = discord.Embed(title=title, description=description, colour=colour)
        if author is not None:
            embed.set_author(name=str(author), icon_url=author.avatar_url)
        
        thumbnail_embed = discord.Embed(title="What thumbnail (URL) do you want for the embed?", description=desc, colour=r_colour)
        thumbnail = await utils.ask_userinput(ctx=ctx, bot=self.bot, embed=thumbnail_embed, reaction=utils.CustomEmojis.RedCross)
        if thumbnail is not None:
            if not utils.validate_url(thumbnail):
                raise utils.SpecialError(":point_right: **Error: an URL must be specified for the thumbnail!**")
            embed.set_thumbnail(url=thumbnail)
            is_empty = False
        
        for field_num in range(25):
            add_field_embed = discord.Embed(title="Do you want to add {} field?".format("another" if field_num else "a"), description="{}/25 fields used.".format(field_num), colour=r_colour)
            add_field = await utils.ask_userinput(ctx=ctx, bot=self.bot, embed=add_field_embed, use_reactions=True)
            if not add_field:
                break

            is_empty = False
            
            fieldtitle_embed = discord.Embed(title="What name do you want for the field?", description=desc, colour=r_colour)
            fieldtitle = await utils.ask_userinput(ctx=ctx, bot=self.bot, embed=fieldtitle_embed, reaction=utils.CustomEmojis.RedCross)
            if fieldtitle is None: fieldtitle = "\u200b"

            fieldvalue_embed = discord.Embed(title="What value do you want for the field?", description=desc, colour=r_colour)
            fieldvalue = await utils.ask_userinput(ctx=ctx, bot=self.bot, embed=fieldvalue_embed, reaction=utils.CustomEmojis.RedCross)
            if fieldvalue is None: fieldvalue = "\u200b"
            
            if field_num:
                fieldinline_embed = discord.Embed(title="Do you want the field to be on the same line as the previous field?", colour=r_colour)
                fieldinline = await utils.ask_userinput(ctx=ctx, bot=self.bot, embed=fieldinline_embed, use_reactions=True)
            else:
                fieldinline = True

            embed.add_field(name=fieldtitle, value=fieldvalue, inline=fieldinline)
        
        add_footer_embed = discord.Embed(title="Do you want to add a footer with your name?", colour=r_colour)
        add_footer = await utils.ask_userinput(ctx=ctx, bot=self.bot, embed=add_footer_embed, use_reactions=True)

        if add_footer:
            is_empty = False
            embed.set_footer(text="Requested by " + str(ctx.author), icon_url=ctx.author.avatar_url)
        
        timestamp_embed = discord.Embed(title="Do you want to set a timestamp for the embed?", colour=r_colour)
        timestamp = await utils.ask_userinput(ctx=ctx, bot=self.bot, embed=timestamp_embed, use_reactions=True)

        if timestamp:
            # is_empty = False # To comment out if needed
            embed.timestamp = datetime.utcnow()
        
        elif is_empty:
            raise utils.SpecialError(":point_right: **Error: cannot send an empty embed!**")

        await ctx.channel.send(embed=embed, reference=None)
    
    @commands.group(aliases=["privacysettings", "settingsprivacy"], invoke_without_command=True, case_insensitive=True)
    @utils.set_cooldown()
    async def privacy(self, ctx):
        query = await self.bot.fetchrow("SELECT * FROM privacysettings WHERE user_id = $1", ctx.author.id)
        if query is None:
            elems = [("balance", True), ("achievements", True)]
        else:
            elems = list(query.items())[1:]
        
        embed = discord.Embed(
            title="Privacy settings",
            description="You can change them using the `privacy public` or `privacy private` command.",
            colour=utils.random_colour()
        )
        embed.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url)

        for elem, value in elems:
            embed.add_field(name=elem.capitalize(), value=":busts_in_silhouette: **Public**" if value else ":lock: **Private**")
        
        await ctx.send(embed=embed)
    
    @privacy.command(name="public", aliases=["makepublic", "publicmake"])
    @utils.set_cooldown(per=300, alter_per=200)
    async def privacy_public(self, ctx, *options):
        if not options:
            raise utils.SpecialError(":point_right: **Error: no options given.**")

        options = [option.lower() for option in options]
        addups = []

        for option in options:
            if option.lower() in ("balance", "achievements"):
                addups.append(option.lower())
            else:
                raise utils.SpecialError(":point_right: **Error: option {} unknown.**".format(option.lower()))
        
        query = await self.bot.fetchrow("SELECT * FROM privacysettings WHERE user_id = $1", ctx.author.id)
        if query is None:
            allops = {"balance": "true", "achievements": "true"}
        else:
            allops = {key: "true" if value else "false" for key, value in tuple(query.items())[1:]}

        for option in addups:
            allops[option] = "true"
        
        all_public = all(value == "true" for _, value in allops.items())
        final_msg = "{} **Changes have been made!**".format(utils.CustomEmojis.GreenCheck)

        if query is None:
            if all_public:
                await ctx.send(final_msg)
                return
            await self.bot.execute(f"INSERT INTO privacysettings(user_id,balance,achievements) VALUES ($1,{allops['balance']},{allops['achievements']})", ctx.author.id)
            await ctx.send(final_msg)
            return
        
        if all_public:
            await self.bot.execute("DELETE FROM privacysettings WHERE user_id = $1", ctx.author.id)
            await ctx.send(final_msg)
            return
        
        await self.bot.execute(f"UPDATE privacysettings SET balance = {allops['balance']}, achievements = {allops['achievements']} WHERE user_id = $1", ctx.author.id)
        await ctx.send(final_msg)
    
    @privacy.command(name="private", aliases=["makeprivate", "privatemake"])
    @utils.set_cooldown(per=300, alter_per=200)
    async def privacy_private(self, ctx, *options):
        if not options:
            raise utils.SpecialError(":point_right: **Error: no options given.**")

        options = [option.lower() for option in options]
        addups = []

        for option in options:
            if option.lower() in ("balance", "achievements"):
                addups.append(option.lower())
            else:
                raise utils.SpecialError(":point_right: **Error: option {} unknown.**".format(option.lower()))
        
        query = await self.bot.fetchrow("SELECT * FROM privacysettings WHERE user_id = $1", ctx.author.id)
        if query is None:
            allops = {"balance": "true", "achievements": "true"}
        else:
            allops = {key: "true" if value else "false" for key, value in tuple(query.items())[1:]}

        for option in addups:
            allops[option] = "false"
        
        final_msg = "{} **Changes have been made!**".format(utils.CustomEmojis.GreenCheck)

        if query is None:
            await self.bot.execute(f"INSERT INTO privacysettings(user_id,balance,achievements) VALUES ($1,{allops['balance']},{allops['achievements']})", ctx.author.id)
            await ctx.send(final_msg)
            return
        
        await self.bot.execute(f"UPDATE privacysettings SET balance = {allops['balance']}, achievements = {allops['achievements']} WHERE user_id = $1", ctx.author.id)
        await ctx.send(final_msg)


    # @commands.command()
    # @utils.set_cooldown()
    # async def help(self, ctx):
    #     embed = discord.Embed(title="Bot Commands", description="", color=0x0000ff)
    #     embed.add_field(name="Under development", value="This command is under development!", inline=True)
    #     await ctx.send(embed=embed)

    @commands.command()
    @utils.set_cooldown()
    async def suggest(self, ctx, *, suggestion=None):
        if not suggestion:
            try:
                await ctx.send(":point_right: **Please enter your suggestion below!**")
                suggestion = await self.bot.wait_for("message", timeout = 180, check=utils.check_msg(ctx))
            except asyncio.TimeoutError:
                await ctx.send(utils.CustomEmojis.RedCross + " **The suggestion menu has been closed due to inactivity!**")
                return
            suggestion = suggestion.content
        dev_guild = self.bot.get_guild(self.bot.dev_guild)
        if not dev_guild:
            await ctx.send(":point_right: **Error: developer server could not be found!** Please contact a bot developer about it!")
            return
        suggchannel = dev_guild.get_channel(self.bot.suggestions)
        if not suggchannel:
            await ctx.send(":point_right: **Error: suggestion channel could not be found!** Please contact a bot developer about it!")
            return
        try:
            embed = discord.Embed(colour=utils.random_colour())
            embed.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url)
            #embed.set_thumbnail(url=ctx.author.avatar_url)
            embed.add_field(name="User ID", value=ctx.author.id)
            if ctx.guild:
                embed.add_field(name="Server", value=ctx.guild.name, inline=True)
                embed.add_field(name="Server ID", value=ctx.guild.id, inline=True)
                try:
                    embed.add_field(name="Server Owner ID", value=ctx.guild.owner.id, inline=True)
                except:
                    pass
            embed.add_field(name="Suggestion", value=suggestion, inline=False)
            suggmsg = await suggchannel.send(embed=embed)
        except:
            try: await suggmsg.delete()
            finally:
                await ctx.send(":thumbsdown: **Sending suggestion failed!**")
                return
        await ctx.send(utils.CustomEmojis.GreenCheck + " **Suggestion has successfully been sent!** Thank you!")

    @commands.command()
    @utils.set_cooldown()
    async def report(self, ctx, target=None, *, report=None):
        if not target:
            try:
                await ctx.send(":point_right: **Please enter a server, user or bug to report!**")
                target = await self.bot.wait_for("message", timeout = 30, check=utils.check_msg(ctx))
            except asyncio.TimeoutError:
                await ctx.send(utils.CustomEmojis.RedCross + " **The report menu has been closed due to inactivity!**")
                return
            target = target.content
        if not report:
            try:
                await ctx.send(":point_right: **Please enter your report below!**")
                report = await self.bot.wait_for("message", timeout = 180, check=utils.check_msg(ctx))
            except asyncio.TimeoutError:
                await ctx.send(utils.CustomEmojis.RedCross + " **The report menu has been closed due to inactivity!**")
                return
            report = report.content
        dev_guild = self.bot.get_guild(self.bot.dev_guild)
        if not dev_guild:
            await ctx.send(":point_right: **Error: developer server could not be found!** Please contact a bot developer about it!")
            return
        rprtchannel = dev_guild.get_channel(self.bot.reports)
        if not rprtchannel:
            await ctx.send(":point_right: **Error: report channel could not be found!** Please contact a bot developer about it!")
            return
        try:
            embed = discord.Embed(colour=utils.random_colour())
            embed.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url)
            #embed.set_thumbnail(url=ctx.author.avatar_url)
            embed.add_field(name="User ID", value=ctx.author.id)
            if ctx.guild:
                embed.add_field(name="Server", value=ctx.guild.name, inline=True)
                embed.add_field(name="Server ID", value=ctx.guild.id, inline=False)
                try:
                    embed.add_field(name="Server Owner ID", value=ctx.guild.owner.id, inline=True)
                except:
                    pass
            embed.add_field(name="Target", value=target, inline=False)
            embed.add_field(name="Report", value=report, inline=False)
            rprtmsg = await rprtchannel.send(embed=embed)
        except:
            try: await rprtmsg.delete()
            finally:
                await ctx.send(":thumbsdown: **Sending report failed!**")
                return
        await ctx.send(utils.CustomEmojis.GreenCheck + " **Report has successfully been sent!** Thank you!")


def setup(bot):
    bot.add_cog(Misc(bot))