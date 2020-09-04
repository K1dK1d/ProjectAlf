# Copyright (C) 2020 Aidil Aryanto.
# DeeezLoad Ported from UniBorg by AnggaR96s
# All rights reserved.

import asyncio
import glob
import os
import shutil
import time

import deezloader
import requests
from bs4 import BeautifulSoup
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from pylast import User
from telethon import events
from telethon.errors.rpcerrorlist import YouBlockedUserError
from telethon.tl.types import DocumentAttributeAudio, DocumentAttributeVideo

from userbot import (
    CMD_HELP,
    DEEZER_ARL_TOKEN,
    LASTFM_USERNAME,
    TEMP_DOWNLOAD_DIRECTORY,
    bot,
    lastfm,
)
from userbot.events import register
from userbot.utils import progress

# For getvideosong


def getmusicvideo(cat):
    search = cat
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
    }
    html = requests.get(
        "https://www.youtube.com/results?search_query=" + search, headers=headers
    ).text
    soup = BeautifulSoup(html, "html.parser")
    for link in soup.find_all("a"):
        if "/watch?v=" in link.get("href"):
            # May change when Youtube Website may get updated in the future.
            video_link = link.get("href")
            break
    video_link = "http://www.youtube.com/" + video_link
    command = 'youtube-dl -f "[filesize<50M]" --merge-output-format mp4 ' + video_link
    os.system(command)


@register(outgoing=True, pattern=r"^\.netease (?:(now)|(.*) - (.*))")
async def _(event):
    if event.fwd_from:
        return
    if event.pattern_match.group(1) == "now":
        playing = User(LASTFM_USERNAME, lastfm).get_now_playing()
        if playing is None:
            return await event.edit("`Error: No current scrobble found.`")
        artist = playing.get_artist()
        song = playing.get_title()
    else:
        artist = event.pattern_match.group(2)
        song = event.pattern_match.group(3)
    track = str(artist) + " - " + str(song)
    chat = "@WooMaiBot"
    link = f"/netease {track}"
    await event.edit("`Searching...`")
    try:
        async with bot.conversation(chat) as conv:
            await asyncio.sleep(2)
            await event.edit("`Processing... Please wait`")
            try:
                msg = await conv.send_message(link)
                response = await conv.get_response()
                respond = await conv.get_response()
                await bot.send_read_acknowledge(conv.chat_id)
            except YouBlockedUserError:
                await event.reply("`Please unblock @WooMaiBot and try again`")
                return
            await event.edit("`Sending Your Music...`")
            await asyncio.sleep(3)
            await bot.send_file(event.chat_id, respond)
        await event.client.delete_messages(
            conv.chat_id, [msg.id, response.id, respond.id]
        )
        await event.delete()
    except TimeoutError:
        return await event.edit(
            "`Error: `@WooMaiBot` is not responding or Song not found!.`"
        )


@register(outgoing=True, pattern=r"^\.vsong(?: |$)(.*)")
async def _(event):
    reply_to_id = event.message.id
    if event.reply_to_msg_id:
        reply_to_id = event.reply_to_msg_id
    reply = await event.get_reply_message()
    if event.pattern_match.group(1):
        query = event.pattern_match.group(1)
        await event.edit("`Wait..! I am finding your videosong..`")
    elif reply.message:
        query = reply.message
        await event.edit("`Wait..! I am finding your videosong..`")
    else:
        await event.edit("`What I am Supposed to find?`")
        return
    getmusicvideo(query)
    l = glob.glob(("*.mp4")) + glob.glob(("*.mkv")) + glob.glob(("*.webm"))
    if l:
        await event.edit("`Yeah..! i found something..`")
    else:
        await event.edit(f"Sorry..! i can't find anything with `{query}`")
    loa = l[0]
    metadata = extractMetadata(createParser(loa))
    duration = 0
    width = 0
    height = 0
    if metadata.has("duration"):
        duration = metadata.get("duration").seconds
    if metadata.has("width"):
        width = metadata.get("width")
    if metadata.has("height"):
        height = metadata.get("height")
    await event.edit("`Uploading video.. Please wait..`")
    os.system("cp *mp4 thumb.mp4")
    os.system("ffmpeg -i thumb.mp4 -vframes 1 -an -s 480x360 -ss 5 thumb.jpg")
    thumb_image = "thumb.jpg"
    c_time = time.time()
    await event.client.send_file(
        event.chat_id,
        loa,
        force_document=False,
        thumb=thumb_image,
        allow_cache=False,
        caption=query,
        supports_streaming=True,
        reply_to=reply_to_id,
        attributes=[
            DocumentAttributeVideo(
                duration=duration,
                w=width,
                h=height,
                round_message=False,
                supports_streaming=True,
            )
        ],
        progress_callback=lambda d, t: asyncio.get_event_loop().create_task(
            progress(d, t, event, c_time, "[UPLOAD]", loa)
        ),
    )
    await event.delete()
    os.remove(thumb_image)
    os.system("rm -rf *.mkv")
    os.system("rm -rf *.mp4")
    os.system("rm -rf *.webm")


