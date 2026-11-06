#!/usr/bin/env python3
"""engli-lang — compile/run Engli, transcode other sources, serve a built site.

    engli-lang compile FILE [--target python|typescript|english] [--no-boost] [-o OUT]
    engli-lang run FILE                      # run (cross-.engli imports resolve)
    engli-lang transcode FILE.html [--to typescript]
    engli-lang serve DIR [--port 8000]       # preview a built static site
"""
import argparse
import sys

from .compiler import compile_source, TARGETS
from .backends import PythonBackend, TypeScriptBackend, EnglishBackend
from .html_frontend import parse_html
from .loader import run_file
from .langinfo import VERSION


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    ap = argparse.ArgumentParser(prog="engli-lang")
    ap.add_argument("--version", action="version", version=f"engli-lang {VERSION}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("compile", help="Engli source -> target code")
    c.add_argument("file")
    c.add_argument("--target", default="python", choices=sorted(TARGETS))
    c.add_argument("--no-boost", action="store_true", help="disable phrase-map boost")
    c.add_argument("-o", "--out")

    r = sub.add_parser("run", help="run an .engli file (imports resolve at runtime)")
    r.add_argument("file")

    t = sub.add_parser("transcode", help="transcode another source (e.g. HTML) to a target")
    t.add_argument("file")
    t.add_argument("--to", default="typescript", choices=sorted(TARGETS))

    s = sub.add_parser("serve", help="serve a built static-site directory")
    s.add_argument("dir")
    s.add_argument("--port", type=int, default=8000)

    a = ap.parse_args(argv)

    if a.cmd == "compile":
        src = open(a.file, encoding="utf-8").read()
        code = compile_source(src, a.target, boost=not a.no_boost)
        if a.out:
            open(a.out, "w", encoding="utf-8").write(code)
            print(f"wrote {a.out}")
        else:
            sys.stdout.write(code)
        return 0

    if a.cmd == "run":
        run_file(a.file)
        return 0

    if a.cmd == "transcode":
        html = open(a.file, encoding="utf-8").read()
        program = parse_html(html)
        backend = {"python": PythonBackend, "typescript": TypeScriptBackend,
                   "english": EnglishBackend}[a.to]()
        sys.stdout.write(backend.generate(program))
        return 0

    if a.cmd == "serve":
        from .webruntime import serve
        serve(a.dir, a.port)
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
