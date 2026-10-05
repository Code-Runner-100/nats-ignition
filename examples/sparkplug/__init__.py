# sparkplug package — expose sparkplug_b_pb2 if generated
try:
    from . import sparkplug_b_pb2  # noqa: F401
except ImportError:
    pass
