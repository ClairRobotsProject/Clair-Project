"""Tests for the commit-message rule enforced by the commit-msg hook and CI."""

import importlib.util
import os

import pytest

PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'scripts', 'check_commit_message.py')
spec = importlib.util.spec_from_file_location('check_commit_message', PATH)
rule = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rule)


@pytest.mark.parametrize('message', [
    'Add the thing\n\nRefs #74 CI-1',
    'Fix it. Closes #75, MVP-12',
    'Tweak\n\nSee #5 and B3',
    'Merge pull request #73 from ClairRobotsProject/feature/x',
    'fixup! Add the thing',
])
def test_accepts_messages_with_both_references(message):
    assert rule.problems(message) == []


@pytest.mark.parametrize('message,count', [
    ('Add the thing', 2),
    ('Add the thing\n\nRefs #74', 1),
    ('Add the thing\n\nMVP-12', 1),
    ('Use UTF-8 and ROS-2 in issue url/#74', 2),
    ('# a git comment mentioning #74 and MVP-1\nSubject', 2),
])
def test_reports_what_is_missing(message, count):
    assert len(rule.problems(message)) == count
