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
import time

from . import networking
from .app import run_portal

BOOT_GRACE_SECONDS = 45
POLL_INTERVAL_SECONDS = 3


def main() -> None:
    waited = 0
    while waited < BOOT_GRACE_SECONDS:
        if networking.is_connected():
            print("Already on a known network -- setup portal not needed.")
            return
        time.sleep(POLL_INTERVAL_SECONDS)
        waited += POLL_INTERVAL_SECONDS

    print("No known network after boot grace period -- starting setup portal.")
    networks = networking.scan_networks()
    networking.start_ap()
    run_portal(networks)


if __name__ == "__main__":
    main()
