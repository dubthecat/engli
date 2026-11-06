"""Engli language metadata — the single source of truth for the version.

This module is imported two ways and so must stay free of relative imports:
  * as ``engli.lang.langinfo`` inside this package, and
  * as a bare top-level module ``langinfo`` from compiled Engli programs
    (``Import module "langinfo" as info``), resolved on sys.path by the loader.

Bump VERSION here and everything — the CLI, the package __version__, and any
Engli program that shows ``info's badge()`` — follows.
"""
VERSION = "0.1.0"
NAME = "Engli"
TAGLINE = "an English-readable programming language for humans and agents"


def version():
    """The current Engli language version, e.g. ``0.1.0``."""
    return VERSION


def badge():
    """A short label a page can show to pin itself to this version."""
    return NAME + " v" + VERSION
