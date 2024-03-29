#!/usr/bin/env python3

from discord.ext import commands
import asyncio
import itertools
import math
import random

import discord
import youtube_dl
from async_timeout import timeout
from functools import partial
from . import utils

# Silence useless bug reports messages
youtube_dl.utils.bug_reports_message = lambda: ""


class VoiceError(Exception):
    pass


class YTDLError(Exception):
    pass


class YTDLSource(discord.PCMVolumeTransformer):
    YTDL_OPTIONS = {
        "format": "bestaudio/best",
        "extractaudio": True,
        "audioformat": "mp3",
        "outtmpl": "downloads/%(extractor)s-%(id)s-%(title)s.mp3",
        "restrictfilenames": True,
        "noplaylist": True,
        "nocheckcertificate": True,
        "ignoreerrors": False,
        "logtostderr": False,
        "quiet": True,
        "no_warnings": True,
        "default_search": "auto",
        "source_address": "0.0.0.0",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192"
        }]
    }

    FFMPEG_OPTIONS = {
        "options": "-vn",
    }

    ytdl = youtube_dl.YoutubeDL(YTDL_OPTIONS)

    def __init__(self, ctx: commands.Context, source: discord.FFmpegPCMAudio, *, data: dict, volume: float = 0.5):
        super().__init__(source, volume)

        self.requester = ctx.author
        self.channel = ctx.channel
        self.data = data

        self.uploader = data.get("uploader")
        self.uploader_url = data.get("uploader_url")
        date = data.get("upload_date")
        try: self.upload_date = date[6:8] + "." + date[4:6] + "." + date[0:4]
        except: self.upload_date = "Unknown"
        self.title = data.get("title")
        self.thumbnail = data.get("thumbnail")
        self.description = data.get("description")
        self.duration = self.parse_duration(int(data.get("duration")))
        self.tags = data.get("tags")
        self.url = data.get("webpage_url")
        self.views = data.get("view_count")
        self.likes = data.get("like_count")
        self.dislikes = data.get("dislike_count")
        self.stream_url = data.get("url")

    def __str__(self):
        return "**{0.title}** by **{0.uploader}**".format(self)

    @classmethod
    async def create_source(cls, ctx: commands.Context, search: str, *, loop: asyncio.BaseEventLoop = None):
        loop = loop or asyncio.get_event_loop()
        to_run = partial(cls.ytdl.extract_info, search, download=False)
        data = await loop.run_in_executor(None, to_run)

        if data is None:
            raise YTDLError("Couldn't find anything that matches `{}`".format(search))

        if "entries" not in data:
            process_info = data
        else:
            process_info = None
            for entry in data["entries"]:
                if entry:
                    process_info = entry
                    break

            if process_info is None:
                raise YTDLError("Couldn't find anything that matches `{}`".format(search))

        webpage_url = process_info["webpage_url"]
        to_run = partial(cls.ytdl.extract_info, webpage_url, download=False)
        processed_info = await loop.run_in_executor(None, to_run)

        if processed_info is None:
            raise YTDLError("Couldn't fetch `{}`".format(webpage_url))

        if "entries" not in processed_info:
            info = processed_info
        else:
            info = None
            while info is None:
                try:
                    info = processed_info["entries"].pop(0)
                except IndexError:
                    raise YTDLError("Couldn't retrieve any matches for `{}`".format(webpage_url))

        return cls(ctx, discord.FFmpegPCMAudio(info["url"], **cls.FFMPEG_OPTIONS), data=info)

    @staticmethod
    def parse_duration(duration: int):
        minutes, seconds = divmod(duration, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)

        duration = []
        if days > 0:
            duration.append("{} days".format(days))
        if hours > 0:
            duration.append("{} hours".format(hours))
        if minutes > 0:
            duration.append("{} minutes".format(minutes))
        if seconds > 0:
            duration.append("{} seconds".format(seconds))

        return ", ".join(duration)


