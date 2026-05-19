# f5finder

A command-line tool to search and filter configuration blocks in F5 BIG-IP files.

---

## Overview

`f5finder` parses F5 BIG-IP configuration files (`bigip_base.conf` and `bigip.conf`) and lets you quickly locate specific configuration blocks by keyword. Results can be further filtered by block type (e.g. `ltm virtual`, `apm`, `net`), making it easy to navigate large and complex configuration files.

It is particularly useful during **migration activities**, when only specific portions of the configuration need to be imported onto a new device allowing you to extract exactly what you need without manually sifting through thousands of lines of configuration.

---

## Features

- Parses both `bigip_base.conf` and `bigip.conf` in a single run
- Searches across all major F5 configuration sections (`net`, `ltm`, `apm`, `auth`, `ilx`, `security`, `sys`, `pem`, `wom`)
- Multiple filter types: contains, prefix, suffix, exact word, IP/network, and section header — each available as include or exclude
- Supports multi-keyword search; a block is returned if **any** of the given strings matches
- Option to print only the first line of each matching block
- Deduplicates results; each matching block is printed only once
- Unix pipe support for integration with shell pipelines
- Custom config file paths via CLI argument

---

## Requirements

- Python 3.10+
- Uses only Python standard library modules (`argparse`, `re`, `pathlib`, `ipaddress`); no `pip install` required.

---

## Installation

```bash
git clone https://github.com/pyquerci/f5finder.git
cd f5finder
```

No installation required. Run directly with Python.

### Windows

A pre-compiled Windows executable is included in the repository, built with PyInstaller 6.19.0. No Python installation is needed, just download and run `f5finder.exe`. For convenience, you can add it to a folder in your system `PATH` to invoke it from any directory.

---

## Usage

```
f5finder.py [-c BIGIP_BASE BIGIP]
            [-f string [string ...]]
            [-Fs string [string ...]]
            [-Fe string [string ...]]
            [-Fw string [string ...]]
            [-Fn IPv4/PREFIX [IPv4/PREFIX ...]]
            [-e string [string ...]]
            [-Es string [string ...]]
            [-Ee string [string ...]]
            [-Ew string [string ...]]
            [-En IPv4/PREFIX [IPv4/PREFIX ...]]
            [-Fm string [string ...]]
            [-Em string [string ...]]
            [-p]
```

### Arguments

| Argument | Description |
|---|---|
| `-h, --help` | Show the help message and exit. |
| `-c, --config BIGIP_BASE BIGIP` | Custom BIG-IP config files. Accepts plain filenames (looked up in the current directory) or full/relative paths. Defaults to `bigip_base.conf` and `bigip.conf` in the current directory. |
| `-f, --find string [string ...]` | Include blocks containing any of the given strings (`*STRING*`). |
| `-Fs, --find-startswith string [string ...]` | Include blocks containing a token that starts with any of the given strings (`STRING*`). |
| `-Fe, --find-endswith string [string ...]` | Include blocks containing a token that ends with any of the given strings (`*STRING`). |
| `-Fw, --find-word string [string ...]` | Include blocks containing any of the given strings as an exact word (`STRING`). |
| `-Fn, --find-network IPv4/PREFIX [IPv4/PREFIX ...]` | Include blocks containing an IP address or subnet that falls within any of the given networks. |
| `-e, --exclude string [string ...]` | Exclude blocks containing any of the given strings (`*STRING*`). |
| `-Es, --exclude-startswith string [string ...]` | Exclude blocks containing a token that starts with any of the given strings (`STRING*`). |
| `-Ee, --exclude-endswith string [string ...]` | Exclude blocks containing a token that ends with any of the given strings (`*STRING`). |
| `-Ew, --exclude-word string [string ...]` | Exclude blocks containing any of the given strings as an exact word (`STRING`). |
| `-En, --exclude-network IPv4/PREFIX [IPv4/PREFIX ...]` | Exclude blocks containing an IP address or subnet that falls within any of the given networks. |
| `-Fm, --find-menu string [string ...]` | Filter results: only print blocks whose first line starts with any of the given prefixes (`STRING*`). |
| `-Em, --exclude-menu string [string ...]` | Exclude results: skip blocks whose first line starts with any of the given prefixes (`STRING*`). |
| `-p, --print` | Print only the first line of each matching block instead of the full block; it gives you a quick idea of which blocks you filtered. |

