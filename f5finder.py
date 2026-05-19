# Author: Andrea Querci
# version: 1.0.0
# project: https://github.com/pyquerci/f5finder
# license: GPLv2

import argparse
import re
import sys
from pathlib import Path
import ipaddress

DEFAULT_BIGIP_BASE = "bigip_base.conf"
DEFAULT_BIGIP = "bigip.conf"

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

IPV4_RE = re.compile(
    r'(?<![\d.])'
    r'('
    r'(?:\d{1,3}\.){3}\d{1,3}'
    r'(?:/\d{1,2})?'
    r')'
    r'(?![\d.])'
)

class F5Config:
    def __init__(self, bigip_base: str, bigip: str) -> None:
        self.bigip_base = bigip_base
        self.bigip = bigip
        self.blocks = self._get_blocks()

    def find(
        self,
        find: list[str] | None = None,
        find_starts: list[str] | None = None,
        find_ends: list[str] | None = None,
        find_words: list[str] | None = None,
        find_nets: list[str] | None = None,
        exclude: list[str] | None = None,
        exclude_starts: list[str] | None = None,
        exclude_ends: list[str] | None = None,
        exclude_words: list[str] | None = None,
        exclude_nets: list[str] | None = None,
        find_menu: list[str] | None = None,
        exclude_menu: list[str] | None = None,
        section_print: bool = False
    ) -> None:

        cache: set[str] = set()

        for block in self.blocks:

            # exclude filter
            excluded = False

            if exclude:
                excluded = any(ex in block for ex in exclude)

            if exclude_starts and not excluded:
                excluded = any(
                    re.search(rf"(?<!\S){re.escape(ex)}\S*", block)
                    for ex in exclude_starts
                )

            if exclude_ends and not excluded:
                excluded = any(
                    re.search(rf"\S*{re.escape(ex)}(?!\S)", block)
                    for ex in exclude_ends
                )

            if exclude_words and not excluded:
                excluded = any(
                    re.search(rf"(?<!\S){re.escape(ex)}(?!\S)", block)
                    for ex in exclude_words
                )

            if exclude_nets and not excluded:
                excluded = any(
                    self._net_lookup(block, net)
                    for net in exclude_nets
                )

            if excluded:
                continue

            # keep blocks if no "find filter" is applied
            has_include_filters = any([
                find,
                find_starts,
                find_ends,
                find_words,
                find_nets,
            ])

            matched = not has_include_filters

            # find filter
            if find and not matched:
                matched = any(s in block for s in find)

            if find_starts and not matched:
                matched = any(
                    re.search(rf"(?<!\S){re.escape(s)}\S*", block)
                    for s in find_starts
                )

            if find_ends and not matched:
                matched = any(
                    re.search(rf"\S*{re.escape(s)}(?!\S)", block)
                    for s in find_ends
                )

            if find_words and not matched:
                matched = any(
                    re.search(rf"(?<!\S){re.escape(w)}(?!\S)", block)
                    for w in find_words
                )

            if find_nets and not matched:
                matched = any(
                    self._net_lookup(block, net)
                    for net in find_nets
                )

            # print with section filter:
            if matched and block not in cache:
                first_line = block.splitlines()[0]

                if find_menu is None or any(
                    first_line.startswith(se)
                    for se in find_menu
                ):
                    if exclude_menu and any(
                        first_line.startswith(se)
                        for se in exclude_menu
                    ):
                        continue

                    cache.add(block)
                    if section_print:
                        print(first_line)
                    else:
                        print(block)

    def _get_blocks(self) -> list[str]:
        blocks: list[str] = []
        current: list[str] = []

        configs = (self.bigip_base, self.bigip)

        for config in configs:
            for line in config.splitlines():

                if any(line.startswith(prefix) for prefix in SECTIONS):
                    if current:
                        blocks.append("\n".join(current))

                    current = [line]

                elif current:
                    current.append(line)

            if current:
                blocks.append("\n".join(current))
                current = []

        return blocks

    def _net_lookup(self,
        line: str,
        target_network: str
    ) -> bool:

        if "/" not in target_network:
            target_network += "/32"

        target = ipaddress.ip_network(target_network, strict=False)

        for match in IPV4_RE.finditer(line):
            candidate = match.group(1)

            try:
                # network
                if "/" in candidate:
                    net = ipaddress.ip_network(candidate, strict=False)

                    # stessa rete
                    if net == target:
                        return True

                    # sottorete della target
                    if net.subnet_of(target):
                        return True

                else:
                    # host
                    ip = ipaddress.ip_address(candidate)

                    if ip in target:
                        return True

            except ValueError:
                pass

        return False


