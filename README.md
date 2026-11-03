# Network Device Command Downloader

A lightweight, terminal-based CLI tool to connect to network devices via SSH, run `show` commands, detect command syntax errors/warnings, and export the output into organized `.txt` files.

---

## Features

- **Multi-Device Support**: Target one or multiple network devices in a single execution.
  - Enter single IP: `192.168.1.1`
  - Enter multiple IPs (comma/space-separated): `192.168.1.1, 192.168.1.2`
  - Or supply a `.txt` file containing a list of IPs.
- **CLI Error & Warning Detection**:
  - Automatically identifies invalid command responses (e.g., `% Invalid input detected at '^' marker.`, `% Incomplete command`, `% Ambiguous command`, `% Unknown command`).
  - Marks command execution status as `WARNING`.
  - Highlights all flagged commands and exact device error notices in the **Final Collection Summary**.
- **Secure Credentials**: Uses `getpass` to mask passwords and enable secrets in the terminal.
- **Flexible Command Input**:
  - **Manual Entry**: Type commands directly in terminal and finish with `done`.
  - **File-based Entry**: Load batch commands from a `.txt` file (ignores comments `#` and blank lines).
- **Organized Output**:
  `output/<IP>/<YYYYMMDD_HHMMSS>/<NN>_<command>.txt`
- **Audit Headers**: Each file records device IP, executed command, timestamp, execution status (`SUCCESS` or `WARNING`), and full raw terminal output.
- **Logging**: Session activities and errors logged to `logs/collector.log`.

---

## Prerequisites

Python 3.8+ with `netmiko`:

```bash
pip install netmiko pyyaml
```

---

## Usage

### 1. Run the script

```bash
python fetch_cmds.py
```

### 2. Enter Target Devices & Credentials

```text
=================================================================
       NETWORK DEVICE COMMAND DOWNLOADER (MULTI-DEVICE)
=================================================================

Enter Target Device(s):
  - Single IP (e.g. 192.168.1.1)
  - Multiple IPs comma or space separated (e.g. 192.168.1.1, 192.168.1.2)
  - Or path to a TXT file with IP addresses (e.g. devices.txt)

IP(s) or File: 192.168.68.119, 192.168.68.120

Target Devices (2): 192.168.68.119, 192.168.68.120

Username: cisco
Password: 
Device Type [cisco_ios]: 
Enable Secret (optional): 
```

### 3. Choose Command Input Method

#### Option 1: Enter commands manually
```text
Select Command Input Method:
1. Enter commands manually
2. Load commands from TXT file

Choice: 1
Enter commands. Type 'done' to finish.
cmd> sh version
cmd> sh ip int brief
cmd> done
```

#### Option 2: Load commands from a file
Point to a file like `sh_config.txt`:
```text
Choice: 2
TXT file path: sh_config.txt
```

---

## Output & Warning Highlighting

If an invalid command is executed (such as `shhh ip`), the script marks it in real time and highlights it in the final summary:

```text
=================================================================
                     FINAL COLLECTION SUMMARY
=================================================================
Device: 192.168.68.119     | Status: WARNING (1 invalid command(s))
  -> Success: 2 | Warnings: 1 | Failed: 0
  -> Folder : output\192.168.68.119\20261103_124057

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
          HIGHLIGHTED WARNINGS / INVALID COMMANDS
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

Device [192.168.68.119]:
  * Command : 'shhh ip'
    Notice  : % Invalid input detected at '^' marker.
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
```

And in the saved text file (`03_shhh_ip.txt`):
```text
Device: 192.168.68.119
Command: shhh ip
Timestamp: 2026-11-03 12:40:59.426517
Status: WARNING (% Invalid input detected at '^' marker.)
============================================================
shhh ip
        ^
% Invalid input detected at '^' marker.

cisco#
```
