#!/usr/bin/env python
# -*- coding: utf-8 -*-
from collections import defaultdict

# To model modal logic, we have here a Kripke class
class Kripke:
    """
    Models a propositional Kripke model
    """
    def __init__(self):
        self.V    = defaultdict(set) # dict { var -> set(worlds) }
        self.W    = set()            # set of world (strings)
        self.R    = defaultdict(set) # dict { world -> set(worlds) }

        self._cached_blind_worlds = None

    def entails(self, expression):
        "Checks whether our model 𝓜 entails the expression"
        return sorted(self.W) == sorted(expression.calc(self))

    def blind_worlds(self):
        if self._cached_blind_worlds != None:
            return self._cached_blind_worlds
        self._cached_blind_worlds = set(w for w in self.W if not self.R[w])
        return self._cached_blind_worlds

    def add_vals(self, var, ws):
        "Adds valuations to the worlds (aka V(p) = {w1, w2, w3})"
        self.V[var].update(ws)
        return self

    def add_val(self, var, w):
        "Adds world w to V(var) set"
        self.V[var].add(w)
        return self

    def add_worlds(self, ws):
        "Adds worlds ws"
        self.W.update(ws)
        return self

    def add_world(self, w):
        "Adds a world w"
        self.W.add(w)
        return self

    def add_transes(self, ts):
        "Adds transistions between worlds, ts is a sequence of tuples"
        for (a,b) in ts:
            self.R[a].add(b)
        return self

    def add_trans(self, t):
        "Adds transition between worlds, t is a tuple of worlds"
        self.R[t[0]].add(t[1])
        return self

    def __repr__(self):
        return "Kripke(W=%s, R=%s, V=%s)" % (str(self.W), str(self.R), str(self.V))

    def __str__(self):
        "Stringifies the object"
        return "W    = {%s}\nR    = {%s}\n%s" % (
            ", ".join(self.W),
            ", ".join('(%s, %s)' % (v,w) for v in self.R for w in self.R[v]),
            "\n".join("V(%s) = {%s}" % (var, ", ".join(self.V[var])) for var in self.V)
        )

# Data components for logic expressions
# Should be easily extensible and adaptable
#
# These data components are supposed to be immutable.
#
# Currently implemented are the Objects
# And, Or, Implies, Not, Var, Constant (true or false)
class LogicExpression:
    """
    Logic Expression is a parent-class, a sort of interface all Logical
    Expressions have to uphold
    """
    class_name = None    # Text representing class
    symbols    = []      # A data container for all operators for expr
    out_symbol = None    # The symbol used to output

    def __init__(self):
        """
        Logic expressions are initialised by calling create_expression, rather
        than their own constructors, this avoids having 2 (a -> a) objects in
        for instance sub expressions
        """
        raise NotImplementedError()

    def __repr__(self):
        """
        repr is the way for the logic expression to show itself as an object structure.
        for instance: And(Or(Var(a), Var(b)), Constant(False))
        """
        raise NotImplementedError()

    def __str__(self):
        """
        str is the way for the logic expression to be human readable
        for instance: (a ∨ b) ∧ 0
        """
        raise NotImplementedError()

    def calc(self, kripke):
        """
        calc evaluates the expression in the context of a kripke model.
        It returns

        kripke : Kripke model
        returns a set of worlds in which the expression holds
        """
        raise NotImplementedError()

    def stack_calc(self, kripke, spacing=""):
        """
        A variant of calc which gives a stack trace like structure back
        return (set of worlds, stack trace (string))
        """
        raise NotImplementedError()

    def game_calc(self, kripke, world, spacing=""):
        """
        A variant of calc which generates game trees
        returns (true/false, stack_trace)
        """
        raise NotImplementedError()

    def expressions(self):
        "returns a set of sub expressions"
        raise NotImplementedError()

    def depth(self):
        "returns the amount of levels of expressions"
        raise NotImplementedError()

    def children(self):
        "returns generator that loops through direct sub expressions"
        raise NotImplementedError()

    def same_type(self, other):
        "basically an isinstance of"
        return self.class_name == other.class_name