def valid_network(value: str) -> str:
    try:
        net = value if "/" in value else value + "/32"
        ipaddress.ip_network(net, strict=False)
        return value
    except ValueError:
        raise SystemExit(f"error: invalid network: {value}")


def load_file(path: str) -> str:
    file_path = Path(path)

    if not file_path.is_file():
        raise SystemExit(f"error: file not found: {path}")

    try:
        return file_path.read_text(encoding="utf-8")

    except PermissionError:
        raise SystemExit(f"error: permission denied: {path}")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        usage=(
            "%(prog)s [-c BIGIP_BASE BIGIP] "
            "[-f string [string ...]] "
            "[-Fs string [string ...]] "
            "[-Fe string [string ...]] "
            "[-Fw string [string ...]] "
            "[-Fn IPv4/PREFIX [IPv4/PREFIX ...]] "
            "[-e string [string ...]] "
            "[-Es string [string ...]] "
            "[-Ee string [string ...]] "
            "[-Ew string [string ...]] "
            "[-En IPv4/PREFIX [IPv4/PREFIX ...]] "
            "[-Fm string [string ...]] "
            "[-Em string [string ...]] "
            "[-p]"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=(
            "description:\n"
            "  search and filter configuration blocks in F5 BIG-IP files\n"
            "  unix pipes are also supported\n\n"

            "about:\n"
            "  author: Andrea Querci\n"
            "  version: 1.0\n"
            "  project: https://github.com/pyquerci/f5finder\n"
            "  license: GPLv2\n\n"
        ),
    )

    parser.add_argument(
        "-c",
        "--config",
        nargs=2,
        metavar=("BIGIP_BASE", "BIGIP"),
        help="BIG-IP config files (base and main)",
    )

    parser.add_argument(
        "-f",
        "--find",
        nargs="+",
        help="contains match (*STRING*)",
    )

    parser.add_argument(
        "-Fs",
        "--find-startswith",
        nargs="+",
        help="prefix match (STRING*)",
    )

    parser.add_argument(
        "-Fe",
        "--find-endswith",
        nargs="+",
        help="suffix match (*STRING)",
    )

    parser.add_argument(
        "-Fw",
        "--find-word",
        nargs="+",
        help="exact match (STRING)",
    )

    parser.add_argument(
        "-Fn",
        "--find-network",
        nargs="+",
        type=valid_network,
        help="IP/network match (*IPv4/PREFIX*)",
    )

    parser.add_argument(
        "-e",
        "--exclude",
        nargs="+",
        help="exclude contains match (*STRING*)",
    )

    parser.add_argument(
        "-Es",
        "--exclude-startswith",
        nargs="+",
        help="exclude prefix (STRING*)",
    )

    parser.add_argument(
        "-Ee",
        "--exclude-endswith",
        nargs="+",
        help="exclude suffix (*STRING)",
    )

    parser.add_argument(
        "-Ew",
        "--exclude-word",
        nargs="+",
        help="exclude exact match (STRING)",
    )

    parser.add_argument(
        "-En",
        "--exclude-network",
        nargs="+",
        type=valid_network,
        help="exclude IP/network match (*IPv4/PREFIX*)",
    )

    parser.add_argument(
        "-Fm",
        "--find-menu",
        nargs="+",
        help="filter by section header (STRING*)",
    )

    parser.add_argument(
        "-Em",
        "--exclude-menu",
        nargs="+",
        help="exclude by section header (STRING*)",
    )

    parser.add_argument(
        "-p",
        "--print",
        action="store_true",
        help="print first line only",
    )

    args = parser.parse_args()

    return args


def main() -> None:
    args = parse_arguments()

    has_stdin = not sys.stdin.isatty()

    if has_stdin:
        piped_input = sys.stdin.read()
        bigip_base = ""
        bigip = piped_input

    else:
        if args.config:
            bigip_base_file, bigip_file = args.config
        else:
            bigip_base_file = DEFAULT_BIGIP_BASE
            bigip_file = DEFAULT_BIGIP

        bigip_base = load_file(bigip_base_file)
        bigip = load_file(bigip_file)

    config = F5Config(
        bigip_base=bigip_base,
        bigip=bigip,
    )

    config.find(
        find=args.find,
        find_starts=args.find_startswith,
        find_ends=args.find_endswith,
        find_words=args.find_word,
        find_nets=args.find_network,
        find_menu=args.find_menu,
        exclude=args.exclude,
        exclude_starts=args.exclude_startswith,
        exclude_ends=args.exclude_endswith,
        exclude_words=args.exclude_word,
        exclude_nets=args.exclude_network,
        exclude_menu=args.exclude_menu,
        section_print=args.print,
    )


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        pass
