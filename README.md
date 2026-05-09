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
- Supports multi-keyword search a block is returned if **any** of the given strings matches
- Optional prefix filtering to narrow results to a specific block type
- Deduplicates results each matching block is printed only once
- Custom config file paths via CLI argument

---

## Requirements

- Python 3.10+
- Uses only Python standard library modules (`argparse`, `sys`) no `pip install` required

---

## Installation

```bash
git clone https://github.com/pyquerci/f5finder.git
cd f5finder
```

No installation required. Run directly with Python.

### Windows

A pre-compiled Windows executable is included in the repository, built with [PyInstaller](https://pyinstaller.org/) 6.19.0. No Python installation is needed, just download and run `f5finder.exe`. For convenience, you can add it to a folder in your system `PATH` to invoke it from any directory.

---

## Usage

```
f5finder.py [-c BIGIP_BASE BIGIP] -f string [string ...] [-s prefix [prefix ...]]
```

### Arguments

| Argument | Description |
|---|---|
| `-h, --help` | Show the help message and exit |
| `-c, --config BIGIP_BASE BIGIP` | Custom BIG-IP config files (base and main). Accepts plain filenames (looked up in the current directory) or full/relative paths. Defaults to `bigip_base.conf` and `bigip.conf` in the current directory |
| `-f, --find string [string ...]` | One or more strings to search inside configuration blocks (**required**) |
| `-s, --startswith prefix [prefix ...]` | Filter results: only print blocks starts with the given prefix(es) |

If a file is not found or cannot be read due to permission issues, `f5finder` exits with a clear error message.

### Examples

```bash
# Search for all configuration blocks containing "cache-path"
f5finder.py -f cache-path

# Search for all configuration blocks containing any of the listed strings
f5finder.py -f %2 %4 VLAN_1024 VLAN_1025

# Search for "VLAN_1024" only in "ltm virtual" blocks, using custom config files
f5finder.py -c base.conf main.conf -f VLAN_1024 -s "ltm virtual"

# Print all blocks of type "apm" (empty string matches everything)
f5finder.py -f "" -s "apm"
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

---

## Shell Integration

`f5finder` prints results to standard output, so it integrates naturally with any Linux/Unix shell pipeline. The following are just a few examples of what you can do with standard Linux shell syntax (`|`, `>`, `>>`):

```bash
# Filter results further with grep
f5finder.py -f VLAN_1024 | grep "destination"

# Save results to a file
f5finder.py -f VLAN_1024 > results.txt

# Append results to an existing file
f5finder.py -f VLAN_1025 >> results.txt

# Count the number of matching entries
f5finder.py -f VLAN_1024 | grep -c "ltm virtual"
```

This syntax is **not natively available on Windows**. To use it on Windows, you need one of the following:

- **WSL** (Windows Subsystem for Linux) provides a native Linux shell environment directly on Windows
- **Cmder** a popular open source terminal emulator for Windows (MIT license) that supports Unix-style commands and piping

---

## License

This project is licensed under the **GNU General Public License v2.0 (GPLv2)**. You are free to use, modify, and distribute this software under the terms of that license. See the [LICENSE](LICENSE) file for the full license text.
