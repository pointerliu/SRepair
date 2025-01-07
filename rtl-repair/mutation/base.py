from copy import deepcopy

from mutation.visitor import children_items
from pyverilog.ast_code_generator.codegen import ASTCodeGenerator

_codegen = ASTCodeGenerator()


def serialize(_ast):
    code_src = _codegen.visit(_ast)
    return code_src


class MutationOp:
    def __init__(self):
        pass

    @staticmethod
    def replace_with_node(ast, old, new):
        children = children_items(ast)

        for name, child in children:
            if child is None:
                continue
            ret = None
            if isinstance(child, list) or isinstance(child, tuple):
                r = []
                for i, c in enumerate(child):
                    if c is not old:
                        r.append(c)
                        MutationOp.replace_with_node(c, old, new)
                    else:
                        r.append(deepcopy(new))
                ret = tuple(r)
            else:
                # do not remove empty block in case there is only one child such as a vast.Case
                if child is old:
                    ret = new
                MutationOp.replace_with_node(child, old, new)
            if ret is not None:
                setattr(ast, name, ret)
        return ast
