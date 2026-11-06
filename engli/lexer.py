from .tokens import (Token, NUMBER, STRING, WORD, PERIOD, COLON, COMMA,
                     LPAREN, RPAREN, LBRACKET, RBRACKET, LBRACE, RBRACE, POSSESSIVE, EOF)
from .errors import LexError

_PUNCT = {".": PERIOD, ":": COLON, ",": COMMA,
          "(": LPAREN, ")": RPAREN, "[": LBRACKET, "]": RBRACKET,
          "{": LBRACE, "}": RBRACE}


def tokenize(src):
    """Turn Engli source text into a list of tokens (ending with EOF)."""
    toks = []
    i, line, col = 0, 1, 1
    n = len(src)

    def emit(kind, value):
        toks.append(Token(kind, value, line, col))

    while i < n:
        c = src[i]
        # whitespace (newlines are insignificant; blocks use ':' .. 'End.')
        if c in " \t\r\n":
            if c == "\n":
                line += 1; col = 1
            else:
                col += 1
            i += 1
            continue
        # line comment:  # ... to end of line
        if c == "#":
            while i < n and src[i] != "\n":
                i += 1
            continue
        # string literal
        if c == '"':
            j = i + 1; buf = []
            while j < n and src[j] != '"':
                if src[j] == "\\" and j + 1 < n:
                    nxt = src[j + 1]
                    buf.append({"n": "\n", "t": "\t", '"': '"', "\\": "\\"}.get(nxt, nxt))
                    j += 2; continue
                buf.append(src[j]); j += 1
            if j >= n:
                raise LexError("unterminated string", line, col)
            emit(STRING, "".join(buf))
            col += (j - i + 1); i = j + 1; continue
        # number
        if c.isdigit() or (c == "." and i + 1 < n and src[i + 1].isdigit()):
            j = i; dot = False
            while j < n and (src[j].isdigit() or
                             (src[j] == "." and not dot and j + 1 < n and src[j + 1].isdigit())):
                if src[j] == ".":
                    dot = True
                j += 1
            emit(NUMBER, src[i:j]); col += (j - i); i = j; continue
        # possessive 's  (member access)
        if c == "'" and i + 1 < n and src[i + 1] == "s" and (i + 2 >= n or not src[i + 2].isalnum()):
            emit(POSSESSIVE, "'s"); i += 2; col += 2; continue
        # word (identifier / contextual keyword)
        if c.isalpha() or c == "_":
            j = i
            while j < n and (src[j].isalnum() or src[j] == "_"):
                j += 1
            emit(WORD, src[i:j]); col += (j - i); i = j; continue
        # punctuation
        if c in _PUNCT:
            emit(_PUNCT[c], c); i += 1; col += 1; continue
        raise LexError(f"unexpected character {c!r}", line, col)

    toks.append(Token(EOF, "", line, col))
    return toks