class Song:
    __slots__ = ("source", "requester")

    def __init__(self, source: YTDLSource):
        self.source = source
        self.requester = source.requester

    def create_embed(self):
        embed = (discord.Embed(title="Now playing",
                               description="```\n{0.source.title}\n```".format(self),
                               color=discord.Color.blurple())
                 .add_field(name="Duration", value=self.source.duration)
                 .add_field(name="Requested by", value=self.requester.mention)
                 .add_field(name="Uploader", value="[{0.source.uploader}]({0.source.uploader_url})".format(self))
                 .add_field(name="URL", value="[Click]({0.source.url})".format(self))
                 .set_thumbnail(url=self.source.thumbnail))

        return embed


class SongQueue(asyncio.Queue):
    def __getitem__(self, item):
        if isinstance(item, slice):
            return list(itertools.islice(self._queue, item.start, item.stop, item.step))
        else:
            return self._queue[item]

    def __iter__(self):
        return self._queue.__iter__()

    def __len__(self):
        return self.qsize()

    def clear(self):
        self._queue.clear()

    def shuffle(self):
        random.shuffle(self._queue)

    def remove(self, index: int):
        del self._queue[index]


class VoiceState:
    def __init__(self, bot: commands.Bot, ctx: commands.Context):
        self.bot = bot
        self._ctx = ctx

        self.current = None
        self.voice = None
        self.next = asyncio.Event()
        self.songs = SongQueue()

        self._loop = False
        self._volume = 0.5
        self.skip_votes = set()

        self.audio_player = bot.loop.create_task(self.audio_player_task())

    def __del__(self):
        self.audio_player.cancel()

    @property
    def loop(self):
        return self._loop

    @loop.setter
    def loop(self, value: bool):
        self._loop = value

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value: float):
        self._volume = value

    @property
    def is_playing(self):
        return self.voice and self.current

    async def audio_player_task(self):
        while True:
            self.next.clear()

            if not self.loop:
                # Try to get the next song within 5 minutes.
                # If no song will be added to the queue in time,
                # the player will disconnect due to performance
                # reasons.
                try:
                    async with timeout(300): # 5 minutes
                        self.current = await self.songs.get()
                except asyncio.TimeoutError:
                    self.bot.loop.create_task(self.stop())
                    return

            self.current.source.volume = self._volume
            self.voice.play(self.current.source, after=self.play_next_song)
            await self.current.source.channel.send(embed=self.current.create_embed())

            await self.next.wait()

    def play_next_song(self, error=None):
        if error:
            raise VoiceError(str(error))

        self.next.set()

    def skip(self):
        self.skip_votes.clear()

        if self.is_playing:
            self.voice.stop()

    async def stop(self):
        self.songs.clear()

        if self.voice:
            await self.voice.disconnect()
            self.voice = None


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_states = {}

    def get_voice_state(self, ctx: commands.Context):
        state = self.voice_states.get(ctx.guild.id)
        if not state:
            state = VoiceState(self.bot, ctx)
            self.voice_states[ctx.guild.id] = state

        return state

    def cog_unload(self):
        for state in self.voice_states.values():
            self.bot.loop.create_task(state.stop())

    def cog_check(self, ctx: commands.Context):
        if not ctx.guild:
            raise commands.NoPrivateMessage("This command can't be used in DM channels.")

        return True

    async def cog_before_invoke(self, ctx: commands.Context):
        ctx.voice_state = self.get_voice_state(ctx)

    def get_number_of_members(self, channel: discord.VoiceChannel):
        counter = 0
        for member in channel.members:
            if not member.bot:
                counter += 1
        return counter
    
    @commands.command(name="join", aliases=["summon", "connect"])
    async def _join(self, ctx: commands.Context):
        """Joins a voice channel."""
        destination = ctx.author.voice.channel
        try:
            ctx.voice_state.voice = await destination.connect()
        except discord.ClientException:
            await ctx.send(":point_right: **I am already connected to the **`{}`** voice channel!**".format(destination.name))
            raise utils.SilentError
        await ctx.send(utils.CustomEmojis.GreenCheck + " **Successfully joined the **`{}`** voice channel!**".format(destination.name))

    @commands.command(name="leave", aliases=["disconnect"])
    @commands.has_permissions(manage_guild=True)
    async def _leave(self, ctx: commands.Context):
        """Clears the queue and leaves the voice channel."""

        if not ctx.voice_state.voice:
            return await ctx.send("Not connected to any voice channel.")

        await ctx.voice_state.stop()
        del self.voice_states[ctx.guild.id]

    @commands.command(name="volume")
    async def _volume(self, ctx: commands.Context, *, volume=None):
        """Sets the volume of the player."""

        if not ctx.voice_state.is_playing:
            return await ctx.send("Nothing being played at the moment.")
        
        sourcevolume = ctx.voice_state.volume
        
        if not volume:
            if sourcevolume:
                await ctx.send(":point_right: Volume has been set to **{}%**.".format(int(sourcevolume*100)))
                return
            await ctx.send(":point_right: **Volume has been disabled!**")
            return
        
        if volume.lower() in ("mute", "muted", "min", "minimum"):
            volume = 0
        elif volume.lower() in ("normal", "default", "standart", "basic"):
            volume = 100
        elif volume.lower() in ("max", "maximum"):
            volume = 200
        elif volume.lower() == "up":
            volume = sourcevolume*100 + 10
        elif volume.lower() == "down":
            volume = sourcevolume*100 - 10
        else:
            try:
                volume = int(volume.strip("%"))
            except ValueError:
                await ctx.send(":point_right: **Error: volume must be an integer!**")
                raise utils.SilentError
            if volume < 0:
                await ctx.send(":point_right: **Error: volume must be a non-negative integer!**")
                raise utils.SilentError
            if volume > 200:
                volume = 200
        
        ctx.voice_state.volume = volume / 100
        if volume:
            await ctx.guild.change_voice_state(channel=ctx.voice_client.channel)
        else:
            await ctx.guild.change_voice_state(channel=ctx.voice_client.channel, self_mute=True)
        await ctx.send(utils.CustomEmojis.GreenCheck + " Successfully changed volume to **{}%**.".format(volume))

    @commands.command(name="now", aliases=["current", "playing"])
    async def _now(self, ctx: commands.Context):
        """Displays the currently playing song."""

        await ctx.send(embed=ctx.voice_state.current.create_embed())

    @commands.command(name="pause")
    @commands.has_permissions(manage_guild=True)
    async def _pause(self, ctx: commands.Context):
        """Pauses the currently playing song."""

        if not ctx.voice_state.is_playing and ctx.voice_state.voice.is_playing():
            ctx.voice_state.voice.pause()
            await ctx.message.add_reaction("⏯")

    @commands.command(name="resume")
    @commands.has_permissions(manage_guild=True)
    async def _resume(self, ctx: commands.Context):
        """Resumes a currently paused song."""

        if not ctx.voice_state.is_playing and ctx.voice_state.voice.is_paused():
            ctx.voice_state.voice.resume()
            await ctx.message.add_reaction("⏯")

    @commands.command(name="stop")
    @commands.has_permissions(manage_guild=True)
    async def _stop(self, ctx: commands.Context):
        """Stops playing song and clears the queue."""

        ctx.voice_state.songs.clear()

        if not ctx.voice_state.is_playing:
            ctx.voice_state.voice.stop()
            await ctx.message.add_reaction("⏹")

    @commands.command(name="skip")
    async def _skip(self, ctx: commands.Context):
        """Vote to skip a song. The requester can automatically skip.
        3 skip votes are needed for the song to be skipped.
        """

        if not ctx.voice_state.is_playing:
            return await ctx.send("Not playing any music right now...")
        
        number_members = self.get_number_of_members(ctx.voice_state.voice.channel)
        if (number_members == 1):
            ctx.voice_state.skip()
            await ctx.send(":track_next: **Music skipped.**")
            return
        
        voter = ctx.message.author
        if voter == ctx.voice_state.current.requester:
            ctx.voice_state.skip()
            await ctx.send(":track_next: **Music skipped by the requester.**")
            return
        
        if voter.permissions_in(ctx.voice_state.voice.channel).move_members:
            ctx.voice_state.skip()
            await ctx.send(":track_next: **Music skipped by a DJ.**")
            return
        
        if voter.id in ctx.voice_state.skip_votes:
            await ctx.send(":point_right: **You have already voted to skip this music.**")
            return
        
        ctx.voice_state.skip_votes.add(voter.id)
        total_votes = len(ctx.voice_state.skip_votes)
        number_members = min(number_members, 3)

        if total_votes < number_members:
            await ctx.send("{} Skip vote added, currently at **{}/{}**".format(utils.CustomEmojis.GreenCheck, total_votes, number_members))
            return
        
        ctx.voice_state.skip()
        await ctx.send(":track_next: **Music skipped by voting.**")


    @commands.command(name="queue")
    async def _queue(self, ctx: commands.Context, *, page: int = 1):
        """Shows the player"s queue.
        You can optionally specify the page to show. Each page contains 10 elements.
        """

        if not len(ctx.voice_state.songs):
            return await ctx.send("Empty queue.")

        items_per_page = 10
        pages = math.ceil(len(ctx.voice_state.songs) / items_per_page)

        start = (page - 1) * items_per_page
        end = start + items_per_page

        queue = ""
        for i, song in enumerate(ctx.voice_state.songs[start:end], start=start):
            queue += "`{0}.` [**{1.source.title}**]({1.source.url})\n".format(i + 1, song)

        embed = (discord.Embed(description="**{} tracks:**\n\n{}".format(len(ctx.voice_state.songs), queue))
                 .set_footer(text="Viewing page {}/{}".format(page, pages)))
        await ctx.send(embed=embed)

    @commands.command(name="shuffle")
    async def _shuffle(self, ctx: commands.Context):
        """Shuffles the queue."""

        if len(ctx.voice_state.songs) == 0:
            return await ctx.send("Empty queue.")

        ctx.voice_state.songs.shuffle()
        await ctx.message.add_reaction("✅")

    @commands.command(name="remove")
    async def _remove(self, ctx: commands.Context, index: int):
        """Removes a song from the queue at a given index."""

        if len(ctx.voice_state.songs) == 0:
            return await ctx.send("Empty queue.")

        ctx.voice_state.songs.remove(index - 1)
        await ctx.message.add_reaction("✅")

    @commands.command(name="loop")
    async def _loop(self, ctx: commands.Context):
        """Loops the currently playing song.
        Invoke this command again to unloop the song.
        """

        if not ctx.voice_state.is_playing:
            return await ctx.send("Nothing being played at the moment.")

        # Inverse boolean value to loop and unloop.
        ctx.voice_state.loop = not ctx.voice_state.loop
        await ctx.message.add_reaction("✅")

    @commands.command(name="play")
    async def _play(self, ctx: commands.Context, *, search: str):
        """Plays a song.
        If there are songs in the queue, this will be queued until the
        other songs finished playing.
        This command automatically searches from various sites if no URL is provided.
        A list of these sites can be found here: https://rg3.github.io/youtube-dl/supportedsites.html
        """

        if not ctx.voice_state.voice:
            await ctx.invoke(self._join)

        async with ctx.typing():
            try:
                source = await YTDLSource.create_source(ctx, search, loop=self.bot.loop)
            except YTDLError as e:
                await ctx.send("An error occurred while processing this request: {}".format(str(e)))
            else:
                song = Song(source)

                await ctx.voice_state.songs.put(song)
                await ctx.send("Enqueued {}".format(str(source)))

    @_join.before_invoke
    @_play.before_invoke
    async def check_before_join(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            raise utils.SpecialError(":point_right: **Error: you are not connected to any voice channel!**")

        if ctx.author.voice.afk:
            raise utils.SpecialError(":point_right: **Error: cannot connect to AFK channel!**")

        if ctx.voice_client and ctx.voice_client.channel != ctx.author.voice.channel:
            raise utils.SpecialError(":point_right: **Error: I am already connected in another voice channel!**")
    
    @_skip.before_invoke
    async def check_before_cmds(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            raise utils.SpecialError(":point_right: **Error: you are not connected to any voice channel!**")

        if not ctx.voice_client:
            raise utils.SpecialError(":point_right: **Error: I am not connected to any voice channel!**")

        if ctx.voice_client.channel != ctx.author.voice.channel:
            raise utils.SpecialError(":point_right: **Error: I am connected in another voice channel!**")


def setup(bot):
    bot.add_cog(Music(bot))