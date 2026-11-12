from abc import ABC
from dataclasses import dataclass

class Expr(ABC): pass

@dataclass
class Input(Expr): pass

@dataclass
class Literal(Expr): pass

@dataclass
class Add(Expr):
    left: Expr
    right: Expr

@dataclass
class Multiply(Expr):
    left: Expr
    right: Expr