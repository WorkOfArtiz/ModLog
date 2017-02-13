#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Parser that deals with the most ridiculous expressions
from pyparsing import *
from data import create_var_const, create_expression, And, Or, Implies, prefix_operators

__bnf = None

def _bnf():
    global __bnf
    if __bnf:
        return __bnf
    # varconst    := Word of letters numbers and underscores
    # atom        := varconst | '(' expression ')'
    # prefix_expr := [ prefix ]* atom
    # and_expr    := prefix_expr  [ and_symbols prefix_expr ]*
    #  or_expr    := and_expr     [  or_symbols    and_expr ]*
    # expression  := or_expr      [impl_symbols     or_expr ]*
    expression  = Forward()
    and_symbol  = oneOf(And.symbols, caseless=True)
    or_symbol   = oneOf(Or.symbols, caseless=True)
    impl_symbol = oneOf(Implies.symbols, caseless=True)
    prefix_op   = oneOf(prefix_operators, caseless=True)

    varconst = Word(alphas + '_').setParseAction(lambda t: create_var_const(t[0]))
    nest     = Suppress('(') + expression + Suppress(')')
    atom     = varconst | nest
    prefix_expr = (ZeroOrMore(prefix_op) + atom).setParseAction(parse_prefix_op)
    and_expr = (prefix_expr + ZeroOrMore(and_symbol + prefix_expr)).setParseAction(parse_infix_op)
    or_expr  = (and_expr + ZeroOrMore(or_symbol + and_expr)).setParseAction(parse_infix_op)
    expression << (or_expr + ZeroOrMore(impl_symbol + or_expr)).setParseAction(parse_infix_op)
    __bnf = expression
    return __bnf


def parse_prefix_op(toks):
    assert toks
    for i, t in enumerate(toks[::-1]):
        res = t if i == 0 else create_expression(t, res)
    return res

def parse_infix_op(toks):
    left = toks[0]

    for op, right in zip(toks[1::2], toks[2::2]):
        left = create_expression(op, left, right)
    return left

def parse(string):
    return _bnf().parseString(string)[0]

if __name__ == '__main__':
    from argparse import ArgumentParser, RawTextHelpFormatter
    from parser   import parse

    parser = ArgumentParser(description="a kripke expression parser",
        formatter_class=RawTextHelpFormatter, epilog="""
    Expression examples:

    P \/ Q /\ ~R -> S
    ((a or c) or d)
    b * (((a))) + d * shit * crazy
    throw_money_in_machine implies candy_rolls_out
    (a implies a) implies (a or ¬ b ^ c)
    ! ~ not ~ ! True
    ◇d \/ not ◇◇t
    """)

    parser.add_argument("expressions", metavar='expression', nargs='+', help="a logic expression")
    args = parser.parse_args()

    for expr_in in args.expressions:
        try:
            print("Input                  : '%s'" % expr_in)
            expr_out = parse(expr_in)
            print("Internal representation: %s" % repr(expr_out))
            print("Human    representation: %s" %  str(expr_out))
            print("")
        except Exception:
            print("Input could not be parsed")
