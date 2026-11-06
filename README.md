<h1 align="center">Engli</h1>

<p align="center"><b>An English-readable programming language for humans and agents.</b></p>

<p align="center">
  <img alt="version" src="https://img.shields.io/badge/version-0.1.0-e8a838">
  <img alt="license" src="https://img.shields.io/badge/license-MIT-5fd08a">
  <img alt="python" src="https://img.shields.io/badge/python-3.9%2B-7cc4ff">
  <img alt="targets" src="https://img.shields.io/badge/targets-Python%20%7C%20TypeScript%20%7C%20English-b58cff">
</p>

Engli is a small, real programming language. You write it as plain, punctuated
English — `Let total be 0.` — and a genuine compiler (lexer → parser → a shared
AST → code generators) lowers it to **Python, TypeScript, or back to English**.
It reads like a sentence, but it is parsed like a language, not find-and-replaced
like a template.

It is built for two kinds of author: people who want to read and write code in
words, and agents that need a precise, inspectable surface to generate.

```engli
Let total be 0.
For each n in [1, 2, 3, 4, 5]:
    Set total to total plus n.
End.

Define function classify taking n as number giving text:
    If n is greater than or equal to 10:
        Return "big".
    Otherwise:
        Return "small".
    End.
End.

Show total.
Show classify(total).
```

```bash
$ engli run program.engli
15
big
```

## Install

```bash
pip install engli-lang            # from PyPI
# or, from a clone of this repo:
pip install .
```

Requires Python 3.9+ and nothing else. The optional `fuzzy` extra
(`pip install "engli-lang[fuzzy]"`) sharpens phrase-map matching; without it a
standard-library fallback is used.

## Use it

**CLI**

```bash
engli run program.engli                         # compile to Python and run
engli compile program.engli --target typescript # emit TypeScript
engli compile program.engli --target english    # pretty-print back to Engli
engli transcode page.html --to typescript        # transcode HTML to the AST, then a target
engli serve public                               # preview a built static site
engli --version
```

**Python API**

```python
import engli

print(engli.compile_source('Show 1 plus 1.\n'))     # print((1 + 1))
engli.run_python('Show "hello".\n')                  # hello
```

## One source, three targets

The same program lowers to every backend, because every backend consumes the
same AST.

| Engli | Python | TypeScript |
| --- | --- | --- |
| `Let x be true.` | `x = True` | `let x = true;` |
| `Show x.` | `print(x)` | `console.log(x);` |
| `If 1 is equal to 1:` | `if 1 == 1:` | `if (1 === 1) {` |

The **English** backend round-trips the AST back to Engli, so `source → English
→ Python` is byte-for-byte identical to `source → Python`. That is the proof the
AST — not the text — is the language.

## What's in the box

- **A real type system (optional).** `as number`, `as whole`, `as text`,
  `as truth`, `list of text`, `map of text to number`, or your own names — they
  lower to Python hints and TypeScript annotations.
- **A module system.** `Export`, `Import x from "./file"`, `Import module "m" as
  alias`. Cross-`.engli` imports **resolve and run** at runtime through an import
  hook, with Python's own module caching.
- **Records.** `{ "key": value }` literals compile to a Python dict or a
  TypeScript object; read them with the `records` module.
- **A standard library, written in Engli** — `text`, `lists`, `numbers`,
  `records`, a `web` site-builder, a `learn` education module, and a `shop`
  storefront.
- **A boost layer.** `Use snippet "…"`, `Run "…"`, and `prompt "…"` expand from
  bundled phrase-maps (`engli/boost/`) — so Engli stays in sync with its Python
  mappings, and the feature works with zero external data.
- **Pure words.** No underscore lingo; classic punctuation only (comma, period,
  quotation). Python builtins like `len`, `str`, and `sorted` are callable
  directly.

## Batteries: build a website, teach, sell

Three stdlib modules turn Engli into something you can ship a real project with
— each has a runnable example under `engli/examples/`.

```engli
Import heading, bullets, doc, save from "web".
save("public/index.html", doc("Hi", heading("Hello") plus bullets(["a", "b"]))).
```

- **`web`** — HTML builders, template inheritance, and a Markdown-to-page helper.
  See `examples/website/`.
- **`learn`** — an education module (lessons, a syllabus, version-pinned pages).
  It powers the course on [engli.org](https://engli.org); see `examples/learn/`.
- **`shop`** — a reusable Stripe storefront: product grid, a cart with a drawer,
  a discount-progress bar, and a checkout endpoint that prices every order
  **server-side** (the client never sends an amount). Real Stripe when a key is
  set, an offline demo otherwise. See `examples/shop/`.

## Architecture

```
            ┌── PythonBackend     → Python (typed)
source ──► lexer ──► parser ──► AST ──┼── TypeScriptBackend → TypeScript (typed)
 (.engli)                             └── EnglishBackend    → Engli (round-trip)
HTML ────► html_frontend ──────► AST ─┘           ▲
                                                  └── boost layer (phrase-maps)
```

One AST, many targets — that is what makes Engli a language rather than a
rewriter. The full tour is in [ARCHITECTURE.md](ARCHITECTURE.md).

## Project layout

```
engli/                 the package (import name: engli)
  lexer.py parser.py ast.py       the front end
  compiler.py                     orchestrator + the boost resolvers
  backends/                       python / typescript / english code generators
  loader.py                       the runtime import hook (cross-.engli imports)
  boost/                          bundled starter phrase-maps
  stdlib/*.engli                  the standard library, written in Engli
  webruntime.py                   file IO, a preview server, Markdown, the shop endpoint
  examples/                       website, learn, shop, and small programs
  langinfo.py                     VERSION — the single source of truth
tests/test_engli.py              the standalone gate
```

## Versioning

The version lives in one place, `engli/langinfo.py` (`VERSION`). The package
`__version__`, `engli --version`, and any Engli program (`Import module
"langinfo" as info.` then `info's badge()` → `"Engli v0.1.0"`) all read from it,
so documentation and tutorials can pin themselves to the exact compiler they
describe. Releases are logged in [CHANGELOG.md](CHANGELOG.md).

## Contributing

Run the gate before sending a change:

```bash
python tests/test_engli.py        # -> ENGLI OK
```

Keep the language surface pure words (no underscores), keep the package
self-contained (relative or standard-library imports only), and keep every
change additive. New stdlib modules are written in Engli; new targets are a new
backend over the same AST.

## License

MIT — see [LICENSE](LICENSE).
