# Copyright 2022 The Regents of the University of California
# released under BSD 3-Clause License
# author: Kevin Laeufer <laeufer@cs.berkeley.edu>
# Some code was imported from pyverilog/utils/identifierreplace.py
# and is under the following copyright + license.
# Copyright (C) 2015, Shinya Takamaeda-Yamazaki
# License: Apache 2.0

from pyverilog.utils.identifierreplace import children_items
import pyverilog.vparser.ast as vast


def is_empty_block(node: vast.Node):
    return isinstance(node, vast.Block) and len(node.statements) == 0


def template_guard(func):
    def wrapper(self, node):
        if self.template_enable:
            return func(self, node)
        return node
    return wrapper


class AstVisitor:
    """ Generic AST visitor for pyverilog. Inspired by the IdentifierReplace class. """

    def __init__(self, only_first_module: bool = True):
        self.only_first_module = only_first_module
        self.visited_first_module = False

        self.template_global_enable = False
        self.template_enable = False

    def visit(self, node):
        if isinstance(node, vast.ModuleDef):
            if self.visited_first_module and self.only_first_module:
                return node  # done
            self.visited_first_module = True
        method = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        if self.template_enable or getattr(node, 'mark', None) is not None or self.template_global_enable:
            self.template_enable = True
        else:
            self.template_enable = False
        ret = visitor(node)
        if getattr(node, 'mark', None) is not None and not self.template_global_enable:
            self.template_enable = False
        if ret is None:
            return node
        return ret

    def generic_visit(self, node):
        if isinstance(node, vast.ModuleDef):
            # make sure we visit children in order
            children = children_items(node)
            # put items to the back so that we visit the port declarations first
            assert children[2][0] == "items"
            children = children[0:2] + children[3:] + [children[2]]
        else:
            children = children_items(node)

        for name, child in children:
            if child is None:
                continue
            if isinstance(child, list) or isinstance(child, tuple):
                r = []
                for c in child:
                    visited = self.visit(c)
                    if visited is not None and not is_empty_block(visited):  # remove empty blocks from AST
                        r.append(visited)
                ret = tuple(r)
            else:
                # do not remove empty block in case there is only one child such as a vast.Case
                ret = self.visit(child)

            setattr(node, name, ret)
        return node

