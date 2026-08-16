"""Tests for wifi_portal.networking.

Every real nmcli call goes through subprocess.run, so these tests fake
that out entirely -- no NetworkManager, no WiFi hardware, no Pi needed.
"""
import types

import pytest

from wifi_portal import networking


def _fake_result(stdout="", returncode=0, stderr=""):
    return types.SimpleNamespace(stdout=stdout, returncode=returncode, stderr=stderr)


def test_is_connected_true_when_wlan0_up_on_a_real_network(monkeypatch):
    calls = []

    def fake_run(args, **kwargs):
        calls.append(args)
        return _fake_result("eth0:connected:Wired connection 1\nwlan0:connected:HomeNetwork\n")

    monkeypatch.setattr(networking.subprocess, "run", fake_run)
    assert networking.is_connected() is True


def test_is_connected_false_when_on_our_own_ap(monkeypatch):
    def fake_run(args, **kwargs):
        return _fake_result(f"wlan0:connected:{networking.AP_CON_NAME}\n")

    monkeypatch.setattr(networking.subprocess, "run", fake_run)
    assert networking.is_connected() is False


def test_is_connected_false_when_disconnected(monkeypatch):
    def fake_run(args, **kwargs):
        return _fake_result("wlan0:disconnected:--\n")

    monkeypatch.setattr(networking.subprocess, "run", fake_run)
    assert networking.is_connected() is False


def test_scan_networks_parses_and_sorts_by_signal(monkeypatch):
    output = "HomeNet:80:WPA2\nCoffeeShop:40:\nHomeNet:55:WPA2\n"

    def fake_run(args, **kwargs):
        return _fake_result(output)

    monkeypatch.setattr(networking.subprocess, "run", fake_run)
    networks = networking.scan_networks()

    assert [n.ssid for n in networks] == ["HomeNet", "CoffeeShop"]
    # de-duplicated: kept the stronger of the two HomeNet readings
    assert networks[0].signal == 80


def test_scan_networks_skips_our_own_ap_and_blank_ssids(monkeypatch):
    output = f"{networking.AP_SSID}:100:\n:60:\nRealNetwork:50:WPA2\n"

    def fake_run(args, **kwargs):
        return _fake_result(output)

    monkeypatch.setattr(networking.subprocess, "run", fake_run)
    networks = networking.scan_networks()

    assert [n.ssid for n in networks] == ["RealNetwork"]


def test_connect_success_stops_ap_first(monkeypatch):
    calls = []

    def fake_run(args, **kwargs):
        calls.append(args)
        return _fake_result(returncode=0)

    monkeypatch.setattr(networking.subprocess, "run", fake_run)
    assert networking.connect("HomeNet", "hunter2") is True

    # AP must come down before we try to join the real network
    ap_down_index = next(i for i, c in enumerate(calls) if c[:3] == ["nmcli", "connection", "down"])
    connect_index = next(i for i, c in enumerate(calls) if "connect" in c)
    assert ap_down_index < connect_index


def test_connect_deletes_any_stale_profile_before_connecting(monkeypatch):
    calls = []

    def fake_run(args, **kwargs):
        calls.append(args)
        return _fake_result(returncode=0)

    monkeypatch.setattr(networking.subprocess, "run", fake_run)
    networking.connect("HomeNet", "hunter2")

    delete_call = next(c for c in calls if c[:3] == ["nmcli", "connection", "delete"])
    assert delete_call[-1] == "HomeNet"
    connect_index = next(i for i, c in enumerate(calls) if "connect" in c)
    delete_index = calls.index(delete_call)
    assert delete_index < connect_index


def test_connect_failure_returns_false(monkeypatch):
    def fake_run(args, **kwargs):
        return _fake_result(returncode=1)

    monkeypatch.setattr(networking.subprocess, "run", fake_run)
    assert networking.connect("HomeNet", "wrongpassword") is False


def test_connect_open_network_omits_password_flag(monkeypatch):
    calls = []

    def fake_run(args, **kwargs):
        calls.append(args)
        return _fake_result(returncode=0)

    monkeypatch.setattr(networking.subprocess, "run", fake_run)
    networking.connect("OpenNet", "")

    connect_call = next(c for c in calls if "connect" in c)
    assert "password" not in connect_call


def test_start_ap_returns_true_when_everything_succeeds(monkeypatch):
    monkeypatch.setattr(networking.subprocess, "run", lambda args, **kw: _fake_result(returncode=0))
    assert networking.start_ap() is True


def test_start_ap_returns_false_when_profile_creation_fails(monkeypatch, caplog):
    def fake_run(args, **kwargs):
        if "add" in args:
            return _fake_result(returncode=1, stdout="")
        return _fake_result(returncode=0)

    monkeypatch.setattr(networking.subprocess, "run", fake_run)
    with caplog.at_level("ERROR"):
        assert networking.start_ap() is False
    assert "couldn't bring it up" not in caplog.text  # failed earlier, at profile creation
    assert any("create the onboarding AP" in r.message for r in caplog.records)


def test_start_ap_returns_false_when_bringing_it_up_fails(monkeypatch, caplog):
    def fake_run(args, **kwargs):
        if args[:3] == ["nmcli", "connection", "up"]:
            return _fake_result(returncode=1)
        return _fake_result(returncode=0)

    monkeypatch.setattr(networking.subprocess, "run", fake_run)
    with caplog.at_level("ERROR"):
        assert networking.start_ap() is False
    assert any("couldn't bring it up" in r.message for r in caplog.records)


def test_run_logs_a_warning_when_a_command_fails(monkeypatch, caplog):
    monkeypatch.setattr(
        networking.subprocess, "run",
        lambda args, **kw: _fake_result(returncode=1),
    )
    with caplog.at_level("WARNING"):
        networking._run(["nmcli", "definitely", "not", "a", "real", "command"])
    assert any("Command failed" in r.message for r in caplog.records)
