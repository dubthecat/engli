# Changelog

All notable changes to the Engli language are recorded here. The version is the
single source of truth in `langinfo.py` (`VERSION`); the CLI (`engli-lang
--version`), the package `__version__`, and any Engli page that shows
`info's badge()` all read from it.

## 0.1.0 — first isolated release

The language, carved out as a self-contained, open-source-ready package.

### Language
- Lexer → recursive-descent parser → shared AST → multi-target codegen
  (Python, TypeScript, and English round-trip).
- Optional type annotations (`number`, `whole`, `text`, `truth`, `list of`,
  `map of ... to ...`, custom names).
- Module system: `Export`, `Import ... from "./mod"`, `Import module "m" as x`,
  with cross-`.engli` imports that resolve and run at runtime.
- Record/dict literals `{ "key": value }`.
- Pure-words surface: no underscore lingo, classic punctuation only.

### Standard library (written in Engli)
- `text`, `lists`, `numbers`, `records`, and a lean `web` website stack with
  template inheritance and a Markdown-to-page helper.

### Boost layer
- Phrase maps (`Use snippet`, `Run`, `prompt "..."`) now ship a bundled starter
  set inside the package, so boost works with zero external data. The richer
  monorepo maps are overlaid when present.

### Tooling
- `engli-lang compile | run | transcode | serve`, now with `--version`.
