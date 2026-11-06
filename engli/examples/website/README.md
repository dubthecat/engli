# Build a website in Engli — a student walkthrough

You will build a real, multi-page website by writing plain English. No
framework, no build tools, no JavaScript required. Just Engli.

## What you need

Python 3 and this repo. That's it. The site you build is plain static HTML you
can host anywhere.

## 1. The idea

A web page is just text (HTML). In Engli, **a page is a function that returns
that text**, and the `web` standard-library module gives you friendly builders
so you never write raw tags:

```engli
Import heading, paragraph, doc, save from "web".

Let page be doc("Hello", heading("Hi!") plus paragraph("My first page.")).
call save with "public/index.html", page.
```

- `heading("Hi!")` -> `<h1>Hi!</h1>`
- `paragraph(...)` -> `<p>...</p>`
- `doc(title, body)` wraps it in a full HTML5 page with clean built-in styling
  (and dark mode).
- `save` writes the file.

## 2. Build the example site

From this folder:

```bash
python3 -m engli.lang.cli run site.engli     # writes public/index.html + about.html
python3 -m engli.lang.cli serve public        # open http://localhost:8000
```

(Installed as a command it is just `engli-lang run site.engli` and
`engli-lang serve public`.)

## 3. Read `site.engli`

The whole site is one short file. Notice the pattern:

- `layout(title, body)` is a function that adds a shared nav bar to every page —
  that's how real sites avoid repeating themselves.
- `home` and `about` are each one page, built by calling element functions and
  gluing them with `plus` (string join) and `join([...])`.
- Two `save` calls write the two files.

## 4. Make it yours

Try these, re-run, and refresh:

1. Add a third page `contact` and a nav link to it.
2. Add a `bullets([...])` of your three favourite things to the home page.
3. Change the heading text, add a `button("Say hi")`.
4. Add an `image("logo.png", "my logo")` (drop a `logo.png` into `public/`).

## 5. The building blocks (`web` module)

| Engli | HTML |
|---|---|
| `heading(t)` / `subheading(t)` | `<h1>` / `<h2>` |
| `paragraph(t)` | `<p>` |
| `link(text, href)` | `<a href>` |
| `image(src, alt)` | `<img>` |
| `button(t)` | `<button>` |
| `bullets([...])` | `<ul><li>…` |
| `nav([...links])` | top navigation bar |
| `section(inner)` | `<section>` |
| `join([...])` | glue fragments into one string |
| `doc(title, body)` | full styled HTML page |

That is the whole stack: pages are functions, HTML is text, a page is saved to
a file, and `serve` previews it. When you understand this, you understand how
every website works.

## A bigger example: `cats.engli`

`cats.engli` is a complete, good-looking three-page site (home, breeds, care).
It shows the next level: **template inheritance** (`extend` with named blocks),
a **card grid**, a **photo grid**, and a **Markdown** page — all sharing one
layout. Build and serve it the same way:

```bash
engli-lang run cats.engli
engli-lang serve public
```
