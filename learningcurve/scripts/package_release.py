"""Create a source-only ZIP and a readable document containing every source file."""
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {'.venv', '__pycache__', '.pytest_cache', '.git'}
files = sorted(p for p in ROOT.rglob('*') if p.is_file()
               and not set(p.relative_to(ROOT).parts).intersection(EXCLUDED)
               and p.name not in {'ALL_CODE.md', 'secrets.toml'}
               and p.suffix in {'.py', '.json', '.md', '.txt', '.toml', '.yaml'}
               or p.is_file() and p.parent == ROOT and p.name == '.gitignore')
sections = ['# LearningCurve — complete source files\n',
            'Use README.md for Databricks setup. Each section below is one complete file.\n']
for path in files:
    language = {'.py': 'python', '.json': 'json', '.yaml': 'yaml', '.toml': 'toml'}.get(path.suffix, 'text')
    sections += [f'## {path.relative_to(ROOT).as_posix()}\n',
                 f'````{language}\n{path.read_text(encoding="utf-8")}\n````\n']
(ROOT / 'ALL_CODE.md').write_text('\n'.join(sections), encoding='utf-8')
output = ROOT.parent / 'LearningCurve-Databricks.zip'
with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
    for path in files + [ROOT / 'ALL_CODE.md']:
        archive.write(path, 'learningcurve/' + path.relative_to(ROOT).as_posix())
print(f'{output}: {len(files) + 1} files')