If no include filter (`-f`, `-Fs`, `-Fe`, `-Fw`, `-Fn`) is specified, all blocks are returned (subject to any active exclude filters). If a file is not found or cannot be read due to permission issues, `f5finder` exits with a clear error message.

### Examples

```bash
# Search for all configuration blocks containing "cache-path"
f5finder.py -f cache-path

# Search for all configuration blocks containing any of the listed strings
f5finder.py -f %2 %4 VLAN_1024 VLAN_1025

# Search for "VLAN_1024" only in "ltm virtual" blocks, using custom config files
f5finder.py -c base.conf main.conf -f VLAN_1024 -Fm "ltm virtual"

# Print all blocks of type "apm"
f5finder.py -Fm "apm"

# Find all blocks containing an IP in the 192.168.37.0/24 range
f5finder.py -Fn 192.168.37.0/24

# Find all "ltm virtual " blocks, excluding any that reference a specific pool
f5finder.py -Fm "ltm virtual " -Ee MY_POOL_NAME

# Print only the first line of each matching "net vlan" block
f5finder.py -Fm "net vlan" -p
```

---

## How It Works

BIG-IP configuration files use a C-like indented syntax with curly braces to delimit blocks. However, reliably parsing these files based on brace matching is not straightforward for two reasons:

- **iRules** can contain opening and closing braces that start at column zero (no indentation), which makes it impossible to detect block boundaries by brace depth alone.
- **Single-line directives** such as `pem global-settings analytics { }` open and close on the same line, further complicating any brace-based approach.

To work around this, `f5finder` uses a section-prefix strategy instead: a new configuration block is assumed to begin whenever a line starts with one of the known top-level prefixes defined in the `SECTIONS` list:

```python
SECTIONS = [
    "net ",
    "ltm ",
    "apm ",
    "auth ",
    "ilx ",
    "security ",
    "sys ",
    "pem ",
    "wom ",
]
```

The current block ends as soon as the next section header is encountered.

These prefixes were identified through direct study of BIG-IP configuration files. If your environment includes additional top-level sections not listed in `SECTIONS`, simply add the corresponding prefix to the list.

### IP/Network Matching

The `-Fn` and `-En` options accept one or more IPv4 addresses or CIDR prefixes. For each block, `f5finder` extracts all IPv4 addresses and subnets found in the text and checks whether any of them fall within the given target network. The following cases all count as a match:

- An exact host IP that belongs to the target network
- A subnet that is equal to the target network
- A subnet that is entirely contained within the target network

A bare IP address without a prefix (e.g. `10.0.0.1`) is treated as a `/32` host.

---

## Shell Integration

`f5finder` prints results to standard output, so it integrates naturally with any Linux/Unix shell pipeline. The following are just a few examples of what you can do with some standard Linux shell syntax:

```bash
# Filter results further with grep and awk
f5finder.py -Fm "ltm virtual " -f %8 | grep destination | awk "{print$2}"

# Save results to a file
f5finder.py -Fm "net vlan" | grep tag | awk "{print$NF}" | sort > all_vlans.txt

# Append results to an existing file
f5finder.py -f VLAN_1025 >> results.txt

# Count the number of matching entries
f5finder.py | grep -c "ltm virtual "

# Pipe output of one search into another
f5finder.py -Fm "ltm virtual " | f5finder -f MY_POOL
```

This syntax is **not natively available on Windows**. To use it on Windows, you need one of the following:

- **WSL** (Windows Subsystem for Linux) provides a native Linux shell environment directly on Windows
- **Cmder** a popular open source terminal emulator for Windows (MIT license) that supports Unix-style commands and piping

---

## License

This project is licensed under the **GNU General Public License v2.0 (GPLv2)**. You are free to use, modify, and distribute this software under the terms of that license. See the [LICENSE](LICENSE) file for the full license text.

---

## Donations

If you value the work and want to help support its development, feel free to make a donation. Your support will be greatly appreciated:

- PayPal: https://paypal.me/pyquerci
- Buy Me a Coffee: https://buymeacoffee.com/pyquerci
