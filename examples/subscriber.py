"""
NATS subscriber — listens to all subjects and decodes Sparkplug B payloads.

Requirements:
    pip install nats-py

Optional (Sparkplug B decode):
    pip install protobuf
    # Generate sparkplug_b_pb2.py from the .proto file in examples/sparkplug/
    protoc --python_out=. examples/sparkplug/sparkplug_b.proto

Usage:
    python examples/subscriber.py
    python examples/subscriber.py --server nats://nats-client:natspass123@10.0.0.215:4222
    python examples/subscriber.py --subject "spBv1.0/>"
"""

import asyncio
import argparse
import json

import nats

# Optional Sparkplug B decode
try:
    from sparkplug import sparkplug_b_pb2
    SPARKPLUG_AVAILABLE = True
except ImportError:
    SPARKPLUG_AVAILABLE = False


SPARKPLUG_PREFIX = "spBv1.0"


def decode_sparkplug(data: bytes, subject: str) -> dict:
    """Decode a Sparkplug B protobuf payload. Returns a dict."""
    payload = sparkplug_b_pb2.Payload()
    payload.ParseFromString(data)
    metrics = {}
    for metric in payload.metrics:
        name = metric.name
        # Pull whichever value field is set
        for field in (
            "int_value", "long_value", "float_value", "double_value",
            "boolean_value", "string_value", "bytes_value",
        ):
            if metric.HasField(field):
                metrics[name] = getattr(metric, field)
                break
    return {
        "subject": subject,
        "timestamp": payload.timestamp,
        "seq": payload.seq,
        "metrics": metrics,
    }


async def message_handler(msg):
    subject = msg.subject
    data = msg.data

    if SPARKPLUG_AVAILABLE and subject.startswith(SPARKPLUG_PREFIX):
        try:
            decoded = decode_sparkplug(data, subject)
            print(json.dumps(decoded, indent=2))
            return
        except Exception as e:
            print(f"[{subject}] sparkplug decode failed: {e}")

    # Fall back to raw print
    try:
        print(f"[{subject}] {data.decode()}")
    except Exception:
        print(f"[{subject}] <{len(data)} bytes>")


async def main(server: str, subject: str):
    print(f"Connecting to {server}")
    nc = await nats.connect(server)
    print(f"Connected. Subscribing to '{subject}'")

    await nc.subscribe(subject, cb=message_handler)

    if not SPARKPLUG_AVAILABLE:
        print(
            "Note: sparkplug_b_pb2 not found — Sparkplug B payloads will print as raw bytes.\n"
            "See examples/sparkplug/ to generate the protobuf module."
        )

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        await nc.drain()
        print("Disconnected.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NATS subscriber")
    parser.add_argument(
        "--server",
        default="nats://nats-client:natspass123@localhost:4222",
        help="NATS server URL",
    )
    parser.add_argument(
        "--subject",
        default=">",
        help="Subject to subscribe to (default: > = everything)",
    )
    args = parser.parse_args()
    asyncio.run(main(args.server, args.subject))
