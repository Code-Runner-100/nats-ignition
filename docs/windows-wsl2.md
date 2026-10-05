# Windows / Docker Desktop — Port Binding Gotcha

Docker Desktop on Windows runs containers inside WSL2. When a container publishes a port, Docker binds it to `127.0.0.1` on the Windows host — not `0.0.0.0`. This means devices on your LAN **cannot reach the port** even if you put `0.0.0.0:1880:1883` in your compose file.

You can confirm this with:

```powershell
netstat -an | findstr "1880"
# Shows: 127.0.0.1:1880   LISTENING
# Should show: 0.0.0.0:1880  LISTENING
```

## Fix — WSL2 Port Proxy

The `netsh portproxy` command bridges the gap: it listens on the real Windows NIC and forwards to the WSL2 loopback.

Run in PowerShell **as Administrator**:

```powershell
netsh interface portproxy add v4tov4 `
  listenaddress=0.0.0.0 `
  listenport=1880 `
  connectaddress=127.0.0.1 `
  connectport=1880
```

Verify it took:

```powershell
netsh interface portproxy show all
```

Expected output:
```
Listen on ipv4:             Connect to ipv4:
Address         Port        Address         Port
--------------- ----------  --------------- ----------
0.0.0.0         1880        127.0.0.1       1880
```

## Windows Firewall

Add an inbound rule so the proxy is reachable from the LAN:

```powershell
New-NetFirewallRule `
  -DisplayName "NATS MQTT 1880" `
  -Direction Inbound `
  -Protocol TCP `
  -LocalPort 1880 `
  -Action Allow `
  -Profile Any
```

## Remove the Proxy Rule

```powershell
netsh interface portproxy delete v4tov4 listenaddress=0.0.0.0 listenport=1880
```

## Why Not Just Change a Docker Desktop Setting?

There is no Docker Desktop UI toggle that fixes this as of 2024. The portproxy approach is the standard workaround for WSL2-hosted services that need LAN exposure.
