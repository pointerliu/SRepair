import shutil
from pathlib import Path

# conver txt -> csv in 10 radix
# for file in Path('.').rglob('test.txt.bk'):
#     print('processing', file)
#     ctx = file.read_text()
#     res = ''
#
#     try:
#         header = ctx.splitlines()[0].split(',')[1:]
#     except Exception as e:
#         print(e, file)
#         continue
#
#     res += ','.join(header) + '\n'
#
#     for line in ctx.splitlines()[1:]:
#         nums = line.split(',')[1:]
#         c_nums = []
#         for n in nums:
#             if 'x' in n:
#                 c_nums.append('x')
#             else:
#                 c_nums.append(str(int(n, 2)))
#         res += ','.join(c_nums) + '\n'
#
#     ofp = Path(file).parent / 'test.csv'
#     ofp.write_text(res)


# template = (Path(__file__).parent / 'template.toml').read_text()

for proj in Path(__file__).parent.glob('*'):
    if not proj.is_dir(): continue
    for bug_dir in proj.glob('*'):
        if not bug_dir.is_dir(): continue
        print(f'processing {bug_dir.stem} in {proj.name}')
        template = (Path(__file__).parent / 'template.toml').read_text()
        try:
            f = list((bug_dir / 'fixed').glob('*_test.v'))[0]
        except IndexError as e:
            print(f"{e}")
            continue
        t = list((bug_dir / 'fixed').glob('*_tb.v'))[0]
        template = template.replace('$(FIX_V)', f.stem)

        template = template.replace('$(BUG_NAME)', bug_dir.stem)
        template = template.replace('$(TB_NAME)', t.stem)
        (bug_dir / 'project.toml').write_text(template)
