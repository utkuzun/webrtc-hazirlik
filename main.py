import argparse
import asyncio
import errno
import json
import logging
import os
import platform
import ssl

from aiohttp import web

from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaPlayer, MediaRelay

ROOT = os.path.dirname(__file__)

relay = None
webcam = None


async def on_shutdown(app):
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros)    
    pcs.clear()

def create_local_track(play_from):
    global relay, webcam
    if play_from:
       player = MediaPlayer(play_from)
       return player.audio, player.video
    else:

        options = {"framerate": "30", "video_size": "640x480"}

        if relay is None:
            if platform.system() == "Darwin":
                webcam = MediaPlayer("default:none", format="avfoundation", options=options)
            
            elif platform.system() == "Windows":
                webcam = MediaPlayer("video=Integrated Camera", format="dshow", options=options)
            
            else:
                webcam = MediaPlayer("/dev/video0", format="v4l2", options=options)
            relay = MediaRelay()
        return None, relay.subscribe(webcam.video)

    

async def index(request):
    content = open(os.path.join(ROOT, "index.html"), "r").read()
    return web.Response(content_type="text/html", text=content)


async def javascript(request):
    content = open(os.path.join(ROOT, "index.js"), "r").read()
    return web.Response(content_type="application/javascript", text=content)

async def css(request):
    content = open(os.path.join(ROOT, "main.css"), "r").read()
    return web.Response(content_type="text/css", text=content)


async def offer(request):
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])
    pc = RTCPeerConnection()
    pcs.add(pc)

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        print("Connection state is %s" % pc.connectionState)
        if pc.connectionState == "failed":
            await pc.close()
            pcs.discard(pc)

    audio, video = create_local_track(args.play_from)

    await pc.setRemoteDescription(offer)

    for t in pc.getTransceivers():
        if t.kind == "audio" and audio:
            pc.addTrack(audio)
        elif t.kind == "video" and video:
            pc.addTrack(video)
    
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return web.Response(content_type="application/json", text=json.dumps({"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}))



    # try:

    #     video = create_local_track()

    #     await pc.setRemoteDescription(offer)

    #     pc.addTrack(video)
        
    #     answer = await pc.createAnswer()
    #     await pc.setLocalDescription(answer)

    #     return web.Response(content_type="application/json", text=json.dumps({"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}))

    # except Exception as err:
    #     print(err)
    #     return web.Response(content_type="application/json", text=json.dumps({"msg": "interval server error"}))


pcs = set()

if __name__ == "__main__":
    parser = argparse.ArgumentParser("WebRTC demo")

    parser.add_argument("--host", default="0.0.0.0", help="Host for HTTP server (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8080, help="Port for HTTP server (default: 8080)")
    parser.add_argument("--play-from", help="Read the media from a file and sent it.")

    args = parser.parse_args()

    app = web.Application()
    app.on_shutdown.append(on_shutdown)
    app.router.add_get("/", index)
    app.router.add_get("/index.js", javascript)
    app.router.add_get("/main.css", css)
    app.router.add_post("/offer", offer)
    web.run_app(app, host=args.host)



