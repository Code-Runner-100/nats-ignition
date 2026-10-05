# Ignition MQTT Engine — Setup

MQTT Engine subscribes to NATS and surfaces Sparkplug B tag data inside Ignition's tag tree.

## MQTT Server Entry

In Ignition Designer → MQTT Engine → Settings → Servers:

| Field | Value |
|-------|-------|
| Name | Nats-Local |
| URL | `tcp://localhost:1883` |

Engine typically runs on the same machine as NATS (or in the same Docker Compose stack), so `localhost` works.

## Namespaces

Under MQTT Engine → Settings → Namespaces, add a Sparkplug B namespace and point it at your server.

Ignition will create tags under `[MQTT Engine] Edge Nodes/<GroupID>/<EdgeNodeID>/<DeviceID>/<TagName>`.

## Verify

Engine status should show the server as **Connected**. Tags appear in the tag browser once Transmission publishes its first `DBIRTH` message.

## Engine vs Transmission

- **Engine** = subscriber. Runs where you want tags to appear in Ignition (usually the central Ignition Gateway).
- **Transmission** = publisher. Runs on the edge Ignition Gateway, sends device data up.

They can run on the same Ignition instance for local testing. For production, Engine is central and Transmission is at the edge.

- **Note**
  If you do not see new tags that were added to the transmission side. Reset your transmission module. 
