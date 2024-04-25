""" 
AiVtDiscordCollabSystem
author: w-AI-fu_DEV
version: 1.0.0

deps:
pip websockets https://pypi.org/project/websockets/
"""

#-------------------------------------------------------------------------------
import subprocess
import sys
import os
import time

import websockets
import websockets.sync
import websockets.sync.client

#-------------------------------------------------------------------------------
class IncomingMessage:
    sender: str = ""
    text: str = "" 

#-------------------------------------------------------------------------------
is_initialized: bool = False
ws: websockets.sync.client.ClientConnection = None
proc: subprocess.Popen = None

#-------------------------------------------------------------------------------
def __connect_websocket()-> None:
    global ws
    ws = websockets.sync.client.connect("ws://127.0.0.1:21896")

#-------------------------------------------------------------------------------
def initialize(token: str, channel_id: str, python_path: str = "python", bot_path: str = "collabbot.py")-> None:
    """
    Run before using any other functions from this package

    `token` Discord bot token

    `channel_id` ID of the discord server text channel

    `python_path` Path to the python executable

    `bot_path` Path to the collabbot.py script
    """
    global proc, ws
    directory = os.path.dirname(os.path.realpath(__file__))
    proc = subprocess.Popen(args=[sys.executable, bot_path],
                            stdout=sys.stdout,
                            stderr=sys.stderr)
    
    while True:
        try:
            __connect_websocket()
            break
        except:
            time.sleep(0.1)
            continue
    
    ws.send(f"#log;{token};{channel_id}")
    while True:
        msg = ws.recv()
        if msg == "#logged":
            return

#-------------------------------------------------------------------------------
def free()-> None:
    """
    Releases the resources allocated to the library
    """
    global ws, proc
    ws.close()
    proc.kill()
    ws = None
    proc = None

#-------------------------------------------------------------------------------
def change_channel(channel_id: str)-> None:
    """
    Change which discord text channel to receive from and send messages to
    """
    global ws
    ws.send(f"#channel;{channel_id}")

#-------------------------------------------------------------------------------
def send(text: str, to: str = "all")-> None:
    """
    Send a message to the text channel
    """
    global ws
    ws.send(f"#send;{to};{text}")

#-------------------------------------------------------------------------------
def receive_poll()-> (IncomingMessage | None):
    """
    Checks for received messages, if no messages have been received returns `None`
    """
    global ws
    result = ""
    while True:
        try:
            result = ws.recv(0)
        except TimeoutError:
            break

    if result == "": return None
    if not result.startswith("#msg"): return None

    split_msg = str(result).split(";")
    msg = IncomingMessage()
    msg.sender = split_msg[1]
    msg.text = ";".join(split_msg[2:])
    return msg