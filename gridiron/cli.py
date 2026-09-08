"""The command line: proofs, check, summary, and nothing chatty."""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="gridiron")
    commands = parser.add_subparsers(dest="command")
    commands.add_parser(
        "proofs", help="every proof with its verdict"
    )
    commands.add_parser(
        "check", help="exit nonzero if any proof is broken"
    )
    commands.add_parser(
        "summary", help="one line: N proofs (M broken)"
    )
    args = parser.parse_args(argv)
    from gridiron.proofs import registry

    if args.command == "proofs":
        print(registry.report())
        return 0
    if args.command == "check":
        failing = registry.broken()
        if failing:
            print(
                "broken: " + ", ".join(failing)
            )
            return 1
        print("all proofs hold")
        return 0
    if args.command == "summary":
        findings = registry.all_findings()
        failing = sum(
            1 for finding in findings if not finding.holds
        )
        print(
            f"{len(findings)} proofs ({failing} broken)"
        )
        return 1 if failing else 0
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
