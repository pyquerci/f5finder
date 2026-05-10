# Author: Andrea Querci
# version: 1.0.0
# project: https://github.com/pyquerci/f5finder
# license: GPLv2


import argparse
from pathlib import Path

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


class F5Config:
    def __init__(self, bigip_base: str, bigip: str) -> None:
        self.bigip_base = bigip_base
        self.bigip = bigip
        self.sections = self._get_sections()

    def find(
        self,
        strings: list[str],
        startswith: list[str] | None = None,
    ) -> None:
        cache: set[str] = set()

        for string in strings:
            for block in self.sections:
                if string in block and block not in cache:
                    cache.add(block)

                    if startswith:
                        for prefix in startswith:
                            if block.startswith(prefix):
                                print(block)
                    else:
                        print(block)

    def _get_sections(self) -> list[str]:
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


def load_file(path: str) -> str:
    file_path = Path(path)

    if not file_path.is_file():
        raise SystemExit(
            f"error: file not found: {path}"
        )
    try:
        return file_path.read_text(encoding="utf-8")

    except PermissionError:
        raise SystemExit(
            f"error: permission denied: {path}"
        )


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        usage=(
            "%(prog)s [-c BIGIP_BASE BIGIP] "
            "-f string [string ...] "
            "[-s prefix [prefix ...]]"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=(
            "examples:\n"
            "  f5finder -f cache-path\n"
            "  f5finder -f %2 %4 VLAN_1024 VLAN_1025\n"
            "  f5finder -c base.conf main.conf -f VLAN_1024 -s \"ltm virtual\"\n"
            "  f5finder -f \"\" -s apm\n\n"

            "description:\n"
            "  search and filter configuration blocks in F5 BIG-IP files\n\n"

            "about:\n"
            "  author: Andrea Querci\n"
            "  version: 1.0\n"
            "  project: https://github.com/pyquerci/f5finder\n"
            "  license: GPLv2"
        ),
    )

    parser.add_argument(
        "-c",
        "--config",
        nargs=2,
        metavar=("BIGIP_BASE", "BIGIP"),
        help="custom BIG-IP config files (base and main)",
    )

    parser.add_argument(
        "-f",
        "--find",
        metavar="string",
        nargs="+",
        required=True,
        help="one or more strings to search inside configuration blocks",
    )

    parser.add_argument(
        "-s",
        "--startswith",
        metavar="prefix",
        nargs="+",
        help=(
            "filter results by matching the beginning "
            "of each configuration block"
        ),
    )

    return parser.parse_args()


def main() -> None:
    args = parse_arguments()

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
        strings=args.find,
        startswith=args.startswith,
    )


if __name__ == "__main__":
    main()
