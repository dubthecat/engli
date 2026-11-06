"""Engli Core — the real, formal Engli language.

A genuine compiler (lexer -> parser -> AST -> multi-target codegen), additive to
the historical phrase-map engines. Engli source is English-readable but formally
parsed, and lowers to multiple targets (Python, TypeScript). The phrase maps
(codemap/functionmap) remain available as a "boost" layer so Engli stays in sync
with its Python mappings instead of replacing them.
"""
from .langinfo import VERSION as __version__, NAME, TAGLINE
from .compiler import compile_source, run_python, TARGETS

__all__ = ["compile_source", "run_python", "TARGETS", "__version__", "NAME", "TAGLINE"]
