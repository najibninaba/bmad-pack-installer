"""Entry point for running bmad_pack_installer as a module."""

import sys
from .cli import cli

if __name__ == '__main__':
    sys.exit(cli())