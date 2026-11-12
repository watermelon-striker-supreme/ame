from abc import ABC
from dataclasses import dataclass

class Expr(ABC):
    def size(self) -> int: return 1
    def count_literals(self) -> int: return 0
    def eval_structure(self, x, params, param_idx): pass

@dataclass
class Input(Expr):
    def size(self) -> int: return 1
    def count_literals(self) -> int: return 0
    def eval_structure(self, x, params, param_idx): return x

@dataclass
class Literal(Expr):
    def size(self) -> int: return 1
    def count_literals(self) -> int: return 1
    def eval_structure(self, x, params, param_idx):
        val = params[param_idx[0]]
        param_idx[0] += 1
        return val

@dataclass
class Add(Expr):
    left: Expr
    right: Expr
    def size(self) -> int: return 1 + self.left.size() + self.right.size()
    def count_literals(self) -> int: return self.left.count_literals() + self.right.count_literals()
    def eval_structure(self, x, params, param_idx):
        return self.left.eval_structure(x, params, param_idx) + self.right.eval_structure(x, params, param_idx)

@dataclass
class Multiply(Expr):
    left: Expr
    right: Expr
    def size(self) -> int: return 1 + self.left.size() + self.right.size()
    def count_literals(self) -> int: return self.left.count_literals() + self.right.count_literals()
    def eval_structure(self, x, params, param_idx):
        return self.left.eval_structure(x, params, param_idx) * self.right.eval_structure(x, params, param_idx)