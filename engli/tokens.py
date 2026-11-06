from dataclasses import dataclass

# Token kinds. Multi-word operators (e.g. "is greater than or equal to") are NOT
# lexed as single tokens; the parser recognizes those word sequences. The lexer
# only needs words, literals, and punctuation.
NUMBER = "NUMBER"
STRING = "STRING"
WORD = "WORD"          # identifier or (contextual) keyword
PERIOD = "PERIOD"      # .
COLON = "COLON"        # :
COMMA = "COMMA"        # ,
LPAREN = "LPAREN"
RPAREN = "RPAREN"
LBRACKET = "LBRACKET"
RBRACKET = "RBRACKET"
LBRACE = "LBRACE"      # {  -> record/dict literal
RBRACE = "RBRACE"      # }
POSSESSIVE = "POSSESSIVE"   # 's  -> member access
EOF = "EOF"


@dataclass
class Token:
    kind: str
    value: str
    line: int
    col: int

    def __repr__(self):
        return f"Token({self.kind}, {self.value!r}, {self.line}:{self.col})"
