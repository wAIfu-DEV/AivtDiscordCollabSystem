import discord
import asyncio
import sys
import threading
from typing import Callable
import websockets
import websockets.server
import websockets.sync
import websockets.sync.server



# WS DATA FORMAT
#  Received from websocket as client:
#   #msg;<from username>;<string text message>      : Text message that has been sent to the discord text channel
#   #logged                                         : Received when Discord bot has finished loading and can send/receive messages.
#  Sent to websocket as client:
#   #send;<to username | all>;<string text message> : Text message to send to the discord text channel. Specify a username to only send message to a single collab partner, or use all to send it to all collab partners.
#   #log;<token>;<channel id>                       : Send this message to initialize the discord bot.
#   #channel;<channel id>                           : Change discord text channel without reloading the bot.



client: discord.Client = None
CHANNEL_ID: int = 0
channel: discord.TextChannel = None

socket: websockets.sync.server.ServerConnection = None

send_queue: str = ""
send_to: str = "all"

queue: str = ""
callbacks: list[Callable[[str], None]] = []



def run_collab_bot(bot_token: str, channel_id: int|None = None)-> None:
    """
    Run before calling any `receieve_message` or `send_message` functions
    """
    global CHANNEL_ID, client, socket
    CHANNEL_ID = channel_id

    intents = discord.Intents().default()
    intents.message_content = True
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        global channel, send_queue
        if CHANNEL_ID == None:
            print("Channel ID is not set.", file=sys.stderr)
            return
        if channel == None:
            channel = client.get_channel(CHANNEL_ID)
        if channel == None:
            print("Could not send message to channel, please verify the channel ID or that the bot was invited to the server.", file=sys.stderr)
            return
        socket.send("#logged")

        # Polling loop
        # Have to do it that way since client events called by `dispatch` take
        # 20s to be called for some reason.
        while True:
            if send_queue != "":
                await sendcollab(send_queue)
                send_queue = ""
            else:
                await asyncio.sleep(0.1)
    
    @client.event
    async def on_message(message: discord.Message):
        global CHANNEL_ID, client
        if message.channel.id != CHANNEL_ID:
            return
        if message.author == client.user:
            return
        if message.content.startswith("#to;"):
            split_message: list[str] = message.content.split(";")
            to: str = split_message[1]
            if to != "all" and to != client.user.name and to != client.user.display_name:
                return
            text: str = ";".join(split_message[2:])
            socket.send(f"#msg;{message.author.display_name};{text}")
            return
        else:
            socket.send(f"#msg;{message.author.display_name};{message.content}")



    async def sendcollab(text: str, to: str = "all"):
        global client, CHANNEL_ID, channel
        if client == None:
            print("Tried sending message before loading discord bot.", file=sys.stderr)
            return
        await channel.send(f"#to;{to};{text.strip()}")

    client.run(bot_token)



def set_channel_id(channel_id: int)-> None:
    """
    Sets the channel from which to receive or send messages to.
    """
    global CHANNEL_ID, channel
    CHANNEL_ID = channel_id
    if channel == None:
        channel = client.get_channel(CHANNEL_ID)
    if channel == None:
        print("Could not send message to channel, please verify the channel ID or that the bot was invited to the server.", file=sys.stderr)



def start_in_thread(token: str, channel: int):
    run_collab_bot(token, channel)



def handle_wss_message(data: str):
    global send_queue, send_to, client
    split_data = data.split(";")

    if (split_data[0] == "#send"):
        send_to = split_data[1]
        send_queue = ";".join(split_data[2:])
        
    if (split_data[0] == "#log"):
        t = threading.Thread(target=start_in_thread, args=[split_data[1], int(split_data[2])])
        t.start()
    
    if (split_data[0] == "#channel"):
        set_channel_id(split_data[1])



if __name__ == "__main__":
    def wss_handler(ws: websockets.sync.server.ServerConnection):
        global socket
        socket = ws
        while True:
            try:
                msg = ws.recv(0)
            except TimeoutError:
                continue
            handle_wss_message(str(msg))

    with websockets.sync.server.serve(host="127.0.0.1", port=21896, handler=wss_handler) as server:
        server.serve_forever()

