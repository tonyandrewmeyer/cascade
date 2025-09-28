#!/usr/bin/env python3

"""Script to run Cascade."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from pebble_shell.shell import main

if __name__ == "__main__":
    main()
