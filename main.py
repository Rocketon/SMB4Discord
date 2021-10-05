import discord
import json
from discord.ext import commands
import os
from yt_dlp import YoutubeDL
from asyncio import sleep

from youtube_dl.utils import ExtractorError

YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': 'False'}
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
audio_queue = []


with open('cfg/Config.json') as f:
    config = json.load(f)

token = config.get("token")
prefix = config.get("default_prefix")

client = commands.Bot(command_prefix=prefix)


@client.event
async def on_connect():
    await client.change_presence(
        activity=discord.Activity(type=discord.ActivityType.listening, name=f"{client.command_prefix}help"))
    print('Бот запущен!')


@client.command()
async def play(ctx, arg):
    global voice

    try:
        voice_channel = ctx.message.author.voice.channel
        voice = await voice_channel.connect()
    except:
        print('Уже подключен или не удалось подключиться')

    if voice.is_playing():
        audio_queue.append(arg)
        await ctx.send(f'{ctx.message.author.mention}, добавлено в очередь.')
        await queue(ctx)
    else:
        with YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(arg, download=False)
            print(info)

        URL = info['formats'][0]['url']

        voice.play(discord.FFmpegPCMAudio(executable="app/ffmpeg.exe", source=URL, **FFMPEG_OPTIONS))

        await ctx.message.delete()

        while voice.is_playing():
            await sleep(1)
        if not voice.is_paused():
            try:
                await play(ctx, audio_queue.pop(0))
            except:
                await voice.disconnect()


@client.command()
async def leave(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice.is_connected():
        await voice.disconnect()
    else:
        await ctx.send("Бота нет в голосовом чате.")
    audio_queue.clear()


@client.command()
async def pause(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice.is_playing():
        voice.pause()
    else:
        await ctx.send("Аудио не проигрывается.")


@client.command()
async def resume(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice.is_paused():
        voice.resume()
    else:
        await ctx.send("Аудио не на паузе.")


@client.command()
async def stop(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    voice.stop()
    audio_queue.clear()

@client.command()
async def queue(ctx, quene='', j=1):
    for i in audio_queue:
        with YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(i, download=False)
        quene += f'{j}. {info.get("title", "error")}\n'
        j += 1
    await ctx.send(f'Очередь:\n{quene}', embed=None)


client.run(token)
