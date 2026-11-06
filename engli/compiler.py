"""Compiler orchestrator: Engli source -> target code, plus the bridges that
keep Engli in sync with the historical phrase maps (functionmap, codemap,
commandmap, suggestionsmap) — upgraded as first-class language features, still
doing all the same things.
"""
import os
import re
import sys

from .parser import parse
from .backends import PythonBackend, TypeScriptBackend, EnglishBackend

TARGETS = {"python": PythonBackend, "typescript": TypeScriptBackend, "english": EnglishBackend}

_TRANSLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "translate")


def _load_maps():
    """Phrase maps for the boost layer.

    Starts from the bundled starter maps that ship inside the package, so boost
    works even when the package is extracted on its own — it is fully isolated
    and needs nothing from the rest of the repo. When the monorepo's richer
    ``engli/translate`` maps are present they are overlaid on top (enrichment,
    never a requirement). Never raises."""
    from .boost import BUNDLED
    maps = {k: dict(v) for k, v in BUNDLED.items()}
    if os.path.isdir(_TRANSLATE_DIR):
        if _TRANSLATE_DIR not in sys.path:
            sys.path.insert(0, _TRANSLATE_DIR)
        for module, attr, key in (("functionsmap", "functionmap", "function"),
                                  ("codesmap", "codemap", "code"),
                                  ("commandsmap", "commandmap", "command"),
                                  ("promptsmap", "suggestionsmap", "prompt")):
            try:
                extra = getattr(__import__(module), attr, {})
                maps[key].update({k: v for k, v in extra.items() if v is not None})
            except Exception:
                pass
    return maps


def _best_key(query, keys):
    """Fuzzy best key (fuzzywuzzy if present, else difflib), None if weak."""
    keys = list(keys)
    if not keys:
        return None
    try:
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            from fuzzywuzzy import process, fuzz
        hit = process.extractOne(query, keys, scorer=fuzz.token_sort_ratio)
        return hit[0] if hit and hit[1] >= 60 else None
    except Exception:
        import difflib
        m = difflib.get_close_matches(query, keys, n=1, cutoff=0.6)
        return m[0] if m else None


class Resolvers:
    """The map-boost bridges handed to a backend."""
    def __init__(self, maps):
        self.maps = maps

    def snippet(self, phrase):
        fmap, cmap = self.maps["function"], self.maps["code"]
        if phrase in fmap:
            return fmap[phrase].strip("\n")
        for pattern, template in cmap.items():
            try:
                m = re.fullmatch(pattern, phrase)
            except re.error:
                continue
            if m:
                out = template
                for i, g in enumerate(m.groups(), start=1):
                    out = out.replace("\\" + str(i), g if g is not None else "")
                return out
        return None

    def command(self, phrase):
        cmap = self.maps["command"]
        if phrase in cmap:
            return str(cmap[phrase])
        key = _best_key(phrase, cmap.keys())
        return str(cmap[key]) if key else None

    def prompt(self, title):
        pmap = self.maps["prompt"]
        if title in pmap:
            return str(pmap[title])
        key = _best_key(title, pmap.keys())
        return str(pmap[key]) if key else None


def _backend(target, boost):
    r = Resolvers(_load_maps()) if boost else None
    if r:
        return TARGETS[target](snippet_resolver=r.snippet,
                               command_resolver=r.command,
                               prompt_resolver=r.prompt)
    return TARGETS[target]()


def compile_source(src, target="python", boost=True):
    if target not in TARGETS:
        raise ValueError(f"unknown target {target!r}; choose from {sorted(TARGETS)}")
    program = parse(src)
    return _backend(target, boost).generate(program)


def run_python(src, boost=True, globs=None):
    code = compile_source(src, "python", boost=boost)
    ns = globs if globs is not None else {}
    # typed programs reference Any; provide it transparently
    if "Any" not in ns:
        from typing import Any
        ns["Any"] = Any
    exec(compile(code, "<engli>", "exec"), ns)
    return ns


# kept for backward compatibility with earlier callers/tests
def make_snippet_resolver():
    return Resolvers(_load_maps()).snippet
