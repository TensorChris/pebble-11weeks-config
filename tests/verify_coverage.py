"""Require the agreed 80 percent line coverage on every calendar module."""
import json
import os
from pathlib import Path
import re
import shlex
import subprocess

root = Path(__file__).resolve().parents[1]
out = root / 'build/coverage'
out.mkdir(parents=True, exist_ok=True)
results = {}
for source in sorted((root / 'src').glob('calendar*.c')):
    report = subprocess.check_output(
        shlex.split(os.environ.get('GCOV', 'gcov')) + [
            '-b', '-o', str(root / 'build/contract-tests' / ('aplite-' + source.stem + '.gcno')),
            str(source)], cwd=root, text=True, env=dict(os.environ, LC_ALL='C'))
    (out / (source.stem + '.txt')).write_text(report)
    generated = root / (source.name + '.gcov')
    if generated.exists():
        generated.replace(out / generated.name)
    match = re.search(r'Lines executed:([\d.]+)% of (\d+)', report)
    assert match, f'No executable line coverage for {source.name}'
    percent = float(match.group(1))
    results[source.name] = percent
    assert percent >= 80, f'{source.name}: {percent}% line coverage is below 80%'
(out / 'summary.json').write_text(json.dumps(results, indent=2))
print(json.dumps(results, indent=2))
