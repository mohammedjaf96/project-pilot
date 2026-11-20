#!/usr/bin/env python3
"""Fingerprint explicit verification inputs without scanning or executing commands."""

import argparse
import hashlib
import json
from pathlib import Path


def fingerprint(root, files, command='', context=()):
    root = Path(root).resolve()
    if not root.is_dir():
        raise ValueError('Root must be an existing directory')
    inputs = {}
    for name in files:
        candidate = Path(name)
        path = (candidate if candidate.is_absolute() else root / candidate).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError('Input must be an existing file inside root: ' + str(name))
        relative = path.relative_to(root).as_posix()
        inputs[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    if not inputs:
        raise ValueError('At least one input file is required')
    payload = {'files': inputs, 'command': command, 'context': sorted(set(context))}
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return {'algorithm': 'sha256', 'digest': digest, 'fileCount': len(inputs),
            'contextCount': len(set(context)), 'commandIncluded': bool(command)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--files', nargs='+', required=True)
    parser.add_argument('--command', default='', help='Check command as text; never executed')
    parser.add_argument('--context', action='append', default=[], help='Non-secret environment or dependency identity')
    args = parser.parse_args()
    try:
        result = fingerprint(args.root, args.files, args.command, args.context)
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps(result, separators=(',', ':')))


if __name__ == '__main__':
    main()
