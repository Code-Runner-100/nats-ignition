+++
categories = ["Engineering"]
date = "2026-10-05"
tags = ["NATS", "MQTT", "IIoT", "Ignition", "Sparkplug B", "Docker"]
title = "NATS + Ignition MQTT: Sparkplug B from Edge to Subscriber"
author = "Alex Miller"
+++

I've been building out an IIoT pipeline using NATS as the backbone for Sparkplug B telemetry from Ignition SCADA. This post covers the Docker setup: standalone NATS with JetStream and MQTT, Ignition Transmission publishing from the edge, and a Python subscriber decoding Sparkplug B on the other end.

No leaf nodes, no hub. Just a single NATS server you can drop anywhere and start connecting clients.

## What we're building

```
Ignition Transmission (edge)
        │
        │  MQTT / Sparkplug B  (tcp://<NATS_HOST>:1883)
        ▼
  NATS + JetStream (Docker)
        │
        │  NATS core  (nats://localhost:4222)
        ▼
  Python subscriber  (decodes Sparkplug B protobuf)
```

Everything is in the [nats-ignition](https://github.com/code-runner-100/nats-ignition) repo.

## Stand up NATS

Two files.

**docker-compose.yml**

```yaml
services:
  nats:
    image: nats:latest
    container_name: nats
    restart: unless-stopped
    ports:
      - "4222:4222"   # NATS client
      - "8222:8222"   # HTTP monitoring
      - "1883:1883"   # MQTT
    volumes:
      - ./nats.conf:/etc/nats/nats.conf
      - nats-data:/data/jetstream
    command: ["-c", "/etc/nats/nats.conf"]

volumes:
  nats-data:
    driver: local
```

**nats.conf**

```
port: 4222
http_port: 8222
server_name: "nats"
jetstream: enabled

jetstream {
  store_dir: "/data/jetstream"
}

accounts {
  DEFAULT: {
    users: [
      { user: "nats-client", password: "natspass123" }
    ]
    jetstream: enabled
  }
}

mqtt {
  port: 1883
  ack_wait: "1m"
  max_ack_pending: 100
  no_auth_user: "nats-client"
}
```

`no_auth_user` lets MQTT clients connect without credentials. Ignition Transmission doesn't send credentials by default, so this keeps the config simple.

```bash
# Linux / Mac
docker compose up -d

# Windows
docker-compose up -d
```

Verify it's running:

```bash
curl http://localhost:8222/varz
```

## Configure Ignition Transmission

In Ignition Designer, go to MQTT Transmission, Settings, Servers, and add a server:

| Field | Value |
|-------|-------|
| Name | Nats-Gen |
| URL | `tcp://<NATS_HOST>:1883` |

Then set your Group ID and Edge Node ID under Transmitters.

**Watch your naming.** NATS maps MQTT topics directly to subjects. Dots (`.`) are the NATS subject delimiter, so a dot in your Group ID or Edge Node ID will break things. No spaces either. Use underscores or hyphens: `site_01`, `edge-01`, `device_01`. Tag names inside the Sparkplug payload are fine since they don't hit the topic.

## Python subscriber

```bash
pip install nats-py
python examples/subscriber.py
```

Connects on port 4222 (NATS, not MQTT) and subscribes to everything. To decode Sparkplug B, generate the protobuf module first:

```bash
pip install grpcio-tools
python -m grpc_tools.protoc \
  -I examples/sparkplug \
  --python_out=examples/sparkplug \
  examples/sparkplug/sparkplug_b.proto
```

With it, you get decoded metrics:

```json
{
  "subject": "spBv1.0/site_01/DDATA/edge-01/device_01",
  "timestamp": 1727123456789,
  "seq": 4,
  "metrics": {
    "Temperature": 72.4,
    "Pressure": 14.7,
    "Running": true
  }
}
```

Point it at a remote server:

```bash
python examples/subscriber.py \
  --server nats://nats-client:natspass123@10.0.0.215:4222 \
  --subject "spBv1.0/>"
```

Repo: [github.com/code-runner-100/nats-ignition](https://github.com/code-runner-100/nats-ignition)
