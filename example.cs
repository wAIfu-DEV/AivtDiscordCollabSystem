using AiVtDiscordCollabSystem;

namespace Program
{
    internal class MainClass
    {
        public static async Task Main(string[] args)
        {
            await AVDCS.Initialize(
                token: "<TOKEN>",
                channel_id: "<CHANNEL ID>",
                python_path: "python",
                bot_path: "lib/collabbot.py");

            while (true)
            {
                AVDCS.IncomingMessage msg = await AVDCS.Receive();
                if (msg.text.Equals("quit")) break;

                Console.WriteLine(msg.sender + ": " + msg.text);
                await AVDCS.Send("This is a test", "all");
            }
            await AVDCS.Free();
        }
    }
}
