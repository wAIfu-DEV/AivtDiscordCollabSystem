"use strict";
/**
 * @name AiVtDiscordCollabSystem
 * @author w-AI-fu_DEV
 * @version 1.0.0
 *
 * Deps:
 * npm ws https://www.npmjs.com/package/ws
 */

//------------------------------------------------------------------------------
const cproc = require("child_process");
const WebSocket = require("ws");

//------------------------------------------------------------------------------
/** @type { boolean } */
exports.is_initialized = false;
/** @type { Array<(msg: string, from: string) => any> } */
let listeners = [];
/** @type { Array<(msg: string, from: string) => any> } */
let temp_listeners = [];
let in_queue = "";
let in_queue_sender = "";
/** @type { WebSocket | undefined } */
let ws = undefined;
/** @type { cproc.ChildProcess | undefined } */
let proc = undefined;

//------------------------------------------------------------------------------
/**
 * @returns { Promise<void> }
 */
function connectWebsocket(token, channel_id) {
  ws = new WebSocket("ws://127.0.0.1:21896");

  ws.onerror = (err) => {
    setImmediate(() => {
      connectWebsocket(token, channel_id);
    });
  };

  ws.onopen = () => {
    ws.onmessage = (ev) => {
      let data = String(ev.data);

      if (data == "#logged") {
        exports.is_initialized = true;
        exports.onLoaded();
        return;
      }

      if (data.startsWith("#msg")) {
        /** @type { string[] } */
        let split_data = data.split(";");
        let username = split_data[1];
        let text = split_data.slice(2, undefined).join(";");

        in_queue = text;
        in_queue_sender = username;
        for (let listener of temp_listeners) {
          listener(text, username);
        }
        temp_listeners = [];
        for (let listener of listeners) {
          listener(text, username);
        }
      }
    };
    ws.send(`#log;${token};${channel_id}`);
  };
}

//------------------------------------------------------------------------------
/**
 * Run before using any other functions from this package
 * @param { string } token Token of the Discord bot.
 * @param { string } channel_id ID of the channel to send and receive messages to.
 * @param { string } args.python_path Path to the python process, defaults to `python`. Change this if you are using a venv.
 * @param { string } args.bot_path Path to the `collabbot.py` script.
 * @returns { Promise<void> }
 */
exports.initialize = async function (
  token,
  channel_id,
  args = {
    python_path: "python",
    bot_path: "collabbot.py",
  }
) {
  proc = cproc.spawn(args.python_path ?? "python", [
    args.bot_path ?? "collabbot.py",
  ]);
  proc.stdout.on("data", (chunk) => {
    console.log(chunk.toString());
  });
  proc.stderr.on("data", (chunk) => {
    console.log(chunk.toString());
  });
  connectWebsocket(token, channel_id);
  while (true) {
    if (ws.readyState == ws.OPEN) return;
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
};

//------------------------------------------------------------------------------
/**
 * Release ressources allocated for the library
 */
exports.free = function () {
  ws.removeAllListeners();
  ws.close();
  proc.kill(2);
  ws = undefined;
  proc = undefined;
};

//------------------------------------------------------------------------------
/**
 * Change the Discord text channel to receive from and send to.
 * @param { string } channel_id ID of the Discord text channel to switch to
 * @returns
 */
exports.changeChannel = function (channel_id) {
  if (ws.readyState != ws.OPEN) {
    console.warn(
      "Failed to change channel, connection to discord bot is lost."
    );
    return;
  }
  ws.send(`#channel;${channel_id}`);
};

//------------------------------------------------------------------------------
/**
 * Send a message to the collab discord channel
 * @param { string } text Content of the message to send to the collab partner
 * @param { string | "all" } to Name of the collab partner's bot (either DisplayName or Name). Set to "all" to send to all collab partners.
 */
exports.send = function (text, to = "all") {
  if (ws.readyState != ws.OPEN) {
    console.warn(
      "Failed to send message to collab partner, connection to discord bot is lost."
    );
    return;
  }
  ws.send(`#send;${to};${text}`);
};

//------------------------------------------------------------------------------
/**
 * Removes all listeners added via "WithListener" functions.
 */
exports.removeAllListeners = function () {
  listeners = [];
};

//------------------------------------------------------------------------------
/**
 * Callback function will be called everytime a message is received
 * @param { (msg: string, from: string) => any } listener
 */
exports.receiveWithListener = function (listener) {
  listeners.push(listener);
};

//------------------------------------------------------------------------------
/**
 * Awaits for a response from the collab partner, rejects the Promise if takes longer than `timeout_ms`
 *
 * Promise rejection throws an Error when using the `await` keyword.
 * @param { number | undefined } timeout_ms Timeout in milliseconds, leave as undefined for no timeout
 * @returns { Promise<{ text: string, sender: string }> }
 */
exports.receiveAsync = function (timeout_ms = undefined) {
  return new Promise((resolve, reject) => {
    let is_resolved = false;
    temp_listeners.push((msg, username) => {
      if (is_resolved) return;
      is_resolved = true;
      resolve({
        text: msg,
        sender: username,
      });
    });
    if (timeout_ms) {
      setTimeout(() => {
        if (is_resolved) return;
        is_resolved = true;
        reject("timeout");
      }, timeout_ms);
    }
  });
};

//------------------------------------------------------------------------------
/**
 * Syncronous polling version of `receiveAsync` and `receiveWithListener`
 *
 * Returns a string if a message has been received, or null if none has been received yet.
 * @returns { { text: string, sender: string } | null }
 */
exports.receivePoll = function () {
  if (in_queue == "") return null;
  let tmp = in_queue;
  in_queue = "";
  return {
    text: tmp,
    sender: in_queue_sender,
  };
};

//------------------------------------------------------------------------------
/**
 * Called when the discord bot has finished loading, overwrite this function to add your own logic.
 */
exports.onLoaded = () => {};
