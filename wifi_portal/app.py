"""The setup portal's web app.

Runs only while the Pi is in AP mode (see main.py for when that
happens). Serves the network-picker page from a *cached* scan taken
before the AP came up (the radio can't scan and run an AP at once --
see networking.py), and tries to join whichever network the recipient
picks.
"""
import threading

from flask import Flask, jsonify, render_template, request

from . import networking

app = Flask(__name__)

# Mutable shared state for this single-process, single-recipient flow.
# No concurrency concerns worth a lock here: only one setup happens at a
# time, on one device, for one person standing in front of it.
_state = {
    "networks": [],
    "status": "idle",  # idle | connecting | success | failed
    "ssid": None,
    "error": None,
}


def _rescan_and_restart_ap() -> None:
    networking.stop_ap()
    _state["networks"] = networking.scan_networks()
    networking.start_ap()


@app.route("/")
@app.route("/<path:_catch_all>")  # any path a phone's captive-portal probe hits
def index(_catch_all=None):
    return render_template("setup.html", networks=_state["networks"], state=_state)


@app.route("/rescan", methods=["POST"])
def rescan():
    _rescan_and_restart_ap()
    return jsonify({"networks": [n.ssid for n in _state["networks"]]})


@app.route("/connect", methods=["POST"])
def connect():
    ssid = request.form.get("ssid", "").strip()
    password = request.form.get("password", "")
    if not ssid:
        return jsonify({"ok": False, "error": "Pick a network first."}), 400

    _state["status"] = "connecting"
    _state["ssid"] = ssid
    _state["error"] = None

    def attempt():
        ok = networking.connect(ssid, password)
        if ok:
            _state["status"] = "success"
        else:
            _state["status"] = "failed"
            _state["error"] = "Couldn't join that network -- check the password and try again."
            _rescan_and_restart_ap()

    threading.Thread(target=attempt, daemon=True).start()
    return jsonify({"ok": True})


@app.route("/status")
def status():
    return jsonify({
        "status": _state["status"],
        "ssid": _state["ssid"],
        "error": _state["error"],
    })


def run_portal(networks) -> None:
    """Start serving the portal. Call after start_ap() -- networks should
    already be a completed scan taken before the AP came up."""
    _state["networks"] = networks
    app.run(host="0.0.0.0", port=80)
