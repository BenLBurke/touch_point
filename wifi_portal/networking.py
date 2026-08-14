"""nmcli wrapper: WiFi connection state, scanning, and connecting.

Every real network call goes through subprocess, so this can be
exercised in tests by monkeypatching subprocess.run -- the same
"keep hardware/OS calls behind a thin, mockable layer" pattern used in
touchpoint/hardware.py.

Important hardware constraint: a Pi Zero W has a single WiFi radio, so
it cannot scan for nearby networks while also running as an access
point. Callers must scan_networks() *before* start_ap(), not after.
"""
import subprocess
from dataclasses import dataclass

WLAN_IFACE = "wlan0"
AP_SSID = "Touch Point Setup"
AP_CON_NAME = "touchpoint-ap"


@dataclass(frozen=True)
class WifiNetwork:
    ssid: str
    signal: int  # 0-100
    security: str  # e.g. "WPA2", "" for open


def _run(args):
    return subprocess.run(args, capture_output=True, text=True, check=False)


def is_connected() -> bool:
    """True if wlan0 currently has a working connection to a real network
    (not our own onboarding access point)."""
    result = _run(["nmcli", "-t", "-f", "DEVICE,STATE,CONNECTION", "device", "status"])
    for line in result.stdout.strip().splitlines():
        parts = line.split(":")
        if len(parts) >= 3 and parts[0] == WLAN_IFACE:
            return parts[1] == "connected" and parts[2] != AP_CON_NAME
    return False


def scan_networks() -> list:
    """Return nearby WiFi networks, strongest signal first, de-duplicated
    by SSID (multiple access points broadcasting the same network show up
    as one entry, keeping whichever has the better signal)."""
    _run(["nmcli", "device", "wifi", "rescan"])
    result = _run(["nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY", "device", "wifi", "list"])
    seen = {}
    for line in result.stdout.strip().splitlines():
        parts = line.split(":")
        if len(parts) < 3:
            continue
        ssid, signal, security = parts[0], parts[1], parts[2]
        if not ssid or ssid == AP_SSID:
            continue
        try:
            signal_val = int(signal)
        except ValueError:
            signal_val = 0
        if ssid not in seen or signal_val > seen[ssid].signal:
            seen[ssid] = WifiNetwork(ssid=ssid, signal=signal_val, security=security)
    return sorted(seen.values(), key=lambda n: n.signal, reverse=True)


def start_ap() -> None:
    """Bring up an open (no password) access point for onboarding."""
    _run(["nmcli", "connection", "delete", AP_CON_NAME])  # clear any stale profile
    _run([
        "nmcli", "connection", "add",
        "type", "wifi",
        "ifname", WLAN_IFACE,
        "con-name", AP_CON_NAME,
        "autoconnect", "no",
        "ssid", AP_SSID,
        "802-11-wireless.mode", "ap",
        "802-11-wireless.band", "bg",
        "ipv4.method", "shared",
        "wifi-sec.key-mgmt", "none",
    ])
    _run(["nmcli", "connection", "up", AP_CON_NAME])


def stop_ap() -> None:
    _run(["nmcli", "connection", "down", AP_CON_NAME])


def connect(ssid: str, password: str) -> bool:
    """Tear down the onboarding AP and try to join a real network.
    Returns True on success."""
    stop_ap()
    args = ["nmcli", "device", "wifi", "connect", ssid, "ifname", WLAN_IFACE]
    if password:
        args += ["password", password]
    result = _run(args)
    return result.returncode == 0
