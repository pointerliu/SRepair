from pathlib import Path

for dir in Path(__file__).parent.glob('*'):
    if dir.is_dir():
        file = dir / 'project.toml'
        ctx = file.read_text()
        ctx = ctx.replace('toplevel = "mux21_test"', 'toplevel = "mux21"')
        file.write_text(ctx)
