import random
import time
from enum import Enum
from typing import List, Optional, Any, Dict

import z3
from z3 import Solver, BitVec, Bool, BitVecVal, And, Or, Not, If


def timer(f):
    def wrapper(*args, **kwargs):
        t0 = time.time()
        f(*args, **kwargs)
        t1 = time.time()
        print(f'Elapsed time: {t1 - t0:0.4f}s')
        return t1 - t0

    return wrapper


class Operator(Enum):
    ADDI = ('addi', '$v0 + const',)
    ADD = ('add', '$v0 + $v1',)
    SUBI = ('subi', '$v0 + const',)
    ORI = ('ori', '$v0 | const',)
    ANDI = ('andi', '$v0 & const',)
    AND = ('and', '$v0 & $v1',)
    FLIP = ('flip', '~$v0',)
    IDENTITY = ('identity', '$v0')

    @staticmethod
    def get(s: str):
        for v in Operator:
            if s == v.value[0]:
                return v
        raise NotImplementedError(f"Operator {s} is not yet implemented.")

    def get_name(self) -> str:
        return self.value[0]

    def get_pattern(self) -> str:
        return self.value[1]

    def require_const_var(self):
        return 'const' in self.get_pattern()

    def require_two_var(self):
        return '$v1' in self.get_pattern()


class Node:
    def __init__(self, prefix: str):
        self.guards = []
        self.prefix = prefix
        self.vars = {}

        self.children = []

    def add_var(self, name: str, var):
        self.vars[self.prefix + '.' + name] = var

    def get_var(self, name):
        return self.vars[self.prefix + '.' + name]

    def generate_body(
            self,
            op: Operator,
            bv: int,
            i_tb: int,
            i_node: int,
            x_const: Optional[List[int]] = None,
            y_const: Optional[int] = None,
    ):
        if op.require_const_var():
            const = BitVec(self.prefix + f'.const_{op.get_name()}', bv)
            self.add_var(f'const_{op.get_name()}', const)

        if x_const is not None:
            xc = BitVecVal(x_const[i_node], bv)
            self.add_var(f'xc_{i_tb}', xc)
        else:
            x0 = BitVec(self.prefix + f'.x_0_{i_tb}', bv)
            self.add_var(f'x_0_{i_tb}', x0)

            x1 = BitVec(self.prefix + f'.x_1_{i_tb}', bv)
            self.add_var(f'x_1_{i_tb}', x1)

        if y_const is not None:
            yc = BitVecVal(y_const, bv)
            self.add_var(f'yc_{i_tb}', yc)
        else:
            y = BitVec(self.prefix + f'.y_{i_tb}', bv)
            self.add_var(f'y_{i_tb}', y)
        pat = op.get_pattern().replace("$v0", 'xc' if x_const is not None else 'x0').replace("$v1", 'x1')

        return eval(pat + ' == ' + ('yc' if y_const is not None else 'y'))

    def generate_guards(
            self,
            ops
    ):
        for i in range(len(ops)):
            guard = eval(f"Bool('{self.prefix}.g_{ops[i].get_name()}')")
            self.add_var(f'g_{ops[i].get_name()}', guard)
            self.guards.append(guard)

    def generate_switch(self):
        res = []
        for i in range(len(self.guards)):
            f = []
            for j in range(len(self.guards)):
                if i == j:
                    f.append(self.guards[j])
                else:
                    f.append(Not(self.guards[j]))
            res.append(And(*f))
        return Or(*res)

    def generate_if(
            self,
            ops: List[Operator],
            bv: int,
            i_tb: int,
            i_node: int,
            x_const: Optional[int] = None,
            y_const: Optional[int] = None,
    ):
        ifs = []
        for i in range(len(ops)):
            ifs.append(If(self.guards[i], self.generate_body(
                op=ops[i],
                bv=bv,
                i_tb=i_tb,
                i_node=i_node,
                x_const=x_const,
                y_const=y_const
            ), False))

        return Or(*ifs)

    def generate_node(
            self,
            ops: List[Operator],
            bv: int,
            tb_i: int,
            i_node: int,
            x_const: Optional[List[List[int]]] = None,
            y_const: Optional[List[int]] = None,
    ):
        components = []

        if_body = self.generate_if(
            ops=ops,
            bv=bv,
            i_tb=tb_i,
            i_node=i_node,
            x_const=x_const[tb_i] if x_const is not None else None,
            y_const=y_const[tb_i] if y_const is not None else None,
        )

        components.append(if_body)
        return And(*components)


