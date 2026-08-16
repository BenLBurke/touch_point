"""nmcli wrapper: WiFi connection state, scanning, and connecting.

Every real network call goes through subprocess, so this can be
exercised in tests by monkeypatching subprocess.run -- the same
"keep hardware/OS calls behind a thin, mockable layer" pattern used in
touchpoint/hardware.py.

Important hardware constraint: a Pi Zero W has a single WiFi radio, so
it cannot scan for nearby networks while also running as an access
point. Callers must scan_networks() *before* start_ap(), not after.
"""
import logging
import subprocess
from dataclasses import dataclass

WLAN_IFACE = "wlan0"
AP_SSID = "Touch Point Setup"
AP_CON_NAME = "touchpoint-ap"

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WifiNetwork:
    ssid: str
    signal: int  # 0-100
    security: str  # e.g. "WPA2", "" for open


def _run(args):
    result = subprocess.run(args, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        logger.warning(
            "Command failed (exit %d): %s\nstdout: %s\nstderr: %s",
            result.returncode, " ".join(args), result.stdout.strip(), result.stderr.strip(),
        )
    else:
        logger.debug("Ran: %s", " ".join(args))
    return result


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


def start_ap() -> bool:
    """Bring up an open (no password) access point for onboarding.
    Returns True if it actually came up."""
    _run(["nmcli", "connection", "delete", AP_CON_NAME])  # clear any stale profile; ok if it didn't exist
    add_result = _run([
        "nmcli", "connection", "add",
        "type", "wifi",
        "ifname", WLAN_IFACE,
        "con-name", AP_CON_NAME,
        "autoconnect", "no",
        "ssid", AP_SSID,
        "802-11-wireless.mode", "ap",
        "802-11-wireless.band", "bg",
        "ipv4.method", "shared",
        # Deliberately no wifi-sec.* properties: NetworkManager treats a
        # connection with no 802-11-wireless-security section as open.
        # Explicitly setting key-mgmt=none (even though that's the
        # documented "no security" value) has been observed to make
        # `nmcli connection up` prompt for a password it can never get in
        # a non-interactive context, and fail with "Passwords or
        # encryption keys are required" -- omitting it entirely avoids
        # that.
    ])
    if add_result.returncode != 0:
        logger.error("Failed to create the onboarding AP connection profile -- see command output above.")
        return False

    up_result = _run(["nmcli", "connection", "up", AP_CON_NAME])
    if up_result.returncode != 0:
        logger.error("Created the AP profile but couldn't bring it up -- see command output above.")
        return False

    logger.info("Onboarding AP '%s' is up.", AP_SSID)
    return True


def stop_ap() -> None:
    _run(["nmcli", "connection", "down", AP_CON_NAME])


def connect(ssid: str, password: str) -> bool:
    """Tear down the onboarding AP and try to join a real network.
    Returns True on success."""
    stop_ap()
    # Delete any existing saved profile for this SSID first. A stale or
    # partially-created profile (e.g. left over from an earlier attempt,
    # or from before this device went through onboarding) makes nmcli try
    # to patch it instead of building a fresh one -- observed on real
    # hardware to fail with "802-11-wireless-security.key-mgmt: property
    # is missing" even with a correct password supplied. Deleting first
    # guarantees a clean profile every time; harmless no-op if none exists.
    _run(["nmcli", "connection", "delete", ssid])
    args = ["nmcli", "device", "wifi", "connect", ssid, "ifname", WLAN_IFACE]
    if password:
        args += ["password", password]
    result = _run(args)
    return result.returncode == 0
