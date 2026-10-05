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

import asyncio    # nats-py is built on asyncio, so we need an event loop
import argparse   # command-line argument parsing
import json       # used to pretty-print decoded Sparkplug payloads

import nats       # official NATS asyncio client

# Sparkplug B decoding is optional. The protobuf module has to be generated
# from the .proto file with protoc, so it may not exist. Instead of crashing
# at import time, we record whether it's available and degrade gracefully.
try:
    from sparkplug import sparkplug_b_pb2
    SPARKPLUG_AVAILABLE = True
except ImportError:
    SPARKPLUG_AVAILABLE = False


# Sparkplug B topics always begin with this namespace (e.g. spBv1.0/group/NDATA/node).
# We use it to decide whether a message should be run through the protobuf decoder.
SPARKPLUG_PREFIX = "spBv1.0"


def decode_sparkplug(data: bytes, subject: str) -> dict:
    """Decode a Sparkplug B protobuf payload. Returns a dict."""
    # Create an empty Payload message and fill it by parsing the raw bytes.
    payload = sparkplug_b_pb2.Payload()
    payload.ParseFromString(data)

    # Flatten the list of metrics into a simple {metric_name: value} dict.
    metrics = {}
    for metric in payload.metrics:
        name = metric.name
        # In Sparkplug B a metric stores its value in one of several typed
        # fields (a protobuf "oneof"). We check each in turn and take the
        # first one that is actually set on this message.
        for field in (
            "int_value", "long_value", "float_value", "double_value",
            "boolean_value", "string_value", "bytes_value",
        ):
            if metric.HasField(field):
                metrics[name] = getattr(metric, field)
                break  # only one value field can be set, so stop searching

    # Return the payload header (timestamp, seq) plus the flattened metrics.
    # `seq` is the Sparkplug sequence number (0-255), useful for spotting
    # dropped or out-of-order messages.
    return {
        "subject": subject,
        "timestamp": payload.timestamp,
        "seq": payload.seq,
        "metrics": metrics,
    }


async def message_handler(msg):
    """Callback invoked by nats-py for every message received."""
    subject = msg.subject
    data = msg.data  # always raw bytes

    # Path 1: Sparkplug B message and the decoder is available
    if SPARKPLUG_AVAILABLE and subject.startswith(SPARKPLUG_PREFIX):
        try:
            decoded = decode_sparkplug(data, subject)
            print(json.dumps(decoded, indent=2))
            return  # handled, skip the fallback below
        except Exception as e:
            # Malformed payload or a non-protobuf message on a spBv1.0 subject.
            # Log it and fall through to the raw print below.
            print(f"[{subject}] sparkplug decode failed: {e}")

    # Path 2: fallback for everything else.
    # Try to show the payload as text; if it isn't valid UTF-8 (binary data),
    # just report how many bytes it was.
    try:
        print(f"[{subject}] {data.decode()}")
    except Exception:
        print(f"[{subject}] <{len(data)} bytes>")


async def main(server: str, subject: str):
    print(f"Connecting to {server}")
    # Open the connection. Credentials can be embedded in the URL.
    nc = await nats.connect(server)
    print(f"Connected. Subscribing to '{subject}'")

    # Register message_handler as the callback. NATS wildcards:
    #   *  matches one token   (a.*.c)
    #   >  matches one or more trailing tokens (a.>), so ">" alone is everything
    await nc.subscribe(subject, cb=message_handler)

    # Warn up front if we can't decode Sparkplug B
    if not SPARKPLUG_AVAILABLE:
        print(
            "Note: sparkplug_b_pb2 not found — Sparkplug B payloads will print as raw bytes.\n"
            "See examples/sparkplug/ to generate the protobuf module."
        )

    try:
        # Keep the program alive. Messages are delivered by the callback in the
        # background, so this loop just prevents main() from returning.
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        # drain() unsubscribes, lets in-flight messages finish processing,
        # then closes the connection cleanly.
        await nc.drain()
        print("Disconnected.")


if __name__ == "__main__":
    # Command-line interface
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
    # asyncio.run creates the event loop, runs main() to completion, then closes the loop
    asyncio.run(main(args.server, args.subject))
