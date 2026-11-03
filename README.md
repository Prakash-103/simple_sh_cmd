# Network Device Command Downloader

A lightweight, vendor-agnostic CLI tool built on pure **Paramiko** to connect to network devices via SSH, run commands through an interactive shell, detect CLI errors/warnings, and save each command's output into a clean `.txt` file.

---

## Key Features

- **Vendor-Agnostic (Pure Paramiko)**:
  - Uses standard interactive SSH shell sessions (`invoke_shell`).
  - Handles automatic prompt detection and paging bypass.
- **Multi-Device Support**:
  - Run against a single IP (`192.168.1.1`).
  - Run against multiple IPs separated by commas or spaces (`192.168.1.1, 192.168.1.2`).
  - Load target IPs directly from a text file (`sample_devices.txt`).
- **Flexible Command Input**:
  - **Manual Entry**: Enter commands directly into the terminal and finish by typing `done`.
  - **File-based Entry**: Load commands from a file like `sample_commands.txt` (ignores comments `#` and blank lines).
- **Clean Output Processing**:
  - Automatically strips echoed input commands and trailing device prompts (`hostname#` / `hostname>`).
  - Organizes files by device and timestamp:  
    `output/<IP>/<YYYYMMDD_HHMMSS>/<NN>_<command>.txt`
- **CLI Error & Warning Detection**:
  - Identifies CLI errors (e.g., `% Invalid input detected at '^' marker.`, `% Incomplete command`, `% Ambiguous command`, syntax errors).
  - Flags status as `WARNING`.
- **Concise, Non-Repetitive Summary**:
  - Structured summary table showing `DEVICE`, `STATUS`, `OK`, `WARN`, `FAIL`.
  - Highlights warning commands with only the command name and reason (does not dump raw output).

---

## Prerequisites & Installation

### Step 1: Install Python (if not already installed)

This tool requires **Python 3.8 or higher**.

#### Windows
1. **Via Official Installer**:
   - Download the latest Python installer from [python.org/downloads](https://www.python.org/downloads/).
   - Run the installer.
   - ⚠️ **IMPORTANT**: Check the box **"Add python.exe to PATH"** at the bottom of the first setup screen before clicking *Install Now*.
2. **Via Windows Terminal (winget)**:
   ```powershell
   winget install Python.Python.3.12
   ```

#### Linux (Ubuntu / Debian)
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv
```

#### macOS
```bash
# Using Homebrew:
brew install python
# Or download the macOS package from python.org/downloads
```

#### Verify Installation
Open a new terminal and verify:
```bash
# Check Python version (should be 3.8+)
python --version     # (or: python3 --version)

# Check pip package manager
pip --version        # (or: pip3 --version)
```

---

### Step 2: Install Project Dependencies

Choose either **Method 1** (recommended virtual environment) or **Method 2** (direct system install).

### Method 1: Using Virtual Environment (`venv`) — Recommended

Isolates package dependencies from your system/global Python environment.

#### Windows (PowerShell / CMD)
```powershell
# 1. Navigate to project folder
cd d:\practice\simple_sh_cmd

# 2. Create virtual environment
python -m venv .venv

# 3. Activate virtual environment
# In PowerShell:
.\.venv\Scripts\Activate.ps1
# (Or in Command Prompt: .\.venv\Scripts\activate.bat)

# 4. Install dependencies
pip install -r requirements.txt
# Or: pip install paramiko

# 5. Run the tool
python fetch_cmds.py

# 6. Deactivate when done
deactivate
```

> **Note for Windows PowerShell**: If you encounter an execution policy error when activating (`scripts is disabled on this system`), run:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

#### Linux / macOS (Bash / Zsh)
```bash
# 1. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt
# Or: pip install paramiko

# 3. Run the tool
python fetch_cmds.py

# 4. Deactivate when done
deactivate
```

---

### Method 2: Without Virtual Environment (Direct / Global Install)

Installs `paramiko` directly into your existing Python environment.

#### Windows
```powershell
# Install directly
pip install paramiko
# Or using requirements file:
pip install -r requirements.txt

# Run directly
python fetch_cmds.py
```

#### Linux / macOS
```bash
# Install directly (use --user if permissions are restricted)
pip install --user paramiko
# Or using requirements file:
pip install --user -r requirements.txt

# Run directly
python3 fetch_cmds.py
```

---

## Project Structure

```text
simple_sh_cmd/
├── fetch_cmds.py          # Main execution script (Paramiko-based)
├── requirements.txt       # Project dependencies (paramiko)
├── sample_devices.txt     # Sample target IP list file
├── sample_commands.txt    # Sample show commands file
├── logs/                  # Application logs
│   └── collector.log
└── output/                # Output files organized by device & run timestamp
    └── <IP>/
        └── <YYYYMMDD_HHMMSS>/
            ├── 01_sh_version.txt
            ├── 02_sh_ip_int_brief.txt
            └── ...
```

---

## Sample Input Files

### 1. `sample_devices.txt` (Target IPs)
Lines starting with `#` are treated as comments:
```text
# Core Routers
192.168.68.119
192.168.68.120

# Distribution Switches
10.10.10.1
10.10.10.2
```

### 2. `sample_commands.txt` (Commands)
```text
# Device Info
sh version
sh inventory
sh clock

# Interfaces
sh ip int brief
sh interfaces status
```

---

## Usage

### 1. Run the script

```bash
python fetch_cmds.py
```

### 2. Enter Target Devices and Credentials

```text
=================================================================
      NETWORK DEVICE COMMAND DOWNLOADER
=================================================================

Target Device(s):
  Single IP        :  192.168.1.1
  Multiple (comma) :  192.168.1.1, 192.168.1.2
  File             :  devices.txt

IP(s) or file: sample_devices.txt

  Devices (2): 192.168.68.119, 192.168.68.120

Username: cisco
Password: 
Enable Secret (press Enter to skip): 
```

### 3. Choose Command Input

```text
Command Input:
  1. Type manually
  2. Load from TXT file

Choice [1/2]: 2
TXT file path: sample_commands.txt
```

---

## Terminal Execution & Output Format

### Live Execution Progress:
```text
  Connecting 192.168.68.119...  Connected ✓
  [ 1/19] sh version              [OK]
  [ 2/19] sh inventory            [OK]
  [17/19] sh environment all      [WARNING]
  [18/19] sh logging              [OK]

  Connecting 192.168.68.120...  FAILED
```

### Final Collection Summary:
```text
=================================================================
  COLLECTION SUMMARY  —  2026-11-03 13:30:00
  Devices: 2  |  Commands per device: 19
=================================================================
  DEVICE                 STATUS                     OK  WARN  FAIL
  ---------------------- ------------------------ ---- ----- -----
  192.168.68.119         WARNING                    18     1     0
  192.168.68.120         CONNECTION FAILED           0     0    19
=================================================================
  192.168.68.119         → output\192.168.68.119\20261103_130612

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
  INVALID / WARNING COMMANDS
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
  Device : 192.168.68.119
    Command : sh environment all
    Reason  : % Invalid input detected at '^' marker.

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

Done.
```

### Clean Saved Command Output (`.txt` file)
Each file contains execution metadata and cleaned command output (without prompt artifacts or echoed input commands):

```text
Device    : 192.168.68.119
Command   : sh ip int brief
Timestamp : 2026-11-03 13:06:13.123456
Status    : SUCCESS
============================================================
Interface              IP-Address      OK? Method Status                Protocol
FastEthernet0/0        192.168.68.119  YES manual up                    up      
FastEthernet0/1        unassigned      YES unset  administratively down down    
```
