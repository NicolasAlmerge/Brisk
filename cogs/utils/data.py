#!/usr/bin/env python3

import re
import regex

__all__ = (
    "bot_owner",
    "bot_developers",
    "trusteds",
    "defaultcolour",
    "dev_guild_id",
    "support_guild_id",
    "confirmlist",
    "cancellist",
    "secret_code",
    "Options",
    "achievements",
    "LONG_HEX_COLOR",
    "SHORT_HEX_COLOR",
    "RGB_TUPLE",
    "CustomEmojis",
    "Links",
    "Files",
    "EmbedColours",
    "EmojiLinks",
    "Reactions",
    "NAMES_TO_HEX",
    "HEX_TO_NAMES"
)

##### BOT ROLES #####
# 👑 Owner: Pigeon Bleu#2600
# 🛠 Developers, in order: Khryashch#1881, Clespy#4083
# ⭐️ Trusted Users, in order: swaswan#1842, 𝔼𝟘𝟛#9685, alex_almerge#1584, Skyrall#1412

bot_owner = 401046718030020610
bot_developers = (bot_owner, 432509292898418699, 360826371087269888)
trusteds = bot_developers + (480026984114814977, 605114755018915840, 402355659397529603, 326543406103003139)

defaultcolour = 0x696969
dev_guild_id = 510027458662105089
support_guild_id = 470864809710059520

confirmlist = "yes", "y", "ye", "yeah", "please", "confirm"
cancellist = "no", "n", "nope", "stop", "exit", "cancel"
secret_code = "3ihwX1Oe9DvcTLSNlPem"

class Options:
    STRING  = 3
    INTEGER = 4
    USER    = 6
    CHANNEL = 7

achievements = (
    ("Math Destroyer", None, "mathdestroy"),
    ("C0d3br34k3r", None, "codebreaker"),
    ("Detective", None, "detective"),
    ("Cat Lover", 100, "cats"),
    ("Dog Lover", 100, "dogs"),
    ("Mentalist", None, "mentalist"),
    ("Lucky", 5, "coinflipping"),
    ("Scissors", 50, "rps"),
    ("Roulette Expert", None, "roll"),

    ("First Step", 50, "commands"),
    ("Shy Guy", 250, "commands"),
    ("Geek", 1000, "commands"),
    ("Addicted", 5000, "commands"),
    ("Robot", 10000, "commands"),
    ("Legend", 20000, "commands"),

    ("Level 5", 5, "level"),
    ("Level 10", 10, "level"),
    ("Level 15", 15, "level"),
    ("Level 20", 20, "level"),
    ("Level 25", 25, "level"),
    ("Level 30", 30, "level"),
    ("Level 35", 35, "level"),
    ("Level 40", 40, "level"),
    ("Level 45", 45, "level"),
    ("Level 50", 50, "level")
)


LONG_HEX_COLOR = re.compile(r"#?[0-9a-fA-F]{6}")
SHORT_HEX_COLOR = re.compile(r"#?[0-9a-fA-F]{3}")
RGB_TUPLE = regex.compile(
    r"(?|(?:rgb\s*)?\(\s*([0-9]+)\s*"
    r"\,\s*([0-9]+)\s*\,\s*([0-9]+)\s*\)|"
    r"([0-9]+)\s*"
    r"\,\s*([0-9]+)\s*\,\s*([0-9]+))",
    regex.IGNORECASE
)


class CustomEmojis:
    """Class representing custom emojis."""

    # Smilo = "<:smilo_banknote:610561635211280397>"
    Smilo = "<:smilo:742810361794920499>"
    SmiloCoin = "<:smilo_coin:610561632279724082>"
    SmiloMoney = "<:smilo_money:610761240289214464>"
    Online = "<:online:598804039739637770>"
    Idle = "<:idle:598804174011891732>"
    DND = "<:dnd:598804229301207050>"
    Invisible = "<:invisible:598804316744056842>"
    GreenCheck = "<:greencheck:563404313846612028>"
    RedCross = "<:redcross:563404222436212736>"
    GreyNeutral = "<:greyneutral:563404284910239744>"
    StopSign = "<:stop:568845842908315648>"
    Enabled = "<:enabled:573498160182329344>"
    Disabled = "<:disabled:573498196274315264>"
    BotDeveloper = "<:developer:600636449213251584>"
    TrustedUser = "<:trusted:600485063955578880>"
    Loading = "<a:loading:614849889880375331>"
    Roulette = "<a:roulette:796019669945024572>"


