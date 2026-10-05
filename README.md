# nats-ignition

Standalone NATS server with JetStream + MQTT, wired up for Ignition SCADA and Sparkplug B. No leaf nodes, no hub. Drop it on any machine and start connecting clients.

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
  windows-wsl2.md        # Docker Desktop port binding fix for Windows
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
| 1880 | 1883 | TCP | MQTT |

---

## Credentials

| User | Password |
|------|----------|
| nats-client | natspass123 |

MQTT clients connect without credentials (`no_auth_user` is set to `nats-client`).

---

## Ignition Setup

**Transmission** (edge, publishes data):

| Field | Value |
|-------|-------|
| Server URL | `tcp://<NATS_HOST>:1880` |
| Group ID | `site01` |
| Edge Node ID | `edge01` |

**Engine** (central, subscribes):

| Field | Value |
|-------|-------|
| Server URL | `tcp://localhost:1880` |

Full walkthrough: [docs/ignition-transmission.md](docs/ignition-transmission.md) · [docs/ignition-engine.md](docs/ignition-engine.md)

> **No spaces or dots in Group ID, Edge Node ID, or Device ID.** NATS maps MQTT topics to subjects — dots and spaces are illegal in subject segments. Use underscores or hyphens: `site_01`, `edge-01`. Tag names inside the Sparkplug payload are fine.

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

---

## Python Subscriber

```bash
pip install nats-py
python examples/subscriber.py
# or point at a remote server:
python examples/subscriber.py --server nats://nats-client:natspass123@10.0.0.215:4222
```

For Sparkplug B decode, generate the protobuf module first:

```bash
pip install grpcio-tools
python -m grpc_tools.protoc -I examples/sparkplug --python_out=examples/sparkplug examples/sparkplug/sparkplug_b.proto
```

Then re-run the subscriber — it will auto-decode `spBv1.0/...` subjects.

---

## Windows — Docker Desktop Port Binding

Docker Desktop on Windows (WSL2 mode) binds container ports to `127.0.0.1`, not `0.0.0.0`. LAN devices can't reach the port even with explicit `0.0.0.0:` bindings in compose.

Fix with a port proxy (PowerShell as Administrator):

```powershell
netsh interface portproxy add v4tov4 listenaddress=0.0.0.0 listenport=1880 connectaddress=127.0.0.1 connectport=1880
New-NetFirewallRule -DisplayName "NATS MQTT 1880" -Direction Inbound -Protocol TCP -LocalPort 1880 -Action Allow -Profile Any
```

Full details: [docs/windows-wsl2.md](docs/windows-wsl2.md)