class SRN:
    def __init__(self, bv: int, ops: List[Operator], node_nums: List[int], xs_len: int):
        self.solver = Solver()
        self.bv = bv

        self.xs_len = xs_len
        self.ops = ops
        self.layer_num = len(node_nums)
        self.node_nums = node_nums
        self.nodes: Dict[str, List[Node]] = {}
        self.link_guards = {}
        self.edge = {}

    def root_node(self):
        return self.nodes[f'layer_{self.layer_num - 1}'][0]

    def link_two_node(self, node1: Node, node2: Node):
        node2.children.append(node1)
        for i in range(self.xs_len):
            self.solver.add(node1.get_var(f'y_{i}') == node2.get_var(f'x_{i}'))

    def generate_link_guards(self, name: str, nodes):
        guards = []
        for i in range(len(nodes)):
            guard = eval(f"Bool('edge.g_{name}_{i}')")
            self.edge[f'edge.g_{name}'] = guard
            guards.append(guard)
        return guards

    def generate_link_switch(self, guards):
        res = []
        for i in range(len(guards)):
            f = []
            for j in range(len(guards)):
                if i == j:
                    f.append(guards[j])
                else:
                    f.append(Not(guards[j]))
            res.append(And(*f))
        return Or(*res)

    def generate_link_if(self, guards, node, ys):
        ifs = []

        for i in range(len(ys)):
            ifs.append(If(guards[i], node == ys[i], False))

        return Or(*ifs)

    def guard_link(self, name: str, node, ys):
        guards = self.generate_link_guards(name, ys)
        self.link_guards[name] = guards
        switch_body = self.generate_link_switch(guards)
        self.solver.add(switch_body)
        components = []
        components.append(self.generate_link_if(guards, node, ys))
        self.solver.add(And(*components))

    def link_all(self, l: int):
        c1 = self.nodes[f'layer_{l - 1}']
        c2 = self.nodes[f'layer_{l}']

        for tb_i in range(self.xs_len):
            ys = []
            for li, c1_node in enumerate(c1):
                # get c1_node y_tbi
                ys.append(c1_node.get_var(f'y_{tb_i}'))

            for li, c2_node in enumerate(c2):
                self.guard_link(f'{l}_{li}_x0', node=c2_node.get_var(f'x_0_{tb_i}'), ys=ys)
                self.guard_link(f'{l}_{li}_x1', node=c2_node.get_var(f'x_1_{tb_i}'), ys=ys)

    def build_layer(self, l: int, m: int, xs: List[List[int]], ys: List[int]):
        for i in range(m):
            node = Node(f'layer_{l}_{i}')
            t_xs = xs if l == 0 else None
            t_yx = ys if l == self.layer_num - 1 else None

            node.generate_guards(ops=[Operator.IDENTITY] if l == 0 else self.ops)
            switch_body = node.generate_switch()
            self.solver.add(switch_body)
            for tb_i in range(self.xs_len):
                self.solver.add(
                    node.generate_node(
                        [Operator.IDENTITY] if l == 0 else self.ops,
                        self.bv,
                        tb_i,
                        i,
                        t_xs,
                        t_yx
                    )
                )

            if f'layer_{l}' in self.nodes:
                self.nodes[f'layer_{l}'].append(node)
            else:
                self.nodes[f'layer_{l}'] = [node]

    def build(self, xs: List[List[int]], ys: List[int]):
        # self.build_input_layer(xs, ys)
        for i in range(self.layer_num):
            self.build_layer(i, self.node_nums[i], xs, ys)
            if i >= 1:
                self.link_all(i)

    def solve(self):
        return self.solver.check()

    def build_expr(self, node: Node):
        model = self.solver.model()
        for var in node.vars.keys():
            layer_name = var.split('.')[0]
            layer_id = int(layer_name.split('_')[1])
            node_id = int(layer_name.split('_')[2])
            ops = var.split('.')[1][2:]
            if layer_id == 0:
                return f'x{node_id}'
            if 'g_' in var and model.eval(node.vars[var]) == True:
                # if
                # var2 = model.eval(node.vars[f'{layer_name}.const_{ops}'])
                var1 = None
                for i in self.link_guards[f'{layer_id}_{node_id}_x0']:
                    pre_ptr = int(str(i).split('_')[-1])
                    v = model.eval(i)
                    if v:
                        var1 = self.build_expr(self.nodes[f'layer_{layer_id - 1}'][pre_ptr])
                        break
                var2 = None
                for i in self.link_guards[f'{layer_id}_{node_id}_x1']:
                    pre_ptr = int(str(i).split('_')[-1])
                    v = model.eval(i)
                    if v:
                        var2 = self.build_expr(self.nodes[f'layer_{layer_id - 1}'][pre_ptr])
                        break

                op_e = Operator.get(ops)
                if op_e.require_const_var():
                    var2 = self.nodes[f'layer_{layer_id}'][node_id].vars[f'layer_{layer_id}_{node_id}.const_{ops}']
                    var2 = model.eval(var2)
                elif not op_e.require_two_var():
                    var2 = None

                return (ops, var1, var2)


