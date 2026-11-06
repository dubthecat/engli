# Architecture

Engli is a conventional compiler with an unconventional surface. The design goal
is that **the AST is the language** — English is one way to write it and one way
to read it back, but every target is generated from the same tree, never from
the text.

```
            ┌── PythonBackend     → Python (typed)
source ──► lexer ──► parser ──► AST ──┼── TypeScriptBackend → TypeScript (typed)
 (.engli)                             └── EnglishBackend    → Engli (round-trip)
HTML ────► html_frontend ──────► AST ─┘           ▲
                                                  └── boost layer (phrase-maps)
```

## The front end

**`lexer.py`** turns source text into tokens. Whitespace and newlines are
insignificant; blocks open with `:` and close with `End.`, and simple statements
end with `.`. Strings use double quotes with `\n`/`\"` escapes; member access is
the English possessive `'s` (`record's keys()`). A `.` is only part of a number
when a digit follows, so `Show 0.` ends the statement cleanly.

**`parser.py`** is a hand-written recursive-descent parser. Keywords are
*contextual* — `is greater than or equal to`, `For each`, `Define function …
taking … giving …`, `Import … from …` — matched by position, not reserved
globally, which is what lets the surface read like prose. Expression precedence,
low to high: `or · and · not · comparison · additive · multiplicative · unary ·
postfix · primary`.

**`ast.py`** defines the shared node types (the dataclasses every stage speaks):
expressions (`Num`, `Str`, `Name`, `ListLit`, `DictLit`, `Binary`, `Call`,
`Member`, `Index`, `PromptLookup`, …), statements (`Let`, `Assign`, `Func`, `If`,
`ForEach`, `While`, `Return`, `Show`, `Import`, `Snippet`, `RunCommand`, …) and
the type nodes (`TypeName`, `ListOf`, `MapOf`).

## The back ends (`backends/`)

Each backend walks the AST and emits one target. They share nothing but the
tree:

- **`python_backend.py`** — Python with type hints (`a: float`, `-> str`),
  `__all__` for exports, `__import__("subprocess")` for resolved commands.
- **`typescript_backend.py`** — TypeScript with annotations, `===`, `export`,
  and `document.createElement` for transcoded HTML.
- **`english_backend.py`** — prints the AST back as Engli. Because it is a true
  inverse, `source → english → python` equals `source → python`; the test suite
  asserts it.

A second front end, **`html_frontend.py`**, parses HTML into the *same* AST, so
`transcode page.html --to typescript` is just a different source feeding the same
backends.

## The orchestrator (`compiler.py`)

`compile_source(src, target, boost=True)` parses once and dispatches to a
backend. `run_python(src)` compiles to Python and executes it. When `boost` is
on, three **resolvers** are handed to the backend:

- `snippet(phrase)` — expand `Use snippet "…"` from the function/code maps.
- `command(phrase)` — resolve `Run "…"` to a shell command (fuzzy-matched).
- `prompt(title)` — expand `prompt "…"` to a system-prompt string.

## The boost layer (`boost/`)

The maps that back the resolvers **ship with the package** as bundled starter
data (`boost/__init__.py`: `FUNCTIONS`, `CODES`, `COMMANDS`, `PROMPTS`). This is
what keeps the package self-contained: boost works with nothing else installed.
When Engli is embedded in a larger repository that carries richer phrase-maps,
`_load_maps()` overlays those on top of the bundled set — enrichment, never a
requirement. Commands are read-only and safe by contract.

## The runtime loader (`loader.py`)

Compiled Engli emits ordinary `import mod` / `from mod import …`. An import hook
on `sys.meta_path` intercepts those: when Python looks up a module, the finder
locates `<name>.engli` in the search dirs, compiles it to Python, and executes it
as a real module. So cross-`.engli` imports — and the whole Engli-written
standard library — just work at runtime, with Python's own module caching and
transitive imports. `install(extra_dirs)` registers the hook; `run_file(path)`
runs a file as `__main__` with its directory on the path.

## The standard library (`stdlib/*.engli`)

Written in Engli, loaded through the hook above:

- **`text`, `lists`, `numbers`, `records`** — everyday helpers.
- **`web`** — HTML builders, `extend(...)` template inheritance, `markdown(...)`.
- **`learn`** — the education module: `lesson`, `syllabus`, version-pinned
  `course_page`.
- **`shop`** — storefront components over the pricing/checkout runtime.

## The web runtime (`webruntime.py`)

The thin, mostly-standard-library glue Engli shouldn't do by hand: writing files,
a preview server, a dependency-free Markdown subset, and the storefront
(`compute_totals` — the one authoritative pricing function; `checkout_session` —
real Stripe SDK or an offline demo; `storefront` — a static server with a
`POST /checkout` endpoint; `shop_script` — the browser cart).

## Versioning (`langinfo.py`)

`VERSION` is the single source of truth, imported with no relative dependencies
so it resolves both as `engli.langinfo` and as the bare module `langinfo` that
compiled Engli can import. Bump it there and the package `__version__`, the CLI,
and every version-pinned page follow.

## Design rules

1. **One AST, many targets.** A new language feature is new AST + each backend; a
   new output language is one new backend.
2. **Additive, never destructive.** Changes extend the grammar, the maps, and the
   stdlib; they do not remove or repurpose what exists.
3. **Self-contained.** Every import is relative or standard library. The boost
   maps are bundled. The package is always extractable.
4. **Pure words.** The surface avoids underscores and symbol soup; it reads as
   English and uses classic punctuation.

## Extending Engli

- **A new statement or expression** → add a node in `ast.py`, parse it in
  `parser.py`, and emit it in each backend.
- **A new target language** → add a backend in `backends/` over the existing AST
  and register it in `compiler.TARGETS`.
- **A new library** → write a `.engli` module in `stdlib/` (loaded by the hook).
- **New boost knowledge** → add entries to `boost/` (additive; commands stay
  read-only).