class And(LogicExpression):
    class_name = 'and'
    symbols = ('and', '&&', '&', '^', '/\\', '∧', '*')
    out_symbol = '∧'

    def __init__(self, l, r):
        self._left, self._right = l, r

    def __str__(self):
        l = str(self._left)
        r = str(self._right)
        return "(%s %s %s)" % (l, And.out_symbol, r)

    def __repr__(self):
        return "And(%s,%s)" % (self._left.__repr__(), self._right.__repr__())

    def calc(self, kripke):
        return set.intersection(self._left.calc(kripke), self._right.calc(kripke))

    def stack_calc(self, kripke, spacing=""):
        lhs, lstack = self._left.stack_calc(kripke, spacing+"    ")
        rhs, rstack = self._right.stack_calc(kripke, spacing+"    ")
        res = set.intersection(lhs, rhs)

        lines = [
            "%s%s returns {%s}" % (spacing, And.out_symbol, ", ".join(res)),
            '%s- left  expression %s returns {%s}' % (spacing, self._left, ", ".join(lhs)),
            lstack,
            '%s- right expression %s returns {%s}' % (spacing, self._right, ", ".join(rhs)),
            rstack
        ]
        return res, "\n".join(lines)

    def expressions(self):
        e = self._left.expressions()
        e.add(self)
        e.update(self._right.expressions())
        return e

    def depth(self):
        return max(self._left.depth(), self._right.depth()) + 1

    def variables(self):
        return self._left.variables().union(self._right.variables())

    def children(self):
        yield self._left
        yield self._right


class Or(LogicExpression):
    class_name = 'or'
    symbols = ('or', '||', '|', 'v', '\\/', '∨', '+')
    out_symbol = '∨'

    def __init__(self, l, r):
        self._left, self._right = l, r

    def __str__(self):
        l = str(self._left)
        r = str(self._right)
        return "(%s %s %s)" % (l, Or.out_symbol, r)

    def __repr__(self):
        return "Or(%s, %s)" % (self._left.__repr__(), self._right.__repr__())

    def calc(self, kripke):
        return set.union(self._left.calc(kripke), self._right.calc(kripke))

    def stack_calc(self, kripke, spacing=""):
        lhs, lstack = self._left.stack_calc(kripke, spacing+"    ")
        rhs, rstack = self._right.stack_calc(kripke, spacing+"    ")
        res = set.union(lhs, rhs)

        lines = [
            "%s%s returns {%s}" % (spacing, Or.out_symbol, ", ".join(res)),
            '%s- left expression %s gives back {%s}' % (spacing, self._left, ", ".join(lhs)),
            lstack,
            '%s- right expression %s gives back {%s}' % (spacing, self._right, ", ".join(rhs)),
            rstack
        ]
        return res, "\n".join(lines)

    def expressions(self):
        e = self._left.expressions()
        e.add(self)
        e.update(self._right.expressions())
        return e

    def depth(self):
        return max(self._left.depth(), self._right.depth()) + 1

    def variables(self):
        return self._left.variables().union(self._right.variables())

    def children(self):
        yield self._left
        yield self._right


class Implies(LogicExpression):
    class_name = 'implies'
    symbols = ('implies', '->', '=>', '→')
    out_symbol = '→'

    def __init__(self, l, r):
        self._left, self._right = l, r

    def __str__(self):
        l = str(self._left)
        r = str(self._right)
        return "(%s %s %s)" % (l, Implies.out_symbol, r)

    def __repr__(self):
        return "Implies(%s, %s)" % (self._left.__repr__(), self._right.__repr__())

    def calc(self, kripke):
        lhs = self._left.calc(kripke)
        res = kripke.W.difference(lhs)

        if not lhs:
            return res

        res.update(lhs.intersection(self._right.calc(kripke)))
        return res

    def stack_calc(self, kripke, spacing=""):
        lhs, lstack = self._left.stack_calc(kripke, spacing+"    ")
        premise_doesnt_hold = kripke.W.difference(lhs)
        rhs, rstack = self._right.stack_calc(kripke, spacing+"    ")
        res = set.union(premise_doesnt_hold, lhs.intersection(rhs))

        lines = [
            "%s%s, returns {%s}" % (spacing, Implies.out_symbol, ", ".join(res)),
            "%s- Premise doesn't hold for {%s}" % (spacing, ", ".join(premise_doesnt_hold)),
            '%s- left expression %s gives back {%s}' % (spacing, self._left, ", ".join(lhs)),
            lstack,
            '%s- right expression %s gives back {%s}' % (spacing, self._right, ", ".join(rhs)),
            rstack
        ]
        return res, "\n".join(lines)

    def expressions(self):
        e = self._left.expressions()
        e.add(self)
        e.update(self._right.expressions())
        return e

    def depth(self):
        return max(self._left.depth(), self._right.depth()) + 1

    def variables(self):
        return self._left.variables().union(self._right.variables())

    def children(self):
        yield self._left
        yield self._right


