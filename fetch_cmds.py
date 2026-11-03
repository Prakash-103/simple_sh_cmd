from __future__ import annotations

import re
import time
import logging
import socket
from pathlib import Path
from datetime import datetime
from getpass import getpass

import paramiko

# ── Paths ─────────────────────────────────────────────────────────────────────
OUTPUT_DIR = Path("output")
LOG_DIR    = Path("logs")
OUTPUT_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    filename=LOG_DIR / "collector.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

# ── CLI warning patterns ───────────────────────────────────────────────────────
_WARN_RE = re.compile(
    r"%\s*(Invalid input|Incomplete command|Ambiguous command|Unknown command"
    r"|Authorization failed|Error\s*:|Bad (IP address|mask)|Unrecognized command)"
    r"|syntax error|\^",
    re.IGNORECASE,
)

# Prompt: ends with  >  or  #  optionally preceded by hostname chars
_PROMPT_RE = re.compile(r"[\w\-@]+[>#]\s*$", re.MULTILINE)

W    = 65
SEP  = "=" * W
BANG = "!" * W


# ── Helpers ────────────────────────────────────────────────────────────────────
def sanitize(name: str) -> str:
    return re.sub(r"\s+", "_", re.sub(r'[\\/*?:"<>|]', "_", name))[:150]


def cli_warning(output: str) -> str | None:
    for line in output.splitlines():
        if _WARN_RE.search(line):
            return line.strip()
    return None


def load_lines(path: str) -> list[str]:
    return [
        ln.strip() for ln in Path(path).read_text(encoding="utf-8").splitlines()
        if ln.strip() and not ln.lstrip().startswith("#")
    ]


# ── Input helpers ──────────────────────────────────────────────────────────────
def ask_devices() -> list[str]:
    print("\nTarget Device(s):")
    print("  Single IP        :  192.168.1.1")
    print("  Multiple (comma) :  192.168.1.1, 192.168.1.2")
    print("  File             :  devices.txt\n")
    raw = input("IP(s) or file: ").strip()
    if not raw:
        return []
    if Path(raw).is_file():
        return load_lines(raw)
    return [ip for ip in re.split(r"[,;\s]+", raw) if ip]


def ask_commands() -> list[str]:
    print("\nCommand Input:")
    print("  1. Type manually")
    print("  2. Load from TXT file\n")
    choice = input("Choice [1/2]: ").strip()

    if choice == "1":
        print("Enter commands. Type 'done' to finish.")
        cmds: list[str] = []
        while True:
            c = input("cmd> ").strip()
            if c.lower() == "done":
                break
            if c:
                cmds.append(c)
        return cmds

    if choice == "2":
        fp = input("TXT file path: ").strip()
        if not Path(fp).is_file():
            print("  File not found.")
            return []
        return load_lines(fp)

    print("  Invalid choice.")
    return []


# ── Paramiko shell helpers ─────────────────────────────────────────────────────
def _read_until_prompt(channel: paramiko.Channel,
                       timeout: float = 30.0,
                       chunk_delay: float = 0.2) -> str:
    """
    Read from the interactive shell channel until a CLI prompt is detected
    or the timeout expires.  Returns decoded output.
    """
    buf   = ""
    start = time.time()

    while time.time() - start < timeout:
        if channel.recv_ready():
            chunk = channel.recv(8192).decode("utf-8", errors="replace")
            buf  += chunk
            if _PROMPT_RE.search(buf):
                break
        else:
            time.sleep(chunk_delay)

    return buf


def _clean(raw: str, cmd: str) -> str:
    """
    Strip the echoed command and the trailing device prompt from raw output.
    """
    lines = raw.splitlines()

    # Drop leading blank lines + echoed command line
    while lines and (not lines[0].strip() or cmd.strip() in lines[0]):
        lines.pop(0)

    # Drop trailing prompt line
    if lines and _PROMPT_RE.search(lines[-1]):
        lines.pop()

    return "\n".join(lines).strip()


# ── SSH session ────────────────────────────────────────────────────────────────
def connect(host: str, creds: dict) -> paramiko.SSHClient | None:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(
            hostname=host,
            username=creds["username"],
            password=creds["password"],
            port=22,
            timeout=20,
            auth_timeout=20,
            banner_timeout=20,
            look_for_keys=False,
            allow_agent=False,
        )
        return client
    except paramiko.AuthenticationException:
        logging.error("Auth failed: %s", host)
    except (socket.timeout, socket.error, paramiko.SSHException) as e:
        logging.error("Connection failed: %s — %s", host, e)
    except Exception as e:
        logging.error("Unexpected error: %s — %s", host, e)
    return None


