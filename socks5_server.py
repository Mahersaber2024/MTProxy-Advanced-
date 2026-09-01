#!/usr/bin/env python3
# socks5_server.py - lightweight SOCKS5 server for MTProxy Manager
# RFC 1928 (SOCKS5) + RFC 1929 (username/password auth), asyncio, no deps.
# Reads /etc/mtpulse/socks.json, writes real per-user traffic to
# /etc/mtpulse/socks_usage.json (this is where usage numbers actually come
# from - counted on the wire, not scraped from logs).

import asyncio
import json
import os
import signal
import socket
import struct
import sys
import time

CONFIG_DIR = os.environ.get("MTPULSE_DIR", "/etc/mtpulse")
SOCKS_FILE = f"{CONFIG_DIR}/socks.json"
USAGE_FILE = f"{CONFIG_DIR}/socks_usage.json"
FLUSH_INTERVAL = 10
BUF = 65536
CONNECT_TIMEOUT = 12
HANDSHAKE_TIMEOUT = 20

VER = 5
AUTH_NONE = 0x00
AUTH_USERPASS = 0x02
AUTH_FAIL = 0xFF
CMD_CONNECT = 0x01

REP_OK = 0x00
REP_GENERAL = 0x01
REP_NOT_ALLOWED = 0x02
REP_NET_UNREACH = 0x03
REP_HOST_UNREACH = 0x04
REP_REFUSED = 0x05
REP_CMD_UNSUPPORTED = 0x07
REP_ATYP_UNSUPPORTED = 0x08

state = {
    "entries": {},     # sid -> entry
    "by_port": {},     # port -> {username: (password, sid)}
    "live": {},        # sid -> {"up","down","connects","current","peak","ips"}
    "base": {},        # sid -> persisted totals
    "servers": [],
    "dirty": False,
}


def log(*a):
    print(time.strftime("%Y-%m-%d %H:%M:%S"), *a, flush=True)


# ------------------------------------------------------------------- config io
def load_config():
    try:
        with open(SOCKS_FILE, 'r') as f:
            cfg = json.load(f)
    except Exception:
        cfg = {}
    entries = cfg.get("socks", {}) or {}
    by_port = {}
    for sid, e in entries.items():
        if not e.get("enabled", True):
            continue
        try:
            port = int(e.get("port"))
        except (TypeError, ValueError):
            continue
        user = e.get("username") or ""
        pwd = e.get("password") or ""
        if not user:
            continue
        by_port.setdefault(port, {})[user] = (pwd, sid)
    state["entries"] = entries
    state["by_port"] = by_port
    return cfg


def load_usage():
    try:
        with open(USAGE_FILE, 'r') as f:
            data = json.load(f)
        if isinstance(data, dict):
            state["base"] = data.get("totals", {}) or {}
    except Exception:
        state["base"] = {}


def live(sid):
    return state["live"].setdefault(
        sid, {"up": 0, "down": 0, "connects": 0, "current": 0, "peak": 0, "ips": set()})


def flush_usage(force=False):
    if not state["dirty"] and not force:
        return
    totals = {}
    for sid in set(list(state["base"].keys()) + list(state["live"].keys())):
        b = state["base"].get(sid, {})
        l = state["live"].get(sid, {})
        totals[sid] = {
            "up": int(b.get("up", 0)) + int(l.get("up", 0)),
            "down": int(b.get("down", 0)) + int(l.get("down", 0)),
            "connects": int(b.get("connects", 0)) + int(l.get("connects", 0)),
            "current": int(l.get("current", 0)),
            "peak": max(int(b.get("peak", 0)), int(l.get("peak", 0))),
            "unique_ips": max(int(b.get("unique_ips", 0)), len(l.get("ips", ()))),
        }
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        tmp = USAGE_FILE + ".tmp"
        with open(tmp, 'w') as f:
            json.dump({"updated": int(time.time()), "totals": totals}, f, indent=2)
        os.replace(tmp, USAGE_FILE)
        state["dirty"] = False
    except Exception as e:
        log("usage flush failed:", e)


async def flusher():
    while True:
        await asyncio.sleep(FLUSH_INTERVAL)
        flush_usage()


# ------------------------------------------------------------------- protocol
async def readexact(reader, n):
    return await reader.readexactly(n)


async def reply(writer, rep, atyp=0x01, addr=b'\x00\x00\x00\x00', port=0):
    writer.write(struct.pack('!BBB', VER, rep, 0x00) + bytes([atyp]) + addr +
                 struct.pack('!H', port))
    try:
        await writer.drain()
    except Exception:
        pass


async def pump(src, dst, sid, direction):
    total = 0
    try:
        while True:
            data = await src.read(BUF)
            if not data:
                break
            dst.write(data)
            await dst.drain()
            total += len(data)
            if total >= 262144:
                live(sid)[direction] += total
                state["dirty"] = True
                total = 0
    except Exception:
        pass
    finally:
        if total:
            live(sid)[direction] += total
            state["dirty"] = True
        try:
            dst.close()
        except Exception:
            pass


