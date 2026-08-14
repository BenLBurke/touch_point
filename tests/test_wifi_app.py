"""Tests for the wifi_portal Flask app's routes.

networking calls are monkeypatched out entirely -- these test the web
layer (routing, request handling, status transitions), not real WiFi.
"""
import time

import pytest

from wifi_portal import app as wifi_app
from wifi_portal import networking


@pytest.fixture
def client():
    wifi_app.app.config["TESTING"] = True
    wifi_app._state.update({"networks": [], "status": "idle", "ssid": None, "error": None})
    with wifi_app.app.test_client() as client:
        yield client


def test_index_lists_scanned_networks(client):
    wifi_app._state["networks"] = [
        networking.WifiNetwork(ssid="HomeNet", signal=80, security="WPA2"),
        networking.WifiNetwork(ssid="OpenCafe", signal=40, security=""),
    ]
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"HomeNet" in resp.data
    assert b"OpenCafe" in resp.data


def test_index_shows_empty_state_with_no_networks(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"No networks found yet" in resp.data


def test_index_catch_all_serves_setup_page_for_any_path(client):
    # This is what makes phones' captive-portal probes land on the setup
    # page instead of a 404 -- any unmatched path still resolves to "/".
    resp = client.get("/generate_204")
    assert resp.status_code == 200
    assert b"Touch Point" in resp.data


def test_connect_requires_ssid(client):
    resp = client.post("/connect", data={"password": "x"})
    assert resp.status_code == 400
    assert resp.get_json()["ok"] is False


def test_connect_success_updates_status(client, monkeypatch):
    monkeypatch.setattr(networking, "connect", lambda ssid, password: True)

    resp = client.post("/connect", data={"ssid": "HomeNet", "password": "hunter2"})
    assert resp.status_code == 200
    assert resp.get_json()["ok"] is True

    # connect() runs in a background thread; give it a moment
    for _ in range(20):
        if wifi_app._state["status"] != "connecting":
            break
        time.sleep(0.05)

    status = client.get("/status").get_json()
    assert status["status"] == "success"
    assert status["ssid"] == "HomeNet"


def test_connect_failure_rescans_and_reports_error(client, monkeypatch):
    monkeypatch.setattr(networking, "connect", lambda ssid, password: False)
    monkeypatch.setattr(networking, "stop_ap", lambda: None)
    monkeypatch.setattr(networking, "scan_networks", lambda: [])
    monkeypatch.setattr(networking, "start_ap", lambda: None)

    resp = client.post("/connect", data={"ssid": "HomeNet", "password": "wrong"})
    assert resp.get_json()["ok"] is True

    for _ in range(20):
        if wifi_app._state["status"] != "connecting":
            break
        time.sleep(0.05)

    status = client.get("/status").get_json()
    assert status["status"] == "failed"
    assert status["error"]


def test_rescan_updates_cached_network_list(client, monkeypatch):
    monkeypatch.setattr(networking, "stop_ap", lambda: None)
    monkeypatch.setattr(networking, "start_ap", lambda: None)
    monkeypatch.setattr(
        networking,
        "scan_networks",
        lambda: [networking.WifiNetwork(ssid="NewNetwork", signal=60, security="WPA2")],
    )

    resp = client.post("/rescan")
    assert resp.status_code == 200
    assert resp.get_json()["networks"] == ["NewNetwork"]
    assert wifi_app._state["networks"][0].ssid == "NewNetwork"
