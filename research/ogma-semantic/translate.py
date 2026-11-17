#!/usr/bin/env python3
"""Exact-input external translator for a read-only NASA Ogma research control.

The ``strict`` mode is deliberately incorrect. This is not a proposed NASA
requirement translator and must not be used for operational monitoring.
"""

import os
import sys


SOURCE = "The temperature shall always be lower than or equal to 180 degrees"
OUTPUTS = {
    "faithful": "temperature <= 180",
    "strict": "temperature < 180",
}


def main():
    received = sys.stdin.read().strip()
    if received != SOURCE:
        print("Unexpected input requirement; refusing translation", file=sys.stderr)
        return 12
    mode = os.environ.get("OGMA_TRANSLATION_CASE", "")
    if mode not in OUTPUTS:
        print("Missing/unsupported OGMA_TRANSLATION_CASE", file=sys.stderr)
        return 13
    print(OUTPUTS[mode])
    return 0


if __name__ == "__main__":
    sys.exit(main())