@timer
def addi_test(prefix, ops, bv, n):
    upper = 1 << bv
    const = random.randint(0, upper)
    xs = [random.randint(0, upper) for _ in range(n)]
    ys = [x + const for x in xs]

    print(f'xs = {xs}')
    print(f'ys = {ys}')
    print(f'const = {const}')

    node = Node(prefix=prefix)

    solver = Solver()
    formula = node.generate_node(ops, bv, n, xs, ys)
    solver.add(formula)

    result = solver.check()
    print(result)
    if result == z3.sat:
        model = solver.model()
        print(model)


def fit_func(f, x):
    if isinstance(f, str):
        i = int(f[1:])
        return x[i]

    if not isinstance(f, tuple):
        return int(str(f))
    op = Operator.get(f[0])
    pat = op.value[1].replace("$v0", "fit_func(f[1], x)")
    if "$v1" in op.value[1]:
        pat = pat.replace("$v1", "fit_func(f[2], x)")
    if "const" in op.value[1]:
        pat = pat.replace("const", "fit_func(f[2], x)")
    return eval(pat)


@timer
def srn_test(bv, n):
    # layer_{layer-id}_{layer-node-id}.x_{x0/x1}_{tb_i}
    # edge.g_{layer-id}_{layer-node-id}_x{1/0}_{pre-node-id}

    ops = [
        Operator.ADD,
        Operator.ADDI,
        Operator.FLIP,
        Operator.AND,
        Operator.IDENTITY
    ]

    upper = 1 << bv
    random.seed(0)
    xs = [[
        random.randint(0, upper - 1),
        random.randint(0, upper - 1),
        random.randint(0, upper - 1),
    ] for i in range(n)]
    ys = [(x[0] + ~x[1] + ~x[2]) % upper for x in xs]
    print(f"input: {xs}\n")
    print(f"expected output: {ys}\n")
    print(f"expected function: y = x[0] + ~x[1] + ~x[2]")

    net = SRN(bv, ops, xs_len=len(xs), node_nums=[3, 3, 2, 1])
    net.build(xs, ys)

    result = net.solve()
    print(result)
    if result == z3.sat:
        f = net.build_expr(net.root_node())
        pred = [fit_func(f, x) % upper for x in xs]
        print(f"output of fit function: {pred}")

if __name__ == '__main__':
    srn_test(4, 16)
