from dataclasses import dataclass
from base import Expr, Literal

@dataclass
class AddConst(Expr):
    child: Expr
    const: Literal
    def size(self) -> int: return 1 + self.child.size()

@dataclass
class MultConst(Expr):
    child: Expr
    const: Literal
    def size(self) -> int: return 1 + self.child.size()

@dataclass
class Square(Expr):
    child: Expr
    def size(self) -> int: return 1 + self.child.size()

AVAILABLE_MACROS = [AddConst, MultConst, Square]