class Not(LogicExpression):
    class_name = 'not'
    symbols = ('not', '~', '¬', '!')
    out_symbol = '¬'

    def __init__(self, e):
        self._expr = e

    def __repr__(self):
        return "Not(%s)" % self._expr.__repr__()

    def __str__(self):
        return "~%s" % str(self._expr)

    def calc(self, kripke):
        return kripke.W.difference(self._expr.calc(kripke))

    def stack_calc(self, kripke, spacing=""):
        expr_res, expr_stack = self._expr.stack_calc(kripke, spacing+"  ")
        res = kripke.W.difference(expr_res)
        return res, "%s returned {%s}\n%s" % (Not.out_symbol, ", ".join(res), expr_stack)

    def expressions(self):
        expr = self._expr.expressions()
        expr.add(self)
        return expr

    def depth(self):
        return self._expr.depth() + 1

    def variables(self):
        return self._expr.variables()

    def children(self):
        yield self._expr


class Box(LogicExpression):
    class_name = 'box'
    symbols = ('☐', 'box')
    out_symbol = '☐'

    def __init__(self, e):
        self._expr = e

    def __repr__(self):
        return "☐%s" % self._expr.__repr__()

    def __str__(self):
        return "Box(%s)" % str(self._expr)

    def calc(self, kripke):
        internal = self._expr.calc(kripke)
        actual   = set(w for w in kripke.W if all(v in internal for v in kripke.R[w]))
        actual.update(kripke.blind_worlds())
        return actual

    def stack_calc(self, kripke, spacing=""):
        inter, inter_stack = self._expr.stack_calc(kripke, spacing+"    ")
        actual             = set(w for w in kripke.W if all(v in inter for v in kripke.R[w]))
        out                = actual.union(kripke.blind_worlds())
        stack = [
            "%s%s returned {%s}" % (spacing, Box.out_symbol, ", ".join(out)),
            "%s- blind worlds, for which any box holds {%s}" % (spacing, ", ".join(actual)),
            "%s- worlds with successors in which condition holds {%s}" % (spacing, ", ".join(actual)),
            inter_stack
        ]
        return out, "\n".join(stack)

    def expressions(self):
        expr = self._expr.expressions()
        expr.add(self)
        return expr

    def depth(self):
        return self._expr.depth() + 1

    def variables(self):
        return self._expr.variables()

    def children(self):
        yield self._expr


class Diamond(LogicExpression):
    class_name = 'box'
    symbols = ('◇', 'diamond')
    out_symbol = '◇'

    def __init__(self, e):
        self._expr = e

    def __repr__(self):
        return "Diamond(%s)" % self._expr.__repr__()

    def __str__(self):
        return "◇%s" % str(self._expr)

    def calc(self, kripke):
        internal = self._expr.calc(kripke)
        return set(w for w in kripke.W if any(v in internal for v in kripke.R[w]))

    def stack_calc(self, kripke, spacing=""):
        inter, inter_stack = self._expr.stack_calc(kripke, spacing+"  ")
        out =  set(w for w in kripke.W if any(v in inter for v in kripke.R[w]))
        stack = "%s%s returned {%s}\n%s" % (spacing, self.out_symbol, ", ".join(out), inter_stack)
        return out, stack

    def expressions(self):
        expr = self._expr.expressions()
        expr.add(self)
        return expr

    def depth(self):
        return self._expr.depth() + 1

    def variables(self):
        return self._expr.variables()

    def children(self):
        yield self._expr


