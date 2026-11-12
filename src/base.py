from abc import ABC
from dataclasses import dataclass

class Expr(ABC):
    def size(self) -> int:
        return 1

@dataclass
class Input(Expr): 
    pass

@dataclass
class Literal(Expr): 
    pass

@dataclass
class Add(Expr):
    left: Expr
    right: Expr
    def size(self) -> int:
        return 1 + self.left.size() + self.right.size()

@dataclass
class Multiply(Expr):
    left: Expr
    right: Expr
    def size(self) -> int:
        return 1 + self.left.size() + self.right.size()