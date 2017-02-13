#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
from itertools import count
try:
    from Queue     import Queue
except ImportError:
    from queue     import Queue
from parser    import parse

tree = """
digraph parse_tree {
rank_dir = LR;
graph [splines=ortho];
node [shape=square];

%s

%s
}
"""

label_gen = ("q%s" % d for d in count())

def to_graph(expr):
    nodes, edges, todo = [], [], Queue()

    todo.put((expr, next(label_gen)))

    while not todo.empty():
        subexpr, label = todo.get_nowait()
        nodes.append('\t%s [label="%s"];' % (label, subexpr.out_symbol or str(subexpr)))

        for child_expr in subexpr.children():
            child_label = next(label_gen)
            edges.append('\t%s -> %s' % (label, child_label))
            todo.put((child_expr, child_label))

    return tree % ("\n".join(nodes), "\n".join(edges))

if __name__ == '__main__':
    from argparse import ArgumentParser, RawTextHelpFormatter
    import sys

    parser = ArgumentParser(description="Tree viewer, transforms expression into parsetrees in the .dot format",
        formatter_class=RawTextHelpFormatter, epilog="""
Using it
====================
Note: to create a picture, you need graphviz

./tree.py "Diamond Box p Or q Implies Not r" | dot -Tpng > test.png

or

./tree.py -o example.dot "Diamond Box p Or q Implies Not r"
dot example.dot -Tpng -ofile test.png

Expression examples
=====================
P \/ Q /\ ~R -> S
((a or c) or d)
b * (((a))) + d * shit * crazy
throw_money_in_machine implies candy_rolls_out
(a implies a) implies (a or ¬ b ^ c)
! ~ not ~ ! True
◇d \/ not ◇◇t
    """)

    parser.add_argument("expression",
        help="Expression to draw a parse tree of (in quotes)")
    parser.add_argument("-o", "--output",
        help="file to write the dot file to (default stdout)", default=False)
    args = parser.parse_args()
    if not args.output:
        args.output =  sys.stdout

    print(to_graph(parse(args.expression)), file=args.output)
