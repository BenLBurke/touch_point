"""WiFi onboarding portal.

Scoped-down implementation of section 3 ("WiFi Login Screen") from
docs/specs/wifi-login-and-device-dashboard.md. Falls back to a
captive-portal access point when the Pi can't join a known network on
boot, lets the recipient pick their network and enter a password from
their phone, and hands control back to normal networking on success.

Sections 4-6 of that spec (phone-home check-ins, the fleet dashboard,
Tailscale remote access) are deliberately not part of this -- separate
infrastructure, worth building once there's more than one gifted
device to track.
"""
