#!/usr/bin/env python
# -*- coding: utf-8 -*-
from data        import Kripke
import pyparsing as pp


def parse_kripke_file(filename):
    """
    Parses a kripke file into a Kripke Object
    """
    assert(filename.endswith(".kripke"))
    with open(filename) as kf:
        # Remove comments and empty lines
        kl = []
        for line in kf:
            if "#" in line:
                line, comment = line.split('#', 1)

            line = line.strip()
            if line:
                kl.append(line)
        kstring = "\n".join(kl)
    assert(kstring)

    # Create a kripke model
    kripke = Kripke()

    obrack,  cbrack   = pp.Suppress('{'), pp.Suppress('}')
    oparens, cparens  = pp.Suppress('('), pp.Suppress(')')
    equals,  end      = pp.Suppress('='),pp.Suppress(';')
    comma             = pp.Suppress(',')

    ident     = pp.Word(pp.alphanums + '_$')
    ident.setParseAction(lambda tokens:tokens[0])

    ident_seq = pp.Optional(ident + pp.ZeroOrMore(comma + ident))
    ident_seq.setParseAction(lambda tokens:tokens)
    ident_set = obrack + ident_seq + cbrack

    tup       = oparens + ident + comma + ident + cparens
    tup.setParseAction(lambda t:(t[0], t[1]))
    tup_seq   = pp.Optional(tup + pp.ZeroOrMore(comma + tup))
    tup_seq.setParseAction(lambda t:t)
    tup_set   = obrack + tup_seq + cbrack

    V = pp.Suppress('V') + oparens + ident + cparens + equals + ident_set + end
    V.setParseAction(lambda t:kripke.add_vals(t[0], t[1:]))

    W = pp.Suppress('W') + equals + ident_set + end
    W.setParseAction(lambda t:kripke.add_worlds(set(t)))

    R = pp.Suppress('R') + equals + tup_set + end
    R.setParseAction(lambda t:kripke.add_transes(set(t)))

    expr = pp.OneOrMore(V | W | R)
    return expr.parseString(kstring)[0]

if __name__ == '__main__':
    from argparse import ArgumentParser
    from parser import parse

    parser = ArgumentParser(description="finite kripke model evaluator")
    parser.add_argument("file", help="kripke file (see examples)")
    parser.add_argument("expression", help="logical expression to test over the kripke model")
    parser.add_argument("-m", "--model", action='store_true', help="displays model")
    parser.add_argument("-s", "--stack", action='store_true', help="displays a sort of stacktrace when evaluating")
    args = parser.parse_args()

    model      = parse_kripke_file(args.file)
    expression = parse(args.expression)

    if args.model:
        print("𝓜  consists of the triplet (W, R, V):")
        print(str(model))
        print("")

    if args.stack:
        print("stack based evaluation")
        print("--------------------------------")
        res, stack = expression.stack_calc(model)
        print(stack)
        print("")

    if model.entails(expression):
        print("𝓜  ⊨ %s" % expression)
    else:
        print("𝓜  ⊭ %s" % expression)

        worlds = expression.calc(model)
        if worlds:
            print("However,")
            for w in worlds:
                print("𝓜 , %s ⊨ %s" % (w, expression))
