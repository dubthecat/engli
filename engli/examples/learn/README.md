# Learn Engli — the Education module

A small, self-building course that teaches Engli, written in Engli. It is the
reference example for the reusable `learn` stdlib module.

- `curriculum.engli` — the lessons, as data only (no side effects), so both the
  site builder and the test suite import it. Each lesson carries its code and
  the output that code produces.
- `build.engli` — turns the curriculum into a static site (a syllabus home page
  plus one page per lesson), styled by the `learn` module and **pinned to the
  running language version** via `langinfo` (the footer shows `Engli vX.Y.Z`).

```bash
engli-lang run build.engli      # writes public/*.html
engli-lang serve public         # preview on http://localhost:8000
```

## Why it can't drift

The gate (`engli/tests/test_lang.py`) imports the curriculum, runs every
lesson's code, and asserts the result equals the output the lesson shows. If a
language change alters a result, the course fails the suite until it is updated
— so the tutorials always match the compiler they ship with.

## Reuse it for your own course

```engli
Import course_page, lesson, lesson_card, syllabus from "learn".
```

`lesson(title, body, code, shows)` renders one lesson (Markdown body, a code
block, and a result chip); `lesson_card(...)` / `syllabus(...)` build the index;
`course_page(title, menu, body)` wraps it all with the version-pinned footer.
