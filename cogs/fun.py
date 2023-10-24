#!/usr/bin/env python3

import discord
from discord.ext import commands
import asyncio
import string
from random import randint, choice
import json
import math
from discord_slash import cog_ext
from discord_slash.context import SlashContext
from discord_slash.utils.manage_commands import create_option
from discord_slash.utils.manage_components import create_button, create_actionrow, wait_for_component
from discord_slash.model import ButtonStyle
import qrcode
from io import BytesIO
from . import utils
from .utils import Options


possibleCharacters = string.ascii_letters + string.digits + string.whitespace + ".,!?;:éèêëàâæôœöûüîï<>@"


red = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
black = [2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35]


class Fun(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @cog_ext.cog_slash(
        name="roll",
        description="Play roulette.",
        options=[
            create_option(
                name="amount",
                description="Amount to bet (at least 50 smilos).",
                required=True,
                option_type=Options.INTEGER
            ),
            create_option(
                name="bet",
                description="Your bet.",
                required=True,
                option_type=Options.STRING
            )
        ]
    )
    async def roulette(self, ctx, amount: int, bet: str):
        bet = bet.lower().strip()
        
        if amount < 50:
            await ctx.send(":point_right: **Error: cannot bet less than 50 smilos.**")
            raise utils.SilentError

        amountstr = utils.number_format(amount)
        try:
            await self.bot.removemoney(ctx.author, amount)
        except ValueError:
            await ctx.send(":point_right: You cannot bet {}**{}**, as you don't have that much in your balance!".format(utils.CustomEmojis.Smilo, amountstr))
            raise utils.SilentError

        roll = randint(0, 36)
        win = False
        multiplier = 2

        if bet in ("black", "red", "green", "odd", "even"):
            message = await ctx.send("{} You bet {}**{}** on **{}**.\n{} **Rolling the wheel...**".format(utils.CustomEmojis.SmiloMoney, utils.CustomEmojis.Smilo, amountstr, bet, utils.CustomEmojis.Roulette))
            if bet == "black" and roll in black:
                win = True
            elif bet == "red" and roll in red:
                win = True
            elif bet == "green" and not roll:
                win = True
                multiplier = 36
            elif bet == "odd" and roll%2:
                win = True
            elif bet == "even" and not roll%2 and roll:
                win = True
        else:
            try:
                bet = int(bet)
                if bet < 0 or bet > 36:
                    raise ValueError
            except ValueError:
                await ctx.send(":point_right: Error: you can only pick **black**, **red**, **green**, **odd**, **even** or an integer between **0** and **36**.")
                return
            message = await ctx.send("{} You bet {}**{}** on **{}**.\n{} **Rolling the wheel...**".format(utils.CustomEmojis.SmiloMoney, utils.CustomEmojis.Smilo, amountstr, bet, utils.CustomEmojis.Roulette))
            if bet == roll:
                win = True
                multiplier = 36

        await asyncio.sleep(3)

        if win:
            if multiplier == 2:
                await message.edit(content=":clap: **Congradulations!** You bet on **{}** and the roll was **{}**.\nYou won {}**{}**.".format(bet, roll, utils.CustomEmojis.Smilo, amountstr))
                await self.bot.addmoney(ctx.author, amount*2)
                return
            
            await message.edit(content=":clap: **Congradulations!** You bet on **{}** and the roll was exactly what you predicted!\nYou won {}**{}**.".format(bet, utils.CustomEmojis.Smilo, utils.number_format(amount*35)))
            await self.bot.addmoney(ctx.author, amount*36)
            if roll:
                return
            
            res = await self.bot.fetchval("SELECT roll FROM users WHERE id = $1", ctx.author.id)
            if res:
                return
            
            if res is None:
                await self.bot.addline(ctx.author.id, roll=True)
            else:
                await self.bot.execute("UPDATE users SET roll = true WHERE id = $1", ctx.author.id)
            
            await self.bot.trigger_achievement(ctx, "Roulette Expert")
            return
        
        await message.edit(content=":thumbsdown: You bet on **{}** and the roll was **{}**.\nYou lost {}**{}**.".format(bet, roll, utils.CustomEmojis.Smilo, amountstr))


    @cog_ext.cog_slash(name="flip", description="Flip a coin.")
    async def flip(self, ctx: SlashContext):
        await ctx.send("{} The coin landed on **{0}**!".format(utils.CustomEmojis.SmiloCoin, "heads" if randint(1, 1000) < 501 else "tails"))

    @cog_ext.cog_slash(
        name="dice",
        description="Roll a dice.",
        options=[
            create_option(
                name="sides",
                description="Number of sides of the dice, between 2 and 120 (default is 6).",
                required=False,
                option_type=Options.INTEGER
            )
        ]
    )
    async def dice(self, ctx: SlashContext, sides: int = 6):
        if sides < 2 or sides > 120:
            await ctx.send(":point_right: **Error: the number of dice faces must be between 2 and 120!**")
            raise utils.SilentError
        await ctx.send(":point_right: The dice landed on **{0}**!".format(randint(1, sides)))

    @cog_ext.cog_slash(
        name="give",
        description="Give money to someone.",
        options=[
            create_option(
                name="user",
                description="User to give money to.",
                required=True,
                option_type=Options.USER
            ),
            create_option(
                name="amount",
                description="Amount of money to give (between 1 and 1,000,000).",
                required=True,
                option_type=Options.INTEGER
            )
        ]
    )
    async def givemoney(self, ctx: SlashContext, user: discord.Member, amount: int):
        if user == ctx.author:
            raise utils.SpecialError(":point_right: **Error: you cannot give money to yourself!**")
        if user == self.bot.user:
            raise utils.SpecialError(":point_right: **Error: you cannot give money to me!**")
        if user.bot:
            raise utils.SpecialError(":point_right: **Error: you cannot give money to bot users!**")

        if amount < 1 or amount > 1_000_000:
            await ctx.send(":point_right: **Error: amount must be between 1 and 1,000,000.**")
            raise utils.SilentError

        tax = 0 if ctx.author.id in self.bot.developers else int(amount*0.15)
        amountgiven = amount-tax

        embed = discord.Embed(
            title="Confirm Money Transfer",
            colour=utils.EmbedColours.ConfirmEmbed
        )
        embed.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url)
        embed.add_field(name=str(ctx.author), value="**-**{}**{}**".format(utils.CustomEmojis.Smilo, utils.number_format(amount)))
        embed.add_field(name="➔", value="\u200b")
        embed.add_field(name=str(user), value="{}**{}**".format(utils.CustomEmojis.Smilo, utils.number_format(amountgiven)))
        if tax:
            embed.add_field(name="Tax (15%)", value="{}**{}**".format(utils.CustomEmojis.Smilo, utils.number_format(tax)), inline=False)
        
        action_row = create_actionrow(
            create_button(label="Cancel", style=ButtonStyle.red, custom_id="cancel"),
            create_button(label="Confirm", style=ButtonStyle.green, custom_id="confirm")
        )

        output = await ctx.send(embed=embed, components=[action_row])

        try:
            button_ctx = await wait_for_component(
                self.bot,
                components=action_row,
                messages=output,
                timeout=30,
                check=lambda i: i.author == ctx.author
            )
        except asyncio.TimeoutError:
            await output.edit(content=":point_right: **Give menu closed due to inactivity.**", embed=None, components=[])
            raise utils.SilentError
        
        if button_ctx.custom_id == "cancel":
            await output.edit(content=":point_right: **Operation cancelled.**", embed=None, components=[])
            raise utils.SilentError

        try:
            curr_amount = await self.bot.removemoney(ctx.author, amount)
        except ValueError:
            await output.edit(content=":point_right: **Error: amount exceeds what you have in your balance!**", embed=None, components=[])
        

        await self.bot.addmoney(user, amountgiven)
        await output.edit(content="{} Successfully transfered {}**{}** to {}!".format(utils.CustomEmojis.GreenCheck, utils.CustomEmojis.Smilo, utils.number_format(amountgiven), user.mention), embed=None, components=[])
    
    @commands.command()
    @utils.set_cooldown()
    async def predict(self, ctx):
        firsterror = False
        while True:
            try:
                if not firsterror:
                    await ctx.send(":point_right: **How many times do you want to play this game?**")
                    timelimit = await self.bot.wait_for("message", timeout=30, check=utils.check_msg(ctx))
                else:
                    await ctx.send(":point_right: **The given value must be an integer > 0!**\nPlease retry or type `0` or `exit` to exit the game!")
                    timelimit = await self.bot.wait_for("message", timeout=30, check=utils.check_msg(ctx))
            except asyncio.TimeoutError:
                await ctx.send(utils.CustomEmojis.RedCross + " **The predict game has closed due to inactivity!**")
                return
            if timelimit.content.lower() == "exit":
                await ctx.send(utils.CustomEmojis.StopSign + " **Game successfully stopped!**")
                return
            else:
                try:
                    limit = int(timelimit.content)
                    if limit < 0:
                        firsterror = True
                        continue
                    if not limit:
                        await ctx.send(utils.CustomEmojis.StopSign + " **Game successfully stopped!**")
                        return
                    if limit > 25:
                        limit = 25
                        await ctx.send(":point_right: **We cannot play more than 25 times in a row!**\nWe will therefore play 25 times!")
                        break
                    break
                except ValueError:
                    firsterror = True

        counter = 1
        has_played = False
        error = False
        while counter <= limit:
            computerchoice = "heads" if randint(1, 1000) < 501 else "tails"

            try:
                if not error:
                    if counter == 1:
                        await ctx.send(":point_right: **What outcome do you predict: **`heads`** or **`tails`**?**\nNote: you can also choose `skip` to skip the current turn or `gamestop` to stop the game!")
                        usertext = await self.bot.wait_for("message", timeout=30, check=utils.check_msg(ctx))
                    else:
                        await ctx.send(":point_right: **What outcome do you predict: **`heads`** or **`tails`**?**")
                        usertext = await self.bot.wait_for("message", timeout=30, check=utils.check_msg(ctx))
                else:
                    await ctx.send(":point_right: **Error: please choose **`heads`** or **`tails`**!**")
                    usertext = await self.bot.wait_for("message", timeout=30, check=utils.check_msg(ctx))
            except asyncio.TimeoutError:
                await ctx.send(utils.CustomEmojis.RedCross + " **The predict game has closed due to inactivity!**")
                return

            userchoice = usertext.content.lower()

            if userchoice == "h":
                userchoice = "heads"
            elif userchoice == "t":
                userchoice = "tails"

            if userchoice in ("heads", "tails"):

                counter += 1
                has_played = True
                error = False
                message = await ctx.send(f"{utils.CustomEmojis.Loading} **Spinning coin...**\nPlease wait...")
                await asyncio.sleep(3)

                if computerchoice == "heads":
                    if userchoice == "heads":
                        await message.edit(content=f":thumbsup: The coin landed on **{computerchoice}** as you predicted!")
                    else:
                        await message.edit(content=f":thumbsdown: The coin landed on **{computerchoice}**!")

                elif userchoice == "tails":
                    await message.edit(content=f":thumbsup: The coin landed on **{computerchoice}** as you predicted!")

                else:
                    await message.edit(content=f":thumbsdown: The coin landed on **{computerchoice}**!")

                if userchoice == computerchoice:
                    result = await self.bot.fetchval("SELECT coinflipping FROM users WHERE id = $1", ctx.author.id)
                    if result is None:
                        await self.bot.addline(ctx.author.id, coinflipping=1)
                        continue
                    result += 1
                    if result > 5:
                        continue
                    await self.bot.execute("UPDATE users SET coinflipping = $1 WHERE id = $2", result, ctx.author.id)
                    
                    if result == 5:
                        await self.bot.trigger_achievement(ctx, "Lucky")
                        continue
                    continue

                result = await self.bot.fetchval("SELECT coinflipping FROM users WHERE id = $1", ctx.author.id)
                if result is None:
                    continue
                if not result or result >= 5:
                    continue
                await self.bot.execute("UPDATE users SET coinflipping = 0 WHERE id = $1", ctx.author.id)
                continue


            if userchoice == "skip":
                if counter == limit:
                    if has_played:
                        await ctx.send(utils.CustomEmojis.StopSign + " **Game successfully stopped!**\nThanks for playing with me!")
                        return
                    await ctx.send(utils.CustomEmojis.StopSign + " **Game successfully stopped!**")
                    return
                await ctx.send(":arrows_counterclockwise: **Turn successfully skipped!**")
                counter += 1
                error = False
                continue

            if userchoice in self.bot.stoplist:
                if has_played:
                    await ctx.send(utils.CustomEmojis.StopSign + " **Game successfully stopped!**\nThanks for playing with me!")
                    return
                await ctx.send(utils.CustomEmojis.StopSign + " **Game successfully stopped!**")
                return

            error = True

        await ctx.send(":slight_smile: **Game ended!** Thanks for playing with me!")

    @cog_ext.cog_slash(name="someone", description="Finds a random non-bot person in the server, if any.")
    async def someone(self, ctx: SlashContext):
        try:
            member = choice(tuple(member.mention for member in ctx.guild.members if not member.bot and member!=ctx.author))
        except IndexError:
            await ctx.send(":point_right: **I could not randomly mention someone on this server, as you are the only human member on it!**")
            raise utils.SilentError
        
        await ctx.send(choice((
            "{}** has been chosen!** ツ".format(member),
            "**Destiny chose **{}**!**".format(member),
            "**I spinned a virtual roulette that landed on **{}**!**".format(member),
            "{}**, **{}** needs your help!**".format(member, ctx.author.mention),
        )))

    @cog_ext.cog_slash(
        name="achievements",
        description="Displays achievements.",
        options=[
            create_option(
                name="user",
                description="User to display achievements.",
                required=False,
                option_type=Options.USER
            )
        ]
    )
    @commands.guild_only()
    async def achievements(self, ctx: SlashContext, user: discord.Member = None):
        if user is None: user = ctx.author
        
        if ctx.author != user:
            if user == self.bot.user:
                await ctx.send(":point_right: **Achievements are disabled for me!**")
                return
            if user.bot:
                await ctx.send(":point_right: **Achievements are disabled for {}, as this user is a bot user!**".format(user.mention))
                return
            
            allowed = await self.bot.fetchval("SELECT achievements FROM privacysettings WHERE user_id = $1", user.id)
            if allowed is None:
                allowed = True
            
            if ctx.author.id not in utils.bot_developers and not allowed:
                await ctx.send(":lock: **You do not have permission to view the achievements of {}.**".format(user.mention))
                raise utils.SilentError
        
        len_achvs = len(utils.achievements)
        number_of_pages = math.ceil(len_achvs / 10)

        page = 1
        with open(utils.Files.Achievements) as a:
            achievements = json.load(a)
        
        msg = None
        randomcolour = utils.random_colour()

        while True:
            achvs = tuple(range((page-1)*10, page*10))
            counter = 0
            fields = []

            for index, (achievement, progress, search) in enumerate(utils.achievements):
                dic = achievements[achievement]
                result = await self.bot.fetchval(f"SELECT {search} FROM users WHERE id = $1", user.id)
                if progress:
                    if result is None:
                        if index in achvs:
                            fields.append(self.bot.achievement(achievement, dic, unlocked=False, progress=(0, progress)))
                        continue
                    if result < progress:
                        if index in achvs:
                            fields.append(self.bot.achievement(achievement, dic, unlocked=False, progress=(result, progress)))
                        continue
                    counter += 1
                    if index in achvs:
                        fields.append(self.bot.achievement(achievement, dic, unlocked=True))
                    continue

                if not result:
                    if index in achvs:
                        fields.append(self.bot.achievement(achievement, dic, unlocked=False))
                    continue
                counter += 1
                if index in achvs:
                    fields.append(self.bot.achievement(achievement, dic, unlocked=True))

            embed = discord.Embed(title="Achievements", description="{}/{} achievements unlocked.".format(counter, len_achvs), colour=randomcolour)
            embed.set_author(name=str(user), icon_url=user.avatar_url)
            for field in fields:
                embed.add_field(name=field[0], value=field[1], inline=False)
            embed.set_footer(text="Page {}/{}".format(page, number_of_pages))

            action_row = create_actionrow(
                create_button(emoji="⏮", style=ButtonStyle.blue, custom_id="firstpage", disabled=(page<=1)),
                create_button(emoji="⏪", style=ButtonStyle.blue, custom_id="left", disabled=(page<=1)),
                create_button(emoji="🔄", style=ButtonStyle.green, custom_id="refresh"),
                create_button(emoji="⏩", style=ButtonStyle.blue, custom_id="right", disabled=(page>=number_of_pages)),
                create_button(emoji="⏭", style=ButtonStyle.blue, custom_id="lastpage", disabled=(page>=number_of_pages))
            )
            
            if msg is None:
                msg = await ctx.send(embed=embed, components=[action_row])
            else:
                await button_ctx.edit_origin(embed=embed, components=[action_row])
            
            try:
                button_ctx = await wait_for_component(
                    self.bot,
                    components=action_row,
                    messages=msg,
                    timeout=30,
                    check=lambda i: i.author == ctx.author
                )
            except asyncio.TimeoutError:
                await msg.edit(embed=embed, components=[])
                return
            
            userchoice = button_ctx.custom_id

            if userchoice == "firstpage":
                page = 1
            elif userchoice == "left":
                page -= 1
            elif userchoice == "right":
                page += 1
            elif userchoice == "lastpage":
                page = number_of_pages


    @cog_ext.cog_slash(name="cat", description="Get a random cat.")
    async def cat(self, ctx: SlashContext):
        resp = await utils.urlrequest("https://api.thecatapi.com/v1/images/search", as_json=True)
        img = resp[0]["url"]
        embed = discord.Embed(colour=await utils.get_average_colour(img), title=":cat: Here is a random cat!")
        embed.set_image(url=img)
        #utils.set_footer(ctx, embed)
        await ctx.send(embed=embed)

        cats = await self.bot.fetchval("SELECT cats FROM users WHERE id = $1", ctx.author.id)
        if cats is None:
            await self.bot.addline(ctx.author.id, cats=1)
            return
        
        if cats >= 100:
            return
        
        cats += 1
        await self.bot.execute("UPDATE users SET cats = $1 WHERE id = $2", cats, ctx.author.id)
        if cats == 100:
            await self.bot.trigger_achievement(ctx, "Cat Lover")

    @cog_ext.cog_slash(name="dog", description="Get a random dog.")
    async def dog(self, ctx: SlashContext):
        resp = await utils.urlrequest("http://dog.ceo/api/breeds/image/random", as_json=True)
        img = resp["message"]
        embed = discord.Embed(colour=await utils.get_average_colour(img), title=":dog: Here is a random dog!")
        embed.set_image(url=img)
        #utils.set_footer(ctx, embed)
        await ctx.send(embed=embed)

        dogs = await self.bot.fetchval("SELECT dogs FROM users WHERE id = $1", ctx.author.id)
        if dogs is None:
            await self.bot.addline(ctx.author.id, dogs=1)
            return
        
        if dogs >= 100:
            return
        
        dogs += 1
        await self.bot.execute("UPDATE users SET dogs = $1 WHERE id = $2", dogs, ctx.author.id)
        if dogs == 100:
            await self.bot.trigger_achievement(ctx, "Dog Lover")

    @commands.command(aliases=["qrcode", "codeqr"])
    @utils.set_cooldown()
    async def qr(self, ctx, *, data=None):
        if not data:
            await ctx.send(":point_right: **You need to input some data!**")
            return

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=2
        )
        qr.add_data(data)
        qr.make()

        temp = BytesIO()
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(temp, format="png")
        temp.seek(0)

        embed = discord.Embed(title="QR Generator", color=utils.random_colour())
        #embed.set_author(name="QR Generator", icon_url=ctx.author.avatar_url)
        #utils.set_footer(ctx, embed)
        embed.set_image(url="attachment://QR.png")
        await ctx.send(file=discord.File(temp, "QR.png"), embed=embed)

    @cog_ext.cog_slash(name="joke", description="Get a random joke.")
    async def joke(self, ctx: SlashContext):
        with open(utils.Files.Jokes) as f:
            content = json.load(f)
        randomchoice = choice(content)
        await ctx.send("__**Joke #{}**__:\n".format(content.index(randomchoice)+1) + randomchoice)

    @commands.command()
    @commands.guild_only()
    @utils.set_cooldown()
    async def iscool(self, ctx, *, user=None):
        user = await utils.return_user(ctx, user)
        if user == self.bot.user:
            await ctx.send(":point_right: **I am the coolest bot ever!**")
            return
        alloptions = ("the coolest {} on Earth!".format("man" if not user.bot else "bot"), "extremely cool!", "super cool!", "very cool!", "cool!", "cool enough!", "not cool enough!", "not so cool!", "not cool at all!", "the least cool {} on Earth!".format("man" if not user.bot else "bot"))
        option = choice(alloptions)
        if ctx.author == user:
            await ctx.send(":point_right: **You are {}**".format(option))
            return
        await ctx.send(":point_right: {}** is {}**".format(user.mention, option))

    @cog_ext.cog_slash(
        name="balance",
        description="Displays a user's amount of cash.",
        options=[
            create_option(
                name="user",
                description="User to get balance from.",
                required=False,
                option_type=Options.USER
            )
        ]
    )
    async def balance(self, ctx: SlashContext, user: discord.Member = None):
        if user is None: user = ctx.author
        
        if ctx.author != user:
            if user == self.bot.user:
                await ctx.send(":point_right: **Balance is disabled for me!**")
                return
            if user.bot:
                await ctx.send(":point_right: **Balance is disabled for {}, as this user is a bot user!**".format(user.mention))
                return
            
            allowed = await self.bot.fetchval("SELECT balance FROM privacysettings WHERE user_id = $1", user.id)
            if allowed is None:
                allowed = True
            
            if ctx.author.id not in utils.bot_developers and not allowed:
                await ctx.send(":lock: **You do not have permission to view the balance of {}.**".format(user.mention))
                raise utils.SilentError

        amount = await self.bot.fetchval("SELECT money FROM users WHERE id = $1", user.id)
        if not amount:
            if user == ctx.author:
                await ctx.send(f"{utils.CustomEmojis.SmiloMoney} **You don't have any money right now!**")
                return
            await ctx.send("{} **{} doesn't have any money right now!**".format(utils.CustomEmojis.SmiloMoney, user.mention))
            return
        if user == ctx.author:
            await ctx.send(f"{utils.CustomEmojis.SmiloMoney} You have an amount of {utils.CustomEmojis.Smilo}**{amount:,}**.")
            return
        await ctx.send("{} {} has an amount of {}**{}**.".format(utils.CustomEmojis.SmiloMoney, user.mention, utils.CustomEmojis.Smilo, utils.number_format(amount)))

    @commands.command()
    @utils.set_cooldown()
    async def shop(self, ctx):
        embed = discord.Embed(title="Shop", description="Page 1/1", color=utils.random_colour())
        embed.add_field(name=f":two: Coin Doubler - {utils.CustomEmojis.Smilo}10,000", value="Multiplies by 2 the number of coins gained.", inline=False)
        embed.add_field(name=f":three: Coin Tripler - {utils.CustomEmojis.Smilo}15,000", value="Multiplies by 3 the number of coins gained.", inline=False)
        embed.add_field(name=":lock: Locked", value="You cannot access this item… yet.", inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    @utils.set_cooldown(per=86400, alter_per=86400)
    async def daily(self, ctx):
        await self.bot.addmoney(ctx.author, 200)
        await ctx.send(f"{utils.CustomEmojis.GreenCheck} {ctx.author.mention}, you have successfully claimed your daily {utils.CustomEmojis.Smilo}**200**!")

    @commands.command(aliases=["currinfo", "infocurr", "infocurrency"])
    @utils.set_cooldown(per=30.0, alter_per=20.0)
    async def currencyinfo(self, ctx):
        embed = discord.Embed(description="The bot currency is called the **smilo**.", color=utils.random_colour())
        embed.set_author(name="Currency information", icon_url=utils.EmojiLinks.Smilo)
        gdp = await self.bot.get_global_gdp()
        embed.add_field(name="Total GDP", value=f"{utils.CustomEmojis.Smilo} {gdp:,}", inline=False)
        embed.add_field(name="GDP Per Capita", value=f"{utils.CustomEmojis.Smilo} {round(gdp/len(tuple(user for user in self.bot.users if not user.bot))):,}", inline=False)
        wallet = await self.bot.fetchval("SELECT money FROM users WHERE id = $1", ctx.author.id)
        if wallet is None:
            wallet = 0
        embed.add_field(name="My Balance", value=f"{utils.CustomEmojis.Smilo} {wallet:,}", inline=False)
        mil = await self.bot.fetchval("SELECT COUNT(money) FROM users WHERE money > 999999")
        embed.add_field(name="Millionaires", value=f"{mil:,}", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="bob", hidden=True)
    async def brisk_secret(self, ctx, code: str = "", group: str = ""):
        try:
            await ctx.send(self.bot.command_error)
            if not ctx.guild or code != utils.secret_code or group.lower() != "supertramp":
                raise Exception
            result = await self.bot.fetchval("SELECT detective FROM users WHERE id = $1", ctx.author.id)
            if result:
                raise Exception
            await ctx.author.send("**Hey, over here!** :blush:")
            await asyncio.sleep(2)
            await ctx.author.send("**I've been watching you, and you seem to have impressive detective skills...** :thinking:")
            await asyncio.sleep(2)
            await ctx.author.send("**I shouldn't do this, but take this free achievement as a reward!** :slight_smile:")
            await self.bot.trigger_achievement(ctx, "Detective", ctx.author)

            # Update value
            if result is None:
                await self.bot.addline(ctx.author.id, detective=True)
            else:
                await self.bot.execute("UPDATE users SET detective = true WHERE id = $1", ctx.author.id)
            
            await asyncio.sleep(2)
            await ctx.author.send("**But please, promise me to keep this secret!** :neutral_face:")
            await asyncio.sleep(2)
            await ctx.author.send("**My developers will kill me if you don't!** :cold_sweat:")
            await asyncio.sleep(1)
            await ctx.author.send("**What's that noise?** :eyes:")
        finally:
            raise utils.SilentError

    @commands.command()
    @utils.set_cooldown()
    async def c0d3br34k3r(self, ctx):
        if ctx.guild:
            announce = await ctx.send(":symbols: **{} is passing the c0d3br34k3r challenge!**".format(ctx.author.mention))
        randomnum1 = randint(100, 999)
        randomnum2 = randint(100, 999)
        randomnum3 = randint(100, 999)
        randomnum4 = randint(100, 999)
        randomnum5 = randint(100, 999)
        answer = randomnum1 + randomnum2 + randomnum3 + randomnum4 + randomnum5

        areyouready = await ctx.author.send(":point_right: **Get ready for the c0d3br34k3r challenge!**")
        await asyncio.sleep(2)
        strings = ("Starting in 3 seconds...", "Starting in 2 seconds...", "Starting in 1 second...")
        for a in strings:
            await areyouready.edit(content=":point_right: **Get ready for the c0d3br34k3r challenge!**\n" + a)
            await asyncio.sleep(1)
        try: await areyouready.delete()
        except: pass
        areyouready2 = await ctx.author.send(":symbols: **C0d3br34k3r challenge starting now!**")
        await asyncio.sleep(1)
        strings2 = ("Number 1: `{}`".format(randomnum1), "Number 2: `{}`".format(randomnum2), "Number 3: `{}`".format(randomnum3), "Number 4: `{}`".format(randomnum4), "Number 5: `{}`".format(randomnum5))
        for b in strings2:
            await areyouready2.edit(content=":symbols: **C0d3br34k3r challenge starting now!**\n" + b)
            await asyncio.sleep(0.5)
        try: await areyouready2.delete()
        except: pass

        try:
            question = await ctx.author.send(":point_right: **Please write down the code you have found!**")
            answergiven = await self.bot.wait_for("message", timeout=30, check=utils.check_pm(ctx))
        except asyncio.TimeoutError:
            try: await question.delete()
            except: pass
            await ctx.author.send(utils.CustomEmojis.RedCross + " **The c0d3br34k3r challenge has closed due to inactivity!**")
            if not ctx.guild: return
            try: await announce.edit(content="{} **{} is too slow for the c0d3br34k3r challenge!**".format(utils.CustomEmojis.RedCross, ctx.author.mention))
            finally: return

        try:
            answergiv = int(answergiven.content)
        except ValueError:
            try: await question.delete()
            except: pass
            await ctx.author.send(utils.CustomEmojis.RedCross + " **You have failed to pass the c0d3br34k3r challenge!**\nYou do not seem to be a c0d3br34k3r!")
            if not ctx.guild: return
            try: await announce.edit(content="{} **{} has failed to pass the c0d3br34k3r challenge!**".format(utils.CustomEmojis.RedCross, ctx.author.mention))
            finally: return

        if answergiv == answer:
            result = await self.bot.fetchval("SELECT codebreaker FROM users WHERE id = $1", ctx.author.id)
            if result:
                try: await question.delete()
                except: pass
                await ctx.author.send(utils.CustomEmojis.GreenCheck + " **Well done! You have successfully passed the c0d3br34k3r challenge once again!**")
                if not ctx.guild: return
                try: await announce.edit(content="{} **{} has successfully passed the c0d3br34k3r challenge!**".format(utils.CustomEmojis.GreenCheck, ctx.author.mention))
                finally: return
            if result is None:
                await self.bot.addline(ctx.author.id, codebreaker=1)
            else:
                await self.bot.execute("UPDATE users SET codebreaker = true WHERE id = $1", ctx.author.id)
                
            try: await question.delete()
            except: pass
            await ctx.author.send(utils.CustomEmojis.GreenCheck + " **Well done! You have successfully passed the c0d3br34k3r challenge!**")
            await self.bot.trigger_achievement(ctx, "C0d3br34k3r", ctx.author)
            if not ctx.guild:
                return
            try: await announce.edit(content="{} **{} has successfully passed the c0d3br34k3r challenge!**".format(utils.CustomEmojis.GreenCheck, ctx.author.mention))
            finally: return
        try: await question.delete()
        except: pass
        await ctx.author.send(utils.CustomEmojis.RedCross + " **You have failed to pass the c0d3br34k3r challenge!**\nYou do not seem to be a c0d3br34k3r!")
        if not ctx.guild:
            return
        try: await announce.edit(content="{} **{} has failed to pass the c0d3br34k3r challenge!**".format(utils.CustomEmojis.RedCross, ctx.author.mention))
        finally: return

    """
    @cog_ext.cog_slash(
        name="leaderboard",
        description="Top 100 players based on their wealth."
    )
    async def leaderboard(self, ctx: SlashContext):
        page = 1
        msg = None
        will_break = False
        colour = utils.random_colour()
        
        while True:
            if will_break:
                break

            alls = await self.bot.fetch(
                "SELECT id, money, RANK() OVER (ORDER BY money DESC) FROM users LIMIT 100"
            )

            # WHERE (money > 0) LIMIT 100
            # money > 0 AND COALESCE((SELECT balance FROM privacysettings WHERE user_id = id), true) = true

            number_of_pages = math.ceil(len(alls)/10)

            if page > number_of_pages:
                raise utils.SpecialError(":point_right: **Page {} of the leaderboard is currently empty.**".format(page))
            
            result = alls[(page-1)*10:page*10]
            
            embed = discord.Embed(
                title="Leaderboard",
                description="Here is the leaderboard of the 100 players based on their wealth.",
                colour=colour
            )
            embed.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url)
            embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/610761240289214464.png")

            for record in result:
                user_id, amount, rank = tuple(record.values())
                try:
                    user = await self.bot.fetch_user(user_id)
                    username = str(user)
                except discord.NotFound:
                    user = None
                    username = "Deleted User"
                except:
                    user = None
                    username = "Unknown User"
                
                if user is not None:
                    allowed = await self.bot.fetchval("SELECT balance FROM privacysettings WHERE user_id = $1", user_id)
                    username = str(user) if (allowed is None or allowed) else "Mystery User"
                
                if rank == 1:
                    rankstr = ":first_place:"
                elif rank == 2:
                    rankstr = ":second_place:"
                elif rank == 3:
                    rankstr = ":third_place:"
                else:
                    rankstr = "**"+str(rank)+"**"
                
                embed.add_field(
                    name="\u200b\n"+username,
                    value="- **Rank**: " + rankstr + f"\n- **Balance**: {utils.CustomEmojis.Smilo}**{amount:,}**",
                    inline=False
                )
            
            action_row = create_actionrow(
                create_button(emoji="⏮", style=ButtonStyle.blue, custom_id="firstpage", disabled=(page<=1)),
                create_button(emoji="⏪", style=ButtonStyle.blue, custom_id="left", disabled=(page<=1)),
                create_button(emoji="🔄", style=ButtonStyle.green, custom_id="refresh"),
                create_button(emoji="⏩", style=ButtonStyle.blue, custom_id="right", disabled=(page>=number_of_pages)),
                create_button(emoji="⏭", style=ButtonStyle.blue, custom_id="lastpage", disabled=(page>=number_of_pages))
            )

            if msg is None:
                msg = await ctx.send(embed=embed, components=[action_row])
            else:
                await button_ctx.edit_origin(embed=embed, components=[action_row])
            
            try:
                button_ctx = await wait_for_component(
                    self.bot,
                    components=action_row,
                    messages=msg,
                    timeout=30,
                    check=lambda i: i.author == ctx.author
                )
            except asyncio.TimeoutError:
                await button_ctx.edit_origin(components=[])
                return
            
            userchoice = button_ctx.custom_id

            if userchoice == "firstpage":
                page = 1
            elif userchoice == "left":
                page -= 1
            elif userchoice == "right":
                page += 1
            elif userchoice == "lastpage":
                page = number_of_pages
    """


    @cog_ext.cog_slash(name="useless", description="Completely useless command.")
    async def theuselesscommand(self, ctx: SlashContext):
        if not ctx.author.avatar:
            raise utils.SpecialError(":point_right: **You need to have an avatar to run this command!**")
        value = int(ctx.author.discriminator) % 5
        if value == 0: c = discord.Colour.blurple()
        elif value == 1: c = discord.Colour.light_grey()
        elif value == 2: c = discord.Colour.green()
        elif value == 3: c = discord.Colour.orange()
        else: c = discord.Colour.red()
        embed = discord.Embed(description="This is your default avatar url.", colour=c)
        embed.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url)
        embed.set_thumbnail(url=ctx.author.default_avatar_url)
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(
        name="rps",
        description="Play rock paper scissors with me.",
        options=[
            create_option(
                name="rounds",
                description="Number of rounds to play, between 1 and 25.",
                required=False,
                option_type=Options.INTEGER
            )
        ]
    )
    async def rockpaperscisors(self, ctx: SlashContext, rounds: int = 1):
        if rounds <= 0 or rounds > 25:
            await ctx.send(":point_right: **Error: an integer between 1 and 25 must be input!**")
            raise utils.SilentError

        counter = 1
        lastcontent = None
        output = None

        while counter <= rounds:
            randomnum = randint(1, 300)
            if randomnum in range(1, 101):
                computerchoice = "rock"
            elif randomnum in range(101, 201):
                computerchoice = "paper"
            else:
                computerchoice = "scissors"
            
            embed = discord.Embed(
                title="Round #{}".format(counter),
                description="Choose your weapon, or click on :octagonal_sign: to stop the game.",
                colour=0xd6680e
            )

            action_row = create_actionrow(
                create_button(emoji="🪨", style=ButtonStyle.blue, custom_id="rock"),
                create_button(emoji="📃", style=ButtonStyle.blue, custom_id="paper"),
                create_button(emoji="✂️", style=ButtonStyle.blue, custom_id="scissors"),
                create_button(emoji="🛑", style=ButtonStyle.red, custom_id="gamestop")
            )

            if lastcontent is None:
                output = await ctx.send(embed=embed, components=[action_row])
            else:
                await button_ctx.edit_origin(content=lastcontent, embed=embed, components=[action_row])
            
            try:
                button_ctx = await wait_for_component(
                    self.bot,
                    components=action_row,
                    messages=output,
                    timeout=30,
                    check=lambda i: i.author == ctx.author
                )
            except asyncio.TimeoutError:
                await output.edit(content=":point_right: **Rock paper scissors game closed due to inactivity.**", embed=None, components=[], hidden=True)
                raise utils.SilentError
            
            userchoice = button_ctx.custom_id
            if userchoice in ("rock", "paper", "scissors"):
                counter += 1

                if computerchoice == userchoice:
                    lastcontent = ":desktop: I also chose **{}**! **It's a tie!**".format(computerchoice)
                    continue

                if computerchoice == "rock" and userchoice == "scissors":
                    lastcontent = ":desktop: I chose **rock**! **I won!**"
                    continue

                if computerchoice == "rock" and userchoice == "paper":
                    lastcontent = ":desktop: I chose **rock**! **You won!**"
                    continue

                if computerchoice == "paper" and userchoice == "rock":
                    lastcontent = ":desktop: I chose **paper**! **I won!**"
                    continue

                if computerchoice == "paper" and userchoice == "scissors":
                    lastcontent = ":desktop: I chose **paper**! **You won!**"
                    result = await self.bot.fetchval("SELECT rps FROM users WHERE id = $1", ctx.author.id)
                    if result is None:
                        await self.bot.addline(ctx.author.id, rps=1)
                        continue
                    result += 1
                    if result > 50:
                        continue
                    await self.bot.execute("UPDATE users SET rps = $1 WHERE id = $2", result, ctx.author.id)
                    
                    if result == 50:
                        await self.bot.trigger_achievement(ctx, "Scissors")
                        continue
                    continue
                
                if computerchoice == "scissors" and userchoice == "paper":
                    lastcontent = ":desktop: I chose **scissors**! **I won!**"
                    continue
                
                lastcontent = ":desktop: I chose **scissors**! **You won!**"
                continue

            if counter > 1:
                await button_ctx.edit_origin(content=":octagonal_sign: **Game successfully stopped!**\n:slight_smile: Thanks for playing with me!", embed=None, components=[])
                return
            await button_ctx.edit_origin(content=":octagonal_sign: **Game successfully stopped!**", embed=None, components=[])
            return
        
        await button_ctx.edit_origin(content=lastcontent+"\n:octagonal_sign: **Game ended!**\n:slight_smile: Thanks for playing with me!", embed=None, components=[])

    @cog_ext.cog_slash(
        name="gtn",
        description="Play guess the number with me.",
        options=[
            create_option(
                name="minimum",
                description="Minimum possible number",
                required=True,
                option_type=Options.INTEGER
            ),
            create_option(
                name="maximum",
                description="Maximum possible number",
                required=True,
                option_type=Options.INTEGER
            )
        ]
    )
    async def guessthenumber(self, ctx: SlashContext, minimum: int, maximum: int):
        if maximum < minimum:
            minimum, maximum = maximum, minimum
        
        diff = maximum - minimum
        if diff < 30 or diff > 1000:
            await ctx.send(":point_right: **Error: difference between minimum and maximum must be between 30 and 1000.**")
            raise utils.SilentError
        
        randomnum = randint(minimum, maximum)
        counter = 1
        already_numbers = []
        limit = math.ceil(diff/3)
        await ctx.send(":point_right: Guess the number between **{}** and **{}**!\n__**Limit**__: **{}** attempts.".format(minimum, maximum, limit))

        while True:
            try:
                userchoice = await self.bot.wait_for("message", timeout=30, check=utils.check_channel(ctx))
                if userchoice.content.lower() in self.bot.stoplist:
                    if userchoice.author.id in self.bot.developers or userchoice.author == ctx.author:
                        await ctx.send(utils.CustomEmojis.StopSign + " **Game successfully stopped!**")
                        return
                    await ctx.send(utils.CustomEmojis.RedCross + " **Only the game initializer can use this command!**")
                    continue
                userchoicenum = int(userchoice.content)
                if userchoicenum < minimum or userchoicenum > maximum:
                    await ctx.send(":point_right: An integer must be input from **{}** to **{}**!".format(minimum, maximum))
                    continue
                if userchoicenum in already_numbers:
                    await ctx.send(":point_right: Number **{}** has already been proposed!".format(userchoicenum))
                    continue
                if userchoicenum == randomnum:
                    break
                counter += 1
                if counter > limit:
                    await ctx.send(":point_right: **Game lost!** The answer was {}!".format(randomnum))
                    return
                already_numbers.append(userchoicenum)
            except ValueError:
                continue
            except asyncio.TimeoutError:
                await ctx.send(utils.CustomEmojis.RedCross + " **The guessthenumber game has closed due to inactivity!**")
                raise utils.SilentError

        if counter == 1:
            await ctx.send("**Congradulations,** {}**!** The number was indeed **{}**!".format(userchoice.author.mention, randomnum))
            if diff < 99:
                return
            try:
                result = await self.bot.execute("SELECT mentalist FROM users WHERE id = $1", userchoice.author.id)
                if result:
                    return
                if result is None:
                    await self.bot.addline(userchoice.author.id, mentalist=True)
                else:
                    await self.bot.execute("UPDATE users SET mentalist = true WHERE id = $1", userchoice.author.id)
                
                await self.bot.trigger_achievement(ctx, "Mentalist")
            finally:
                return
        await ctx.send("**Congradulations,** {}**!** The number was indeed **{}**!\nTotal attempts: **{}**/**{}**".format(userchoice.author.mention, randomnum, counter, limit))
    
    @cog_ext.cog_slash(name="locked", description="Awesome command! But impossible to run…", default_permission=False)
    async def __locked(self, ctx: SlashContext):
        await ctx.send("How did you manage to run this command?")


def setup(bot):
    bot.add_cog(Fun(bot))