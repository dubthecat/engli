"""Runtime module loader: make `Import ... from "./mod"` actually resolve and run.

A compiled Engli program emits ordinary `from mod import ...` / `import mod`.
We register an import hook on sys.meta_path that, when Python looks up a module,
finds `<name>.engli` in the search dirs, compiles it to Python, and execs it as
a real module. So cross-.engli imports (and the Engli stdlib) Just Work at
runtime, including transitive imports, with Python's own module caching.
"""
import importlib.abc
import importlib.util
import os
import sys
from typing import Any

from .compiler import compile_source

STDLIB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stdlib")
LANG_DIR = os.path.dirname(os.path.abspath(__file__))


class EngliLoader(importlib.abc.Loader):
    def __init__(self, path):
        self.path = path

    def create_module(self, spec):
        return None  # default module creation

    def exec_module(self, module):
        src = open(self.path, encoding="utf-8").read()
        code = compile_source(src, "python")
        module.__dict__.setdefault("Any", Any)   # typed modules may reference Any
        module.__file__ = self.path
        exec(compile(code, self.path, "exec"), module.__dict__)


class EngliFinder(importlib.abc.MetaPathFinder):
    def __init__(self, dirs):
        self.dirs = list(dirs)

    def find_spec(self, name, path, target=None):
        base = name.split(".")[-1]
        for d in self.dirs:
            p = os.path.join(d, base + ".engli")
            if os.path.isfile(p):
                return importlib.util.spec_from_loader(name, EngliLoader(p))
        return None   # not an Engli module -> fall through to normal import


_installed = None


def install(extra_dirs=()):
    """Register the Engli import hook. Idempotent per process; extends search dirs."""
    global _installed
    dirs = [*extra_dirs, STDLIB_DIR]
    if _installed is None:
        _installed = EngliFinder(dirs)
        sys.meta_path.insert(0, _installed)
    else:
        for d in dirs:
            if d not in _installed.dirs:
                _installed.dirs.insert(0, d)
    # let compiled Engli reach the Engli stdlib dir and the Python runtime helpers
    for d in (LANG_DIR, STDLIB_DIR, *extra_dirs):
        if d not in sys.path:
            sys.path.insert(0, d)
    return _installed


def run_file(path):
    """Compile and execute an .engli file as __main__, with imports resolving."""
    path = os.path.abspath(path)
    install([os.path.dirname(path)])
    src = open(path, encoding="utf-8").read()
    code = compile_source(src, "python")
    ns = {"__name__": "__main__", "__file__": path, "Any": Any}
    exec(compile(code, path, "exec"), ns)
    return ns
