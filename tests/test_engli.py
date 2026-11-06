#!/usr/bin/env python3
"""Standalone gate for the Engli language package.

Proves the package is self-contained: imports as ``engli`` and exercises the
compiler, the three backends, execution, the type and module systems, the
bundled boost layer, the standard library, and the example curriculum — with
nothing but this repository on the path. Run with ``python tests/test_engli.py``
(or ``pytest``).
"""
import io
import os
import sys
import tempfile
import importlib
import contextlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, os.pardir))
sys.path.insert(0, ROOT)

import engli
from engli import compile_source, run_python, __version__
from engli.loader import install, run_file
from engli.boost import BUNDLED
from engli.compiler import Resolvers

FAILS = []


def check(name, cond):
    print(("  PASS " if cond else "  FAIL ") + name)
    if not cond:
        FAILS.append(name)


def main():
    print(f"Engli {__version__} — standalone gate")

    # execution: loop + function + conditional
    src = ('Let total be 0.\n'
           'For each n in [1, 2, 3, 4]:\n'
           '    Set total to total plus n.\n'
           'End.\n'
           'Define function classify taking n:\n'
           '    If n is greater than or equal to 10:\n'
           '        Return "big".\n'
           '    Otherwise:\n'
           '        Return "small".\n'
           '    End.\n'
           'End.\n'
           'Show total.\nShow classify(total).\n')
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        run_python(src)
    check("executes loop+function+if to 10/big", buf.getvalue().split() == ["10", "big"])

    # three targets from one source
    check("python precedence", "(2 + (3 * 4))" in compile_source("Let x be 2 plus 3 times 4.\n", "python"))
    ts = compile_source('Let x be true.\nShow x.\n', "typescript")
    check("typescript codegen", "let x = true;" in ts and "console.log(x);" in ts)
    py1 = compile_source(src, "python")
    py2 = compile_source(compile_source(src, "english"), "python")
    check("english backend round-trips", py1 == py2)

    # types + modules
    check("python type hints", "a: float" in compile_source(
        'Define function f taking a as number giving text:\n Return "x".\nEnd.\n', "python"))
    check("python named import", "from util import a, b" in compile_source('Import a, b from "./util".\n', "python"))

    # bundled boost works with no external data
    r = Resolvers({k: dict(v) for k, v in BUNDLED.items()})
    check("bundled boost (snippet/prompt/command)",
          r.snippet("Create a dictionary named cache") == "cache = {}"
          and "linux terminal" in (r.prompt("Linux Terminal") or "").lower()
          and r.command("list files in the current directory") == "ls -la")

    # cross-.engli import resolves AND runs
    d = tempfile.mkdtemp()
    open(os.path.join(d, "lib.engli"), "w").write(
        'Export Define function twice taking n as number giving number:\n    Return n times 2.\nEnd.\n')
    open(os.path.join(d, "main.engli"), "w").write('Import twice from "./lib".\nShow twice(21).\n')
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        run_file(os.path.join(d, "main.engli"))
    check("cross-.engli import runs (twice(21)=42)", buf.getvalue().strip() == "42")

    # standard library + web stack
    install()
    text = importlib.import_module("text")
    web = importlib.import_module("web")
    check("stdlib text.upper/join", text.upper("hi") == "HI" and text.join(["a", "b"], "-") == "a-b")
    page = web.doc("T", web.heading("Hi") + web.bullets(["x", "y"]))
    check("web stack renders html", page.startswith("<!doctype html>") and "<h1>Hi</h1>" in page)

    # the Learn curriculum is honest: every lesson's shown output is real
    learn_dir = os.path.join(ROOT, "engli", "examples", "learn")
    install([learn_dir])
    curric = importlib.import_module("curriculum")
    honest = True
    for lsn in curric.lessons:
        b = io.StringIO()
        with contextlib.redirect_stdout(b):
            run_python(lsn["code"])
        if b.getvalue().strip() != lsn["shows"]:
            honest = False
    check(f"Learn curriculum output is produced by its code ({len(curric.lessons)} lessons)", honest)

    # storefront pricing is server-authoritative
    rt = importlib.import_module("webruntime")
    cat = [{"id": "a", "name": "A", "price": 5000}, {"id": "b", "name": "B", "price": 3000}]
    t = rt.compute_totals(cat, [{"id": "a", "quantity": 2}, {"id": "b", "quantity": 1}], threshold=12000, percent=15)
    check("shop prices from catalog, discount over threshold",
          t["subtotal"] == 13000 and t["discount"] == 1950 and t["total"] == 11050)

    print()
    if FAILS:
        print(f"FAIL — {len(FAILS)} check(s)")
        return 1
    print("ENGLI OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