class Links:
    """Class representing important links."""

    Invite = "https://bit.ly/BriskBotInvite"
    Server = "https://discord.gg/NEhB5De"
    GitHub = "https://github.com/NicolasAlmerge/Brisk"
    SecretLink = "https://justpaste.it/BriskBotSecretPage"


class Files:
    """Class representing JSON resource files."""

    Jokes = "./resources/jokes.json"
    Achievements = "./resources/achievements.json"
    Downloads = "./downloads"


class EmbedColours:
    """Class representing embed colours."""

    ConfirmEmbed = 0xd7342a
    MessageDeletion = 0xff0000
    MessageEdition = 0xff6a00


class EmojiLinks:
    """Class representing emoji links."""

    BotLogo = "https://cdn.discordapp.com/emojis/653332594762448923.png"
    BotDeveloper = "https://cdn.discordapp.com/emojis/600636449213251584.png"
    TrustedUser = "https://cdn.discordapp.com/emojis/600485063955578880.png"
    DefaultUserLogo = "https://cdn.discordapp.com/emojis/796475244080660537.png"
    Smilo = "https://cdn.discordapp.com/emojis/687297694150033459.png"


class Reactions:
    FIRST_PAGE = "⏮"
    LEFT_ARROW = "⏪"
    REFRESH = "🔄"
    RIGHT_ARROW = "⏩"
    LAST_PAGE = "⏭"
    STOP = "⏹"


