#!/usr/bin/env python3
"""Require every commit message to name a GitHub issue and an easyBacklog story.

    check_commit_message.py <message-file>     commit-msg hook (pre-commit passes the file)
    check_commit_message.py --range A..B       CI: every non-merge commit in the range

A message needs both, anywhere in it:
  * a GitHub issue reference such as  #74
  * a backlog story ID such as        MVP-12, CI-1, POC-3, or A1..F9 (theme letter + number)
e.g.  "Refs #74 CI-1"  or  "Closes #75 MVP-12".
Merge commits and fixup!/squash! commits are exempt.
"""

import re
import subprocess
import sys

ISSUE = re.compile(r'(?<![\w/&])#\d+\b')
STORY = re.compile(r'\b(?:(?:MVP|CI|POC)-\d+|[A-F]\d{1,2})\b')
EXEMPT = ('Merge ', 'fixup!', 'squash!', 'amend!')
HELP = ('Every commit must reference a GitHub issue and an easyBacklog story ID, '
        'for example "Refs #74 CI-1" or "Closes #75 MVP-12".')


def problems(message):
    """Return what is missing from a commit message (empty list if it is fine)."""
    lines = [ln for ln in message.splitlines() if not ln.startswith('#')]  # git comments
    text = '\n'.join(lines)
    if text.lstrip().startswith(EXEMPT):
        return []
    missing = []
    if not ISSUE.search(text):
        missing.append('a GitHub issue number such as #74')
    if not STORY.search(text):
        missing.append('an easyBacklog story ID such as MVP-12, CI-1 or B3')
    return missing


def check_range(rev_range):
    shas = subprocess.run(['git', 'rev-list', '--no-merges', '--reverse', rev_range],
                          capture_output=True, text=True, check=True).stdout.split()
    bad = 0
    for sha in shas:
        message = subprocess.run(['git', 'log', '-1', '--format=%B', sha],
                                 capture_output=True, text=True, check=True).stdout
        missing = problems(message)
        if missing:
            bad += 1
            subject = message.splitlines()[0] if message.strip() else ''
            print(f'{sha[:8]} {subject}\n    missing: ' + '; '.join(missing))
    print(f'checked {len(shas)} commit(s): ' + ('FAILED' if bad else 'ok'))
    return 1 if bad else 0


def main(argv):
    if len(argv) == 3 and argv[1] == '--range':
        code = check_range(argv[2])
    elif len(argv) == 2:
        with open(argv[1], encoding='utf-8') as f:
            missing = problems(f.read())
        code = 1 if missing else 0
        if missing:
            print('commit message is missing ' + ' and '.join(missing))
    else:
        print(__doc__)
        return 2
    if code:
        print(HELP)
    return code


if __name__ == '__main__':
    sys.exit(main(sys.argv))