# ── Run commands on a device ───────────────────────────────────────────────────
def run_commands(client: paramiko.SSHClient,
                 host: str,
                 commands: list[str]) -> dict:

    ts      = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = OUTPUT_DIR / sanitize(host) / ts
    out_dir.mkdir(parents=True, exist_ok=True)

    ok, warn, fail = 0, [], 0

    # Open interactive shell (vendor-agnostic)
    shell = client.invoke_shell(term="vt100", width=200, height=1000)
    shell.settimeout(30)

    # Let the banner / initial prompt arrive
    _read_until_prompt(shell, timeout=15)

    # Disable paging — works on most CLIs; ignored on others
    shell.send("terminal length 0\n")
    _read_until_prompt(shell, timeout=10)

    for i, cmd in enumerate(commands, 1):
        print(f"  [{i:>2}/{len(commands)}] {cmd}", end="  ", flush=True)
        try:
            shell.send(cmd + "\n")
            raw    = _read_until_prompt(shell, timeout=60)
            output = _clean(raw, cmd)
            issue  = cli_warning(output)
            status = f"WARNING ({issue})" if issue else "SUCCESS"

            fname = out_dir / f"{i:02d}_{sanitize(cmd)}.txt"
            with fname.open("w", encoding="utf-8") as f:
                f.write(f"Device    : {host}\n")
                f.write(f"Command   : {cmd}\n")
                f.write(f"Timestamp : {datetime.now()}\n")
                f.write(f"Status    : {status}\n")
                f.write("=" * 60 + "\n")
                f.write(output + "\n")

            if issue:
                print("[WARNING]")
                warn.append((cmd, issue))
                logging.warning("%s | %s | %s", host, cmd, issue)
            else:
                print("[OK]")
                ok += 1
                logging.info("OK: %s | %s", host, cmd)

        except Exception as e:
            fail += 1
            print("[FAIL]")
            logging.exception("FAIL: %s | %s — %s", host, cmd, e)

    shell.close()
    return {"host": host, "ok": ok, "warn": warn, "fail": fail, "dir": out_dir}


# ── Entry point ────────────────────────────────────────────────────────────────
def main():
    print(SEP)
    print("      NETWORK DEVICE COMMAND DOWNLOADER")
    print(SEP)

    devices = ask_devices()
    if not devices:
        print("No devices provided. Exiting.")
        return

    print(f"\n  Devices ({len(devices)}): {', '.join(devices)}")

    creds = {
        "username": input("\nUsername: ").strip(),
        "password": getpass("Password: "),
    }
    getpass("Enable Secret (press Enter to skip): ")   # reserved for future use

    commands = ask_commands()
    if not commands:
        print("No commands provided. Exiting.")
        return

    results: list[dict] = []

    # ── Per-device loop ────────────────────────────────────────────────────────
    for host in devices:
        print(f"\n  Connecting {host}...", end="  ", flush=True)
        client = connect(host, creds)

        if client is None:
            print("FAILED")
            results.append({
                "host": host, "connected": False,
                "ok": 0, "warn": [], "fail": len(commands), "dir": None,
            })
            continue

        print("Connected ✓")
        try:
            r = run_commands(client, host, commands)
            r["connected"] = True
            results.append(r)
        finally:
            try:
                client.close()
            except Exception:
                pass

    # ── Final summary ──────────────────────────────────────────────────────────
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{SEP}")
    print(f"  COLLECTION SUMMARY  —  {now}")
    print(f"  Devices: {len(results)}  |  Commands per device: {len(commands)}")
    print(SEP)

    print(f"  {'DEVICE':<22} {'STATUS':<24} {'OK':>4} {'WARN':>5} {'FAIL':>5}")
    print(f"  {'-'*22} {'-'*24} {'-'*4} {'-'*5} {'-'*5}")

    any_warn = False
    for r in results:
        if not r["connected"]:
            tag = "CONNECTION FAILED"
        elif r["warn"] and r["fail"]:
            tag = "WARNING + FAILED"
            any_warn = True
        elif r["warn"]:
            tag = "WARNING"
            any_warn = True
        elif r["fail"]:
            tag = "FAILED"
        else:
            tag = "OK"

        print(f"  {r['host']:<22} {tag:<24} {r['ok']:>4} {len(r['warn']):>5} {r['fail']:>5}")

    print(SEP)

    for r in results:
        if r["connected"] and r["dir"]:
            print(f"  {r['host']:<22} → {r['dir']}")

    if any_warn:
        print(f"\n{BANG}")
        print("  INVALID / WARNING COMMANDS")
        print(BANG)
        for r in results:
            if r.get("warn"):
                print(f"  Device : {r['host']}")
                for cmd, reason in r["warn"]:
                    print(f"    Command : {cmd}")
                    print(f"    Reason  : {reason}")
                print()
        print(BANG)

    print("\nDone.\n")


if __name__ == "__main__":
    main()