_formatted = {
    "alice blue": "#F0F8FF",
    "antique white": "#FAEBD7",
    "aqua": "#00FFFF",
    "aquamarine": "#7FFFD4",
    "azure": "#F0FFFF",
    "beige": "#F5F5DC",
    "bisque": "#FFE4C4",
    "black": "#000000",
    "blanched almond": "#FFEBCD",
    "blue": "#0000FF",
    "blue violet": "#8A2BE2",
    "brown": "#A52A2A",
    "burlywood": "#DEB887",
    "cadet blue": "#5F9EA0",
    "chartreuse": "#7FFF00",
    "chocolate": "#D2691E",
    "coral": "#FF7F50",
    "cornflower blue": "#6495ED",
    "cornsilk": "#FFF8DC",
    "crimson": "#DC143C",
    "cyan": "#00FFFF",
    "dark blue": "#00008B",
    "dark cyan": "#008B8B",
    "dark goldenrod": "#B8860B",
    "dark gray": "#A9A9A9",
    "dark green": "#006400",
    "dark grey": "#A9A9A9",
    "dark khaki": "#BDB76B",
    "dark magenta": "#8B008B",
    "dark fuchsia": "#8B008B",
    "dark olive green": "#556B2F",
    "dark orange": "#FF8C00",
    "dark orchid": "#9932CC",
    "dark red": "#8B0000",
    "dark salmon": "#E9967A",
    "dark sea green": "#8FBC8F",
    "dark slate blue": "#483D8B",
    "dark slate gray": "#2F4F4F",
    "dark slate grey": "#2F4F4F",
    "dark turquoise": "#00CED1",
    "dark violet": "#9400D3",
    "deep pink": "#FF1493",
    "deep sky blue": "#00BFFF",
    "dim gray": "#696969",
    "dim grey": "#696969",
    "dodger blue": "#1E90FF",
    "firebrick": "#B22222",
    "floral white": "#FFFAF0",
    "forest green": "#228B22",
    "fuchsia": "#FF00FF",
    "gainsboro": "#DCDCDC",
    "ghost white": "#F8F8FF",
    "gold": "#FFD700",
    "goldenrod": "#DAA520",
    "gray": "#808080",
    "green": "#008000",
    "green yellow": "#ADFF2F",
    "grey": "#808080",
    "honeydew": "#F0FFF0",
    "hot pink": "#FF69B4",
    "indian red": "#CD5C5C",
    "indigo": "#4B0082",
    "ivory": "#FFFFF0",
    "khaki": "#F0E68C",
    "lavender": "#E6E6FA",
    "lavender blush": "#FFF0F5",
    "lawn green": "#7CFC00",
    "lemon chiffon": "#FFFACD",
    "light blue": "#ADD8E6",
    "light coral": "#F08080",
    "light cyan": "#E0FFFF",
    "light goldenrodyellow": "#FAFAD2",
    "light gray": "#D3D3D3",
    "light green": "#90EE90",
    "light grey": "#D3D3D3",
    "light pink": "#FFB6C1",
    "light salmon": "#FFA07A",
    "light sea green": "#20B2AA",
    "light sky blue": "#87CEFA",
    "light slate gray": "#778899",
    "light slate grey": "#778899",
    "light steel blue": "#B0C4DE",
    "light yellow": "#FFFFE0",
    "lime": "#00FF00",
    "lime green": "#32CD32",
    "linen": "#FAF0E6",
    "magenta": "#FF00FF",
    "maroon": "#800000",
    "medium aqua marine": "#66CDAA",
    "medium blue": "#0000CD",
    "medium orchid": "#BA55D3",
    "medium purple": "#9370DB",
    "medium sea green": "#3CB371",
    "medium slate blue": "#7B68EE",
    "medium spring green": "#00FA9A",
    "medium turquoise": "#48D1CC",
    "medium violet red": "#C71585",
    "midnight blue": "#191970",
    "mint cream": "#F5FFFA",
    "misty rose": "#FFE4E1",
    "moccasin": "#FFE4B5",
    "navajo white": "#FFDEAD",
    "navy": "#000080",
    "navy blue": "#000080",
    "blue navy": "#000080",
    "old lace": "#FDF5E6",
    "olive": "#808000",
    "olive drab": "#6B8E23",
    "orange": "#FFA500",
    "orange red": "#FF4500",
    "orchid": "#DA70D6",
    "pale goldenrod": "#EEE8AA",
    "pale green": "#98FB98",
    "pale turquoise": "#AFEEEE",
    "pale violet red": "#DB7093",
    "papaya whip": "#FFEFD5",
    "peach puff": "#FFDAB9",
    "peru": "#CD853F",
    "pink": "#FFC0CB",
    "plum": "#DDA0DD",
    "powder blue": "#B0E0E6",
    "purple": "#800080",
    "rebecca purple": "#663399",
    "red": "#FF0000",
    "rosy brown": "#BC8F8F",
    "royal blue": "#4169E1",
    "saddle brown": "#8B4513",
    "salmon": "#FA8072",
    "sandy brown": "#F4A460",
    "sea green": "#2E8B57",
    "seashell": "#FFF5EE",
    "sienna": "#A0522D",
    "silver": "#C0C0C0",
    "sky blue": "#87CEEB",
    "slate blue": "#6A5ACD",
    "slate gray": "#708090",
    "slate grey": "#708090",
    "snow": "#FFFAFA",
    "spring green": "#00FF7F",
    "steel blue": "#4682B4",
    "tan": "#D2B48C",
    "teal": "#008080",
    "thistle": "#D8BFD8",
    "tomato": "#FF6347",
    "turquoise": "#40E0D0",
    "violet": "#EE82EE",
    "wheat": "#F5DEB3",
    "white": "#FFFFFF",
    "white smoke": "#F5F5F5",
    "yellow": "#FFFF00",
    "yellow green": "#9ACD32"
}

NAMES_TO_HEX = {key.replace(" ", ""): value for key, value in _formatted.items()}

HEX_TO_NAMES = {value: key for key, value in _formatted.items()}
HEX_TO_NAMES["#00FFFF"] = "cyan / aqua"
HEX_TO_NAMES["#A9A9A9"] = "dark gray"
HEX_TO_NAMES["#2F4F4F"] = "dark slate gray"
HEX_TO_NAMES["#696969"] = "dim gray"
HEX_TO_NAMES["#808080"] = "gray"
HEX_TO_NAMES["#D3D3D3"] = "light gray"
HEX_TO_NAMES["#778899"] = "light slate gray"
HEX_TO_NAMES["#FF00FF"] = "magenta / fuchsia"
HEX_TO_NAMES["#8B008B"] = "dark magenta / dark fuchsia"
HEX_TO_NAMES["#708090"] = "slate gray"
HEX_TO_NAMES["#000080"] = "navy blue"