@register(outgoing=True, pattern=r"^\.smd(?: |$)(.*)")
async def _(event):
    if event.fwd_from:
        return
    link = event.pattern_match.group(1)
    chat = "@SpotifyMusicDownloaderBot"
    await event.edit("```Getting Your Music```")
    async with bot.conversation(chat) as conv:
        await asyncio.sleep(2)
        await event.edit("`Downloading music taking some times,  Stay Tuned.....`")
        try:
            response = conv.wait_event(
                events.NewMessage(incoming=True, from_users=752979930)
            )
            msg = await bot.send_message(chat, link)
            respond = await response
            res = conv.wait_event(
                events.NewMessage(incoming=True, from_users=752979930)
            )
            r = await res
            await bot.send_read_acknowledge(conv.chat_id)
        except YouBlockedUserError:
            await event.reply(
                "```Please unblock @SpotifyMusicDownloaderBot and try again```"
            )
            return
        await bot.forward_messages(event.chat_id, respond.message)
    await event.client.delete_messages(conv.chat_id, [msg.id, r.id, respond.id])
    await event.delete()


@register(outgoing=True, pattern=r"^\.deez (.+?|) (FLAC|MP3\_320|MP3\_256|MP3\_128)")
async def _(event):
    if event.fwd_from:
        return

    strings = {
        "name": "DeezLoad",
        "arl_token_cfg_doc": "ARL Token for Deezer",
        "invalid_arl_token": "please set the required variables for this module",
        "wrong_cmd_syntax": "bruh, now i think how far should we go. please terminate my Session 🥺",
        "server_error": "We're experiencing technical difficulties.",
        "processing": "`Downloading..`",
        "uploading": "`Uploading...`",
    }

    ARL_TOKEN = DEEZER_ARL_TOKEN

    if ARL_TOKEN is None:
        await event.edit(strings["invalid_arl_token"])
        return

    try:
        loader = deezloader.Login(ARL_TOKEN)
    except Exception as er:
        await event.edit(str(er))
        return

    temp_dl_path = os.path.join(TEMP_DOWNLOAD_DIRECTORY, str(time.time()))
    if not os.path.exists(temp_dl_path):
        os.makedirs(temp_dl_path)

    required_link = event.pattern_match.group(1)
    required_qty = event.pattern_match.group(2)

    await event.edit(strings["processing"])

    if "spotify" in required_link:
        if "track" in required_link:
            required_track = loader.download_trackspo(
                required_link,
                output=temp_dl_path,
                quality=required_qty,
                recursive_quality=True,
                recursive_download=True,
                not_interface=True,
            )
            await event.edit(strings["uploading"])
            await upload_track(required_track, event)
            shutil.rmtree(temp_dl_path)
            await event.delete()

        elif "album" in required_link:
            reqd_albums = loader.download_albumspo(
                required_link,
                output=temp_dl_path,
                quality=required_qty,
                recursive_quality=True,
                recursive_download=True,
                not_interface=True,
                zips=False,
            )
            for required_track in reqd_albums:
                await event.edit(strings["uploading"])
                await upload_track(required_track, event)
            shutil.rmtree(temp_dl_path)
            await event.delete()

    elif "deezer" in required_link:
        if "track" in required_link:
            required_track = loader.download_trackdee(
                required_link,
                output=temp_dl_path,
                quality=required_qty,
                recursive_quality=True,
                recursive_download=True,
                not_interface=True,
            )
            await upload_track(required_track, event)
            await event.edit(strings["uploading"])
            shutil.rmtree(temp_dl_path)
            await event.delete()

        elif "album" in required_link:
            reqd_albums = loader.download_albumdee(
                required_link,
                output=temp_dl_path,
                quality=required_qty,
                recursive_quality=True,
                recursive_download=True,
                not_interface=True,
                zips=False,
            )
            for required_track in reqd_albums:
                await event.edit(strings["uploading"])
                await upload_track(required_track, event)
            shutil.rmtree(temp_dl_path)
            await event.delete()

    else:
        await event.edit(strings["wrong_cmd_syntax"])


async def upload_track(track_location, message):
    metadata = extractMetadata(createParser(track_location))
    duration = 0
    title = ""
    performer = ""
    if metadata.has("duration"):
        duration = metadata.get("duration").seconds
    if metadata.has("title"):
        title = metadata.get("title")
    if metadata.has("artist"):
        performer = metadata.get("artist")
    document_attributes = [
        DocumentAttributeAudio(
            duration=duration,
            voice=False,
            title=title,
            performer=performer,
            waveform=None,
        )
    ]
    supports_streaming = True
    force_document = False
    caption_rts = os.path.basename(track_location)
    await message.client.send_file(
        message.chat_id,
        track_location,
        caption=caption_rts,
        force_document=force_document,
        supports_streaming=supports_streaming,
        allow_cache=False,
        attributes=document_attributes,
    )
    os.remove(track_location)


CMD_HELP.update(
    {
        "getmusic": ">`.netease <Artist - Song Title>`"
        "\nUsage: Download music with @WooMaiBot"
        "\n\n>`.netease now`"
        "\nUsage: Download current LastFM scrobble use `@WooMaiBot`."
        "\n\n>`.vsong` **Artist - Song Title**"
        "\nUsage: Finding and uploading videoclip."
        "\n\n>`.smd <Artist - Song Title>`"
        "\nUsage: Download music from Spotify"
        "\n\n>`.deez <spotify/deezer link> FORMAT`"
        "\nUsage: Download music from deezer."
        "\n*Format : `FLAC`, `MP3_320`, `MP3_256`, `MP3_128`."
    }
)