async def handle(reader, writer, listen_port):
    sid = None
    peer = writer.get_extra_info('peername')
    peer_ip = peer[0] if peer else '?'
    remote_w = None
    try:
        ver, nmethods = await asyncio.wait_for(readexact(reader, 2), HANDSHAKE_TIMEOUT)
        if ver != VER:
            return
        methods = await readexact(reader, nmethods)

        users = state["by_port"].get(listen_port, {})
        if AUTH_USERPASS not in methods:
            writer.write(bytes([VER, AUTH_FAIL]))
            await writer.drain()
            return
        writer.write(bytes([VER, AUTH_USERPASS]))
        await writer.drain()

        aver = (await readexact(reader, 1))[0]
        ulen = (await readexact(reader, 1))[0]
        uname = (await readexact(reader, ulen)).decode('utf-8', 'replace')
        plen = (await readexact(reader, 1))[0]
        passwd = (await readexact(reader, plen)).decode('utf-8', 'replace')

        cred = users.get(uname)
        if aver != 0x01 or not cred or cred[0] != passwd:
            writer.write(bytes([0x01, 0x01]))
            await writer.drain()
            log(f"auth failed user={uname!r} from {peer_ip} port={listen_port}")
            return
        sid = cred[1]
        writer.write(bytes([0x01, 0x00]))
        await writer.drain()

        ver, cmd, _rsv, atyp = await readexact(reader, 4)
        if ver != VER:
            return
        if atyp == 0x01:
            host = socket.inet_ntoa(await readexact(reader, 4))
        elif atyp == 0x03:
            dlen = (await readexact(reader, 1))[0]
            host = (await readexact(reader, dlen)).decode('utf-8', 'replace')
        elif atyp == 0x04:
            host = socket.inet_ntop(socket.AF_INET6, await readexact(reader, 16))
        else:
            await reply(writer, REP_ATYP_UNSUPPORTED)
            return
        dport = struct.unpack('!H', await readexact(reader, 2))[0]

        if cmd != CMD_CONNECT:
            await reply(writer, REP_CMD_UNSUPPORTED)
            return

        try:
            remote_r, remote_w = await asyncio.wait_for(
                asyncio.open_connection(host, dport), CONNECT_TIMEOUT)
        except asyncio.TimeoutError:
            await reply(writer, REP_HOST_UNREACH)
            return
        except socket.gaierror:
            await reply(writer, REP_HOST_UNREACH)
            return
        except ConnectionRefusedError:
            await reply(writer, REP_REFUSED)
            return
        except OSError:
            await reply(writer, REP_NET_UNREACH)
            return

        try:
            sock = remote_w.get_extra_info('socket')
            if sock is not None:
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        except Exception:
            pass

        st = live(sid)
        st["connects"] += 1
        st["current"] += 1
        st["peak"] = max(st["peak"], st["current"])
        st["ips"].add(peer_ip)
        state["dirty"] = True

        await reply(writer, REP_OK)

        await asyncio.gather(
            pump(reader, remote_w, sid, "up"),
            pump(remote_r, writer, sid, "down"),
        )
    except (asyncio.IncompleteReadError, asyncio.TimeoutError, ConnectionResetError):
        pass
    except Exception as e:
        log("session error:", type(e).__name__, e)
    finally:
        if sid:
            st = live(sid)
            st["current"] = max(0, st["current"] - 1)
            state["dirty"] = True
        for w in (writer, remote_w):
            try:
                if w:
                    w.close()
            except Exception:
                pass


async def start_servers():
    for srv in state["servers"]:
        srv.close()
    state["servers"] = []
    if not state["by_port"]:
        log("no enabled SOCKS5 users configured - idling")
        return
    for port, users in sorted(state["by_port"].items()):
        try:
            server = await asyncio.start_server(
                lambda r, w, p=port: handle(r, w, p),
                host='0.0.0.0', port=port, reuse_address=True, backlog=256)
            state["servers"].append(server)
            log(f"listening on 0.0.0.0:{port} users={list(users.keys())}")
        except OSError as e:
            log(f"cannot bind port {port}: {e}")


async def reload_all():
    load_config()
    await start_servers()


async def main():
    load_config()
    load_usage()
    await start_servers()
    loop = asyncio.get_running_loop()
    try:
        loop.add_signal_handler(signal.SIGHUP,
                                lambda: asyncio.ensure_future(reload_all()))
        loop.add_signal_handler(signal.SIGTERM, lambda: loop.stop())
    except NotImplementedError:
        pass
    asyncio.ensure_future(flusher())
    log("socks5_server started")
    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        flush_usage(force=True)
        log("socks5_server stopped")
