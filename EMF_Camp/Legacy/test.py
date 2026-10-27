#!/usr/bin/env python3
"""Probe EMF Camp's documented 2026 bar-data endpoints and save any data found.

Run once after installing:
    python -m pip install requests websocket-client paho-mqtt
    python emf_bar_2026_probe.py

This script makes one request to /api/stocktypes.json (documented as an
expensive endpoint) and does not poll the API repeatedly.
"""
from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

BASE = "https://bar.emf.camp"
OUT = Path(f"emf_bar_probe_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
OUT.mkdir(parents=True, exist_ok=True)

report: dict[str, Any] = {
    "captured_at_utc": datetime.now(timezone.utc).isoformat(),
    "base_url": BASE,
    "http": {},
    "websocket": {"status": "not tested"},
    "mqtt": {"status": "not tested"},
    "interpretation": (
        "A successful response shows data served at capture time; it does not by itself "
        "prove the response is a time-series archive from the July 2026 event."
    ),
}

# Lightweight endpoints first. stocktypes is fetched once only because the official
# documentation warns that it is expensive and should not be polled.
ENDPOINTS = {
    "sessions": "/api/sessions.json",
    "progress": "/api/progress.json",
    "departments": "/api/departments.json",
    "on_tap": "/api/on-tap.json",
    "cybar_on_tap": "/api/cybar-on-tap.json",
    "locations": "/api/locations.json",
    "stocklines": "/api/stocklines.json",
    "stocktypes": "/api/stocktypes.json",
}


def list_count(data: Any) -> str:
    if not isinstance(data, dict):
        return f"JSON {type(data).__name__}"
    counts = []
    for key, value in data.items():
        if isinstance(value, list):
            counts.append(f"{key}={len(value)}")
        elif isinstance(value, dict):
            counts.append(f"{key}={len(value)} keys")
    return ", ".join(counts) if counts else f"keys={list(data.keys())}"


def save_json(name: str, data: Any) -> None:
    (OUT / f"{name}.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def http_probe() -> tuple[list[str], list[str]]:
    stockline_keys: list[str] = []
    stocktype_keys: list[str] = []
    session = requests.Session()
    session.headers.update({"User-Agent": "EMF-Bar-ReadOnly-Probe/1.0"})

    print("\n=== HTTP JSON API ===")
    for name, path in ENDPOINTS.items():
        url = BASE + path
        entry: dict[str, Any] = {"url": url}
        try:
            response = session.get(url, timeout=12)
            entry["http_status"] = response.status_code
            entry["content_type"] = response.headers.get("content-type", "")
            entry["bytes"] = len(response.content)
            if response.ok:
                try:
                    data = response.json()
                    save_json(name, data)
                    entry["valid_json"] = True
                    entry["summary"] = list_count(data)
                    print(f"[OK]   {response.status_code} {path} — {entry['summary']}")
                    if name == "stocklines" and isinstance(data, dict):
                        rows = data.get("stocklines", [])
                        stockline_keys = [r["key"] for r in rows if isinstance(r, dict) and r.get("key")][:5]
                    if name == "stocktypes" and isinstance(data, dict):
                        rows = data.get("stocktypes", [])
                        stocktype_keys = [r["key"] for r in rows if isinstance(r, dict) and r.get("key")][:5]
                        # Derive per-product usage estimates without summing unlike units.
                        usage_rows = []
                        for row in rows:
                            try:
                                bought = float(row["base_units_bought"])
                                remaining = float(row["base_units_remaining"])
                                used = bought - remaining
                                usage_rows.append({
                                    "id": row.get("id"),
                                    "key": row.get("key"),
                                    "fullname": row.get("fullname", row.get("name")),
                                    "department": (row.get("department") or {}).get("description"),
                                    "base_unit_name": row.get("base_unit_name"),
                                    "base_units_bought": bought,
                                    "base_units_remaining": remaining,
                                    "estimated_base_units_used": used,
                                })
                            except (KeyError, TypeError, ValueError):
                                pass
                        entry["stock_rows_with_bought_remaining"] = len(usage_rows)
                        if usage_rows:
                            save_json("stocktype_usage_estimates", usage_rows)
                            entry["usage_estimates_saved_to"] = "stocktype_usage_estimates.json"
                            # Do not sum these together: products can use different base units.
                except (ValueError, json.JSONDecodeError) as exc:
                    entry["valid_json"] = False
                    entry["parse_error"] = str(exc)
                    print(f"[WARN] {response.status_code} {path} — response wasn't JSON")
            else:
                entry["valid_json"] = False
                entry["body_preview"] = response.text[:200]
                print(f"[NO]   {response.status_code} {path} — {response.text[:100]!r}")
        except requests.RequestException as exc:
            entry["error"] = f"{type(exc).__name__}: {exc}"
            print(f"[ERR]  {path} — {entry['error']}")
        report["http"][name] = entry

    return stockline_keys, stocktype_keys


def websocket_probe(keys: list[str]) -> None:
    print("\n=== WebSocket snapshots ===")
    try:
        import websocket  # websocket-client
    except ImportError:
        report["websocket"] = {"status": "not tested", "reason": "Install websocket-client"}
        print("[SKIP] Install websocket-client to test WebSocket.")
        return

    subscriptions = ["totals/by-unit", "totals/cups-re-used"] + keys[:5]
    received: list[dict[str, Any]] = []
    ws = None
    try:
        ws = websocket.create_connection(BASE.replace("https://", "wss://") + "/websocket/", timeout=4)
        for key in subscriptions:
            ws.send(f"SUBSCRIBE {key}")
        deadline = time.time() + 8
        while time.time() < deadline:
            try:
                raw = ws.recv()
            except websocket.WebSocketTimeoutException:
                continue
            if not raw:
                continue
            item: dict[str, Any] = {"received_at_utc": datetime.now(timezone.utc).isoformat(), "raw": raw}
            try:
                item["json"] = json.loads(raw)
            except (TypeError, ValueError):
                pass
            received.append(item)
            print(f"[MSG] {raw[:240]}")
        status = "connected; messages received" if received else "connected; no messages in 8s (inconclusive)"
        report["websocket"] = {
            "status": status,
            "url": "wss://bar.emf.camp/websocket/",
            "subscriptions": subscriptions,
            "messages_received": len(received),
        }
        save_json("websocket_messages", received)
        print(f"[INFO] {status}; subscribed to {len(subscriptions)} keys.")
    except Exception as exc:
        report["websocket"] = {
            "status": "failed",
            "url": "wss://bar.emf.camp/websocket/",
            "error": f"{type(exc).__name__}: {exc}",
        }
        print(f"[ERR] WebSocket — {type(exc).__name__}: {exc}")
    finally:
        if ws is not None:
            try:
                ws.close()
            except Exception:
                pass


def mqtt_probe() -> None:
    print("\n=== MQTT retained messages ===")
    try:
        import paho.mqtt.client as mqtt
    except ImportError:
        report["mqtt"] = {"status": "not tested", "reason": "Install paho-mqtt"}
        print("[SKIP] Install paho-mqtt to test MQTT.")
        return

    messages: list[dict[str, Any]] = []
    state = {"connected": False, "error": None}

    def on_connect(client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            state["connected"] = True
            client.subscribe("bar/#", qos=0)
            print("[OK] Connected to mqtt.emf.camp:8883; subscribed to bar/#")
        else:
            state["error"] = f"MQTT connect reason: {reason_code}"

    def on_message(client, userdata, msg):
        item = {
            "received_at_utc": datetime.now(timezone.utc).isoformat(),
            "topic": msg.topic,
            "retained": bool(msg.retain),
            "payload_utf8": msg.payload.decode("utf-8", errors="replace"),
        }
        messages.append(item)
        if len(messages) <= 15:
            print(f"[MSG] retained={item['retained']} {msg.topic} {item['payload_utf8'][:180]}")

    client = None
    try:
        client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=f"emf-bar-readonly-probe-{int(time.time())}",
            protocol=mqtt.MQTTv311,
        )
        client.tls_set()  # TLS certificate verification enabled
        client.on_connect = on_connect
        client.on_message = on_message
        client.connect("mqtt.emf.camp", 8883, keepalive=20)
        client.loop_start()
        time.sleep(10)
        if state["connected"]:
            retained_count = sum(1 for m in messages if m["retained"])
            status = "messages received" if messages else "connected but no bar/# messages (inconclusive)"
            report["mqtt"] = {
                "status": status,
                "broker": "mqtt.emf.camp:8883 (TLS)",
                "topic_filter": "bar/#",
                "messages_received": len(messages),
                "retained_messages_received": retained_count,
            }
            save_json("mqtt_bar_messages", messages)
            print(f"[INFO] {status}; {retained_count} retained messages out of {len(messages)} total.")
        else:
            report["mqtt"] = {
                "status": "connection failed",
                "broker": "mqtt.emf.camp:8883 (TLS)",
                "error": state["error"] or "No successful CONNACK received within 10s",
            }
            print(f"[ERR] MQTT — {report['mqtt']['error']}")
    except Exception as exc:
        report["mqtt"] = {
            "status": "failed",
            "broker": "mqtt.emf.camp:8883 (TLS)",
            "error": f"{type(exc).__name__}: {exc}",
        }
        print(f"[ERR] MQTT — {type(exc).__name__}: {exc}")
    finally:
        if client is not None:
            try:
                client.loop_stop()
                client.disconnect()
            except Exception:
                pass


def main() -> None:
    print("EMF 2026 Bar Data Probe")
    print("Output directory:", OUT.resolve())
    stockline_keys, stocktype_keys = http_probe()
    websocket_probe(stocktype_keys + stockline_keys)
    mqtt_probe()
    save_json("report", report)
    print("\n=== Result ===")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\nSaved results to: {OUT.resolve()}")
    print("A successful connection/data response proves availability at the time you ran this script;")
    print("it does not imply that a full event-wide historical time series is archived.")


if __name__ == "__main__":
    main()
