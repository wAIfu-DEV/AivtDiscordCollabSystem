/**
 * @name AiVtDiscordCollabSystem
 * @author w-AI-fu_DEV
 * @version 1.0.0
 *
 * Deps: none
 */

using System.Diagnostics;
using System.Net.WebSockets;
using System.Text;

namespace AiVtDiscordCollabSystem
{
    public class AVDCS
    {
        //----------------------------------------------------------------------
        static public ClientWebSocket? ws = null;
        static public Process? proc = null;

        //----------------------------------------------------------------------
        public struct IncomingMessage
        {
            public string sender;
            public string text;
        }

        //----------------------------------------------------------------------
        private static async Task ConnectWebsocket()
        {
            ws = new ClientWebSocket();
            Uri uri = new Uri("ws://127.0.0.1:21896");
            await ws.ConnectAsync(uri, CancellationToken.None);
        }

        //----------------------------------------------------------------------
        private static async Task SendString(ClientWebSocket socket, string payload)
        {
            byte[] bytes = Encoding.UTF8.GetBytes(payload);
            ArraySegment<byte> segment = new ArraySegment<byte>(bytes, 0, bytes.Length);
            await ws!.SendAsync(segment, WebSocketMessageType.Text, true, CancellationToken.None);
        }

        //----------------------------------------------------------------------
        private static async Task<string> ReceiveString(ClientWebSocket socket)
        {
            WebSocketReceiveResult result;
            string receivedMessage = "";
            var message = new ArraySegment<byte>(new byte[4096]);
            do
            {
                result = await socket.ReceiveAsync(message, CancellationToken.None);
                if (result.MessageType != WebSocketMessageType.Text)
                    break;
                var messageBytes = message.Skip(message.Offset).Take(result.Count).ToArray();
                receivedMessage += Encoding.UTF8.GetString(messageBytes);
            }
            while (!result.EndOfMessage);
            return receivedMessage;
        }

        //----------------------------------------------------------------------
        /// <summary>
        /// Run before using any other functions from this package
        /// </summary>
        /// <param name="token">Token of the Discord bot.</param>
        /// <param name="channel_id">ID of the channel to send and receive messages to.</param>
        /// <param name="python_path">Path to the python process, defaults to `python`. Change this if you are using a venv.</param>
        /// <param name="bot_path">Path to the `collabbot.py` script.</param>
        /// <returns></returns>
        public static async Task Initialize(
            string token,
            string channel_id,
            string python_path = "python",
            string bot_path = "collabbot.py")
        {
            proc = new Process();
            proc.StartInfo.FileName = python_path;
            proc.StartInfo.ArgumentList.Add(bot_path);
            proc.Start();

            while (true)
            {
                try
                {
                    await ConnectWebsocket();
                    break;
                }
                catch (Exception)
                {
                    await Task.Delay(50);
                    continue;
                }
            }

            await SendString(ws!, $"#log;{token};{channel_id}");

            while (true)
            {
                string logged = await ReceiveString(ws!);
                if (logged.Equals("#logged")) break;
            }
        }

        //----------------------------------------------------------------------
        /// <summary>
        /// Release ressources allocated for the library
        /// </summary>
        /// <returns></returns>
        public static async Task Free()
        {
            await ws!.CloseAsync(WebSocketCloseStatus.NormalClosure, "", CancellationToken.None);
            proc!.Kill();

            ws = null;
            proc = null;
        }

        //----------------------------------------------------------------------
        /// <summary>
        /// Change the Discord text channel to receive from and send to.
        /// </summary>
        /// <param name="channel_id">ID of the Discord text channel to switch to</param>
        /// <returns></returns>
        public static async Task ChangeChannel(string channel_id)
        {
            await SendString(ws!, $"#channel;{channel_id}");
        }

        //----------------------------------------------------------------------
        /// <summary>
        /// Send a message to the collab discord channel
        /// </summary>
        /// <param name="text">Content of the message to send to the collab partner</param>
        /// <param name="to">Name of the collab partner's bot (either DisplayName or Name). Set to "all" to send to all collab partners.</param>
        /// <returns></returns>
        public static async Task Send(string text, string to = "all")
        {
            await SendString(ws!, $"#send;{to};{text}");
        }

        //----------------------------------------------------------------------
        /// <summary>
        /// Awaits for a response from one of the collab partners.
        /// </summary>
        /// <returns></returns>
        public static async Task<IncomingMessage> Receive()
        {
            string result = await ReceiveString(ws!);
            string[] split_data = result.Split(";");

            IncomingMessage msg = new IncomingMessage();
            msg.sender = split_data[1];
            msg.text = String.Join(";", split_data.Skip(2).Take(split_data.Length - 2).ToArray());
            return msg;
        }
    }
}