class Var(LogicExpression):
    class_name = 'var'

    def __init__(self, n):
        self.name = n

    def __str__(self):
        return "%s" % self.name

    def __repr__(self):
        return "Var(%s)" % self.name

    def calc(self, kripke):
        return kripke.V[self.name]

    def stack_calc(self, kripke, spacing=""):
        holds_in = kripke.V[self.name]
        return holds_in, "%s%s holds in {%s}" % (spacing, self.name, ", ".join(holds_in))

    def expressions(self):
        return {self}

    def depth(self):
        return 0

    def variables(self):
        return {self.name}

    def children(self):
        return
        yield


class Constant(LogicExpression):
    true_symbols = ('True', 'true', '1', '⊤')
    false_symbols = ('False', 'false', '0', '⊥')
    symbols = ('true', '1', 'false', '0')
    out_symbols = ('⊥', '⊤')
    class_name = 'const'

    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return "{True}" if self.value else "{False}"

    def __str__(self):
        return Constant.out_symbols[self.value]

    def calc(self, kripke):
        return kripke.W if self.value else set()

    def stack_calc(self, kripke, spacing=""):
        out   = kripke.W if self.value else set()
        stack = "%s%s holds for {%s}" % (spacing, self.out_symbols[self.value], ", ".join(out))
        return out, stack

    def expressions(self):
        return {self}

    def depth(self):
        return 0

    def variables(self):
        return set()

    def children(self):
        return
        yield


# The infix classes, prefix classes etc.
infix_classes = [And, Or, Implies]
prefix_classes = [Not, Box, Diamond]

# These are some meta data structures, to quickly lookup:
# - what class belongs to what symbol
# - what operators we have
# - what instances already exist
operator_class   = {}  # maps a symbol to its class '&' -> class And
infix_operators  = []  # a list of all symbols used for infix operators e.g. '&'
prefix_operators = []  # a list of all symbols used for prefix operators e.g. '~'
instances        = {}  # maps a tuple (class, args) to instance, since no duplicates are allowed


# initialise the meta structures
for c in infix_classes:
    operator_class.update((s, c) for s in c.symbols)
    infix_operators.extend(c.symbols)
for c in prefix_classes:
    operator_class.update((s, c) for s in c.symbols)
    prefix_operators.extend(c.symbols)


def create_expression(operator, *kwargs):
    "Creates an expression from tokens, or if operator is 'var', 'const', 'varconst'"
    if operator in ('var', 'const', 'varconst'):
        return create_var_const(*kwargs)

    constructor = operator_class[operator]
    expression = instances.get((constructor, kwargs))
    if expression is None:
        expression = instances[(constructor, kwargs)] = constructor(*kwargs)
    return expression


def create_var_const(name):
    "Creates vars and constants (attempt to avoid complicated BNF)"
    if name.lower() in Constant.symbols:
        constructor = Constant
        args = (name.lower() in Constant.true_symbols)
    else:
        constructor = Var
        args = name

    expr = instances.get((constructor, args))
    if expr == None:
        expr = instances[(constructor, args)] = constructor(args)
    return expr


if __name__ == '__main__':
    # Testing

    # Can vars and constants be properly made
    for i in ('Abc', 'Note', 'a', 't', 'True', 'False'):
        var_const = create_var_const(i)
        expr = create_expression('varconst', i)

        print(repr(expr))
        print(var_const == expr)
        print('-' * 20)

    a = create_var_const('a')
    b = create_var_const('b')
    t = create_var_const('t')
    at = create_expression('&', a, t)

    print(a)
    for i in a.children():
        print(i)

    create_expression('->', a, b)
    create_expression('->', a, b)
    print(instances)

    for i in infix_operators:
        print('input (a & t) %s b' % i)
        expr = create_expression(i, at, b)
        expr2 = create_expression(i, at, b)
        print(expr)
        print(expr == expr2)
