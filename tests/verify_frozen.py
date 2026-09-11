"""Verify approved artifacts against their first committed freeze manifest."""
import hashlib
from pathlib import Path
import subprocess
import sys

ROOT = Path.cwd()
MANIFEST = 'tests/frozen.sha256'
CONTRACT_COMMIT = '4aef169b2944b97310b2cd76c17003344a0b5430'


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def verify_list(data):
    for line in data.decode().splitlines():
        checksum, name = line.split('  ', 1)
        path = ROOT / name
        assert not path.is_symlink() and path.is_file(), f'Missing or redirected frozen file: {name}'
        assert hashlib.sha256(path.read_bytes()).hexdigest() == checksum, f'Unapproved change: {name}'


def main():
    approved_contract = git('show', CONTRACT_COMMIT + ':docs/contracts/calendar-weekday-v1.sha256')
    assert (ROOT / 'docs/contracts/calendar-weekday-v1.sha256').read_bytes() == approved_contract, 'Contract checksum was changed'
    verify_list(approved_contract)
    commits = git('log', '--reverse', '--diff-filter=A', '--format=%H', '--', MANIFEST).decode().splitlines()
    if not commits:
        assert '--candidate' in sys.argv, 'Tests have no committed freeze record'
        print('Approved contract verified; test candidate has not been frozen yet')
        return
    else:
        approved_tests = git('show', commits[0] + ':' + MANIFEST)
        assert (ROOT / MANIFEST).read_bytes() == approved_tests, 'Frozen test manifest was changed'
    verify_list(approved_tests)
    print('Approved contract and frozen tests verified')


if __name__ == '__main__':
    main()
