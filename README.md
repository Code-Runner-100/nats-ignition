# nats-ignition

Standalone NATS server with JetStream + MQTT, set up for Ignition SCADA and Sparkplug B. No leaf nodes, no hub. Drop it on any machine and start connecting clients.

---

## What's in here

```
docker-compose.yml       # NATS container
nats.conf                # Server config — JetStream, MQTT, single account
examples/
  subscriber.py          # Python NATS subscriber with Sparkplug B decode
  sparkplug/
    sparkplug_b.proto    # Sparkplug B protobuf definition
    __init__.py
docs/
  ignition-transmission.md
  ignition-engine.md
```

---

## Quick Start

```bash
# Linux / Mac
docker compose up -d

# Windows
docker-compose up -d
```

Check it's running:

```bash
curl http://localhost:8222/varz
```

---

## Ports

| Port (host) | Port (container) | Protocol | Purpose |
|-------------|-----------------|----------|---------|
| 4222 | 4222 | TCP | NATS client |
| 8222 | 8222 | HTTP | Monitoring |
| 1883 | 1883 | TCP | MQTT |

---

## Credentials

| User | Password |
|------|----------|
| nats-client | natspass123 |

MQTT clients connect without credentials (`no_auth_user` is set to `nats-client`).

---

## Ignition Setup

**Transmission in Ignition <Example>** (edge, publishes data):

| Field | Value |
|-------|-------|
| Server URL | `tcp://<NATS_HOST>:1883` |
| Group ID | `site01` |
| Edge Node ID | `edge01` |

**Engine** (central, subscribes):

| Field | Value |
|-------|-------|
| Server URL | `tcp://localhost:1883` |

Full walkthrough: [docs/ignition-transmission.md](docs/ignition-transmission.md) · [docs/ignition-engine.md](docs/ignition-engine.md)

> **No spaces or dots in Group ID, Edge Node ID, or Device ID.** NATS maps MQTT topics to subjects. dots and spaces are illegal in subject segments. Use underscores or hyphens: `site_01`, `edge-01`. Tag names inside the Sparkplug payload are fine.

---

## Monitoring

```bash
curl http://localhost:8222/varz   # server stats
curl http://localhost:8222/connz  # active connections
curl http://localhost:8222/subsz  # subscriptions
```

---

## NATS CLI

```bash
nats sub ">" --server nats://nats-client:natspass123@localhost:4222
nats pub test.hello "hello world" --server nats://nats-client:natspass123@localhost:4222
```


