from pyverilog.vparser.ast import *


def ischild(node, attr):
    if not isinstance(node, Node):
        return False
    excludes = ('coord', 'attr_names',)
    if attr.startswith('__'):
        return False
    if attr in excludes:
        return False
    attr_names = getattr(node, 'attr_names')
    if attr in attr_names:
        return False
    attr_test = getattr(node, attr)
    if hasattr(attr_test, '__call__'):
        return False
    return True


def children_items(node):
    children = [attr for attr in dir(node) if ischild(node, attr)]
    ret = []
    for c in children:
        ret.append((c, getattr(node, c)))
    return ret
