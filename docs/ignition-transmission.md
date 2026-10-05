# Ignition MQTT Transmission — Setup

This covers connecting Ignition's MQTT Transmission module to this NATS stack.

## MQTT Server Entry

In Ignition Designer → MQTT Transmission → Settings → Servers, add a new server:

| Field | Value |
|-------|-------|
| Name | Nats-Gen (or whatever you want) |
| URL | `tcp://<NATS_HOST>:1883` |
| Client ID | leave default |

If Ignition is on the **same machine** as Docker, use `tcp://localhost:1883`.  
If Ignition is on a **different machine** (e.g., a k3s edge pod), use the NATS host's LAN IP: `tcp://10.0.0.215:1883`.

No username/password needed — `no_auth_user` is configured in nats.conf.

## Transmitter

Under MQTT Transmission → Transmitters, create or edit a transmitter:

| Field | Value |
|-------|-------|
| Server | Nats-Gen |
| Group ID | site01 (no spaces or dots — see below) |
| Edge Node ID | edge01 |

## Naming Rules — No Spaces or Dots

NATS maps MQTT topics directly to NATS subjects. Dots (`.`) and spaces are illegal in NATS subject segments. This affects:

- Group ID
- Edge Node ID  
- Device ID

**Use underscores or hyphens instead:** `site_01`, `edge-01`, `device_01`.

Tag *names* inside the Sparkplug payload are fine.They travel inside the Protobuf, not the topic string.

## Verifying the Connection

Transmission logs (Ignition → Status → Logs) should show:

```
Connected to tcp://<NATS_HOST>:1883
```

On the NATS side, confirm with:

```bash
curl http://localhost:8222/connz
```

You should see a connection entry from the Ignition host.

## Primary Host / Engine

If you have MQTT Engine configured with a Primary Host ID, Transmission will wait for the Engine's `STATE/<primary-host-id>` message before publishing data. Make sure Engine is connected and the Primary Host ID matches, or disable Primary Host on the Transmitter if you're just testing.

## Common Issues

**Transmission shows `0 of 1` connected:**
- Check the URL — host, port, protocol (`tcp://` not `mqtt://`)
- Verify portproxy is running on Windows (see `docs/windows-wsl2.md`)
- Confirm no other broker (Mosquitto, etc.) is sitting on that port
- Refresh Transmission Module if you do not see data at the engine side OR the transmission module is not connecting. 

**`Failed to create ServerContext` in logs:**
- Delete and recreate the server entry — stale entries from a previous config don't always clean up
