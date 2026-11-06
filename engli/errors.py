class EngliError(Exception):
    """Base class for Engli compile errors, with source position."""
    def __init__(self, message, line=None, col=None):
        self.message = message
        self.line = line
        self.col = col
        where = f" at line {line}, col {col}" if line else ""
        super().__init__(f"{message}{where}")


class LexError(EngliError):
    pass


class ParseError(EngliError):
    pass
