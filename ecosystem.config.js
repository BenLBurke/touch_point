// PM2 process config for touch_point.py.
//
// Using this instead of raw `pm2 start` flags so the environment
// variables your hardware actually needs (see README.md's
// Configuration table) survive `pm2 save` / reboots.
//
// Edit the values below to match your board, then:
//   pm2 start ecosystem.config.js
const path = require("path");

module.exports = {
  apps: [
    {
      name: "touch_point",
      script: "touch_point.py",
      interpreter: path.join(__dirname, "venv/bin/python"),
      cwd: __dirname,
      env: {
        TOUCHPOINT_AUDIO_DEVICE: "plughw:0,0",
        TOUCHPOINT_SPECIAL_CARD_ID: "354868069890",
        // TOUCHPOINT_NUM_PIXELS: "46",  // uncomment and set if your ring isn't the default 48
        // TOUCHPOINT_VOLUME: "0.7",     // uncomment to set default playback volume, 0.0-1.0 (default 1.0)
      },
    },
  ],
};
