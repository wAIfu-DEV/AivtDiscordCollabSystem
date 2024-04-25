import time
import sys
import lib.avdcs as avdcs

def main():
    avdcs.initialize(
        token="<TOKEN>",
        channel_id="<CHANNEL ID>",
        python_path=sys.executable,
        bot_path="lib/collabbot.py")

    while True:
        msg = avdcs.receive_poll()
        if msg == None:
            time.sleep(0.1)
            continue
        if msg.text == "quit": break

        print(msg.sender + ": " + msg.text)
        avdcs.send("Test message", "all")

    avdcs.free()


if __name__ == "__main__":
    main()