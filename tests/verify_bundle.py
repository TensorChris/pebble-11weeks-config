"""KAL-06: validate the package produced by the real Pebble SDK."""
import json
from pathlib import Path
import sys
import zipfile


def verify(path):
    expected = json.loads(Path('appinfo.json').read_text())
    with zipfile.ZipFile(path) as bundle:
        assert bundle.testzip() is None, 'Invalid ZIP CRC'
        info = json.loads(bundle.read('appinfo.json'))
        assert info['uuid'] == expected['uuid'], 'Package must update the existing watchface'
        assert info['versionLabel'] == expected['versionLabel']
        assert info['watchapp']['watchface'] is True
        assert set(info['targetPlatforms']) == {'aplite', 'basalt', 'diorite'}
        assert bundle.read('pebble-js-app.js').strip(), 'Existing configuration support must be bundled'
        for platform in info['targetPlatforms']:
            prefix = platform + '/'
            if platform == 'aplite' and prefix + 'manifest.json' not in bundle.namelist():
                prefix = ''
            manifest = json.loads(bundle.read(prefix + 'manifest.json'))
            for field in ('application', 'resources'):
                entry = manifest[field]
                content = bundle.read(prefix + entry['name'])
                assert len(content) == entry['size'] > 0, (platform, field, 'Invalid size')
                if field == 'application':
                    assert content.startswith(b'PBLAPP\0\0'), (platform, 'Invalid application header')
    print(f'Valid installable PBW: {path}')


if __name__ == '__main__':
    paths = list(map(Path, sys.argv[1:])) or list(Path('build').glob('*.pbw'))
    assert paths, 'Pebble SDK produced no PBW'
    for path in paths:
        verify(path)
