#!/usr/bin/env python3
"""Boot-time entry point for the WiFi onboarding portal.

Waits briefly for NetworkManager to rejoin a previously-known network
on its own; if that doesn't happen within the grace period, scans for
nearby networks, brings up the onboarding access point, and serves the
setup page until someone successfully connects (or the process is
stopped). If a connection already exists, does nothing further --
NetworkManager itself handles reconnecting to a known network, this
script only decides whether the *onboarding portal* is needed.
"""
import logging
import sys
import time

from . import networking
from .app import run_portal

BOOT_GRACE_SECONDS = 45
POLL_INTERVAL_SECONDS = 3

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s:%(message)s")
logger = logging.getLogger(__name__)


def main() -> int:
    waited = 0
    while waited < BOOT_GRACE_SECONDS:
        if networking.is_connected():
            print("Already on a known network -- setup portal not needed.")
            return 0
        time.sleep(POLL_INTERVAL_SECONDS)
        waited += POLL_INTERVAL_SECONDS

    print("No known network after boot grace period -- starting setup portal.")
    networks = networking.scan_networks()
    logger.info("Found %d nearby network(s) before starting the AP.", len(networks))

    if not networking.start_ap():
        logger.error(
            "Could not bring up the onboarding access point -- see the warnings above "
            "for the specific nmcli command that failed. Common causes: WiFi country/"
            "regulatory domain not set (try 'sudo raspi-config' -> Localisation Options "
            "-> WLAN Country), or the wifi driver doesn't support AP mode."
        )
        return 1

    run_portal(networks)
    return 0


if __name__ == "__main__":
    sys.exit(main())
