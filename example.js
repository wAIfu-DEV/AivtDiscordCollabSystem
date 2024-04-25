const avdcs = require("./lib/avdcs");

// With event listener
async function main() {
  await avdcs.initialize("<TOKEN>", "<CHANNEL ID>", {
    python_path: "python",
    bot_path: "lib/collabbot.py",
  });
  avdcs.receiveWithListener((msg, from) => {
    if (msg == "quit") {
      avdcs.free();
      process.exit();
    }
    console.log(from + ":", msg);
    avdcs.send("Test message", "all");
  });
}

/*
// With sync polling
async function main() {
    await avdcs.initialize("<TOKEN>", "<CHANNEL ID>", {
      python_path: "python",
      bot_path: "../lib/collabbot.py",
    });
    while (true) {
        let msg = avdcs.receivePoll();
        if (msg == null) {
            await new Promise(resolve => setTimeout(resolve, 50));
            continue;
        }
        if (msg == "quit") {
            avdcs.free();
            process.exit();
        }
        console.log(from + ":", msg);
        avdcs.send("Test message", "all");
    }
}
*/

/*
// With blocking async
async function main() {
    await avdcs.initialize("<TOKEN>", "<CHANNEL ID>", {
      python_path: "python",
      bot_path: "../lib/collabbot.py",
    });
    wile (true) {
        let msg = await avdcs.receiveAsync(undefined);
        if (msg == "quit") {
            avdcs.free();
            process.exit();
        }
        console.log(from + ":", msg);
        avdcs.send("Test message", "all");
    }
}
*/

main();
