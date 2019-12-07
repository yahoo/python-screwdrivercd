#!/usr/bin/env python
# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
"""
Code to generate a changelog for a git repository
"""
import logging
import os
import subprocess  # nosec
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Union

from ..utility.environment import env_bool
from ..utility.package import setup_query
from ..utility.run import run_and_log_output


LOG = logging.getLogger(__name__)

CHANGE_TYPES = dict(
    feature='Features',
    bugfix='Bugfixes',
    doc='Improved Documentation',
    removal='Removed',
    misc='Misc Changes'
)


def git_fetch_tags():
    artifacts_dir = os.environ.get('SD_ARTIFACTS_DIR', '')
    log_filename = os.path.join(artifacts_dir, 'logs/changelog/fetch_tags.log')

    command = ['git', 'fetch', '--tags']
    run_and_log_output(command, logfile=log_filename)


def git_tag_dates() -> Dict[str, str]:
    tags = {}

    command = ['git', 'log', '--date-order', '--tags', '--simplify-by-decoration', '--pretty=format:%ct|%d']
    with subprocess.Popen(command, stdout=subprocess.PIPE) as tag_command:  # nosec
        for line in tag_command.stdout.readlines():
            date, all_tags = line.decode(errors='ignore').strip().split('|')
            all_tags = all_tags.strip().lstrip('(').rstrip(')')

            for tag in all_tags.split(','):
                tag = tag.strip()
                if tag.startswith('tag: '):
                    tag = tag[5:]
                tags[tag] = date
    return tags


def create_first_commit_tag_if_missing() -> None:
    if 'first_commit' in git_tag_dates().keys():
        return

    first_commit_hash = subprocess.check_output(['git', 'rev-list', '--max-parents=0', 'HEAD'], stderr=subprocess.DEVNULL).decode(errors='ignore').strip()  # nosec
    if first_commit_hash:
        output = subprocess.check_output(['git', 'tag', 'first_commit', first_commit_hash])  # nosec


def changed_files(commit1: str, commit2: str, changelog_dir: str='changelog.d') -> List[Path]:
    changed = []

    with subprocess.Popen(['git', 'diff', f'{commit1}..{commit2}', changelog_dir], stdout=subprocess.PIPE) as diff_command:  # nosec
        for binline in diff_command.stdout.readlines():
            line = binline.decode(errors='ignore').strip()
            if line.startswith('+++'):
                line = line.lstrip('+++ b/')
                filepath = Path(line)
                if filepath.parts[0] != changelog_dir:  # pragma: no cover
                    continue
                changed_file = Path(*filepath.parts)
                changed.append(changed_file)
    return changed


def release_changes(changelog_dir: str, only_versions: bool=True) -> Dict[str, Dict[str, Dict[str, str]]]:
    create_first_commit_tag_if_missing()
    tags = git_tag_dates()

    previous_commit = commit = 'first_commit'
    commits = list(tags.keys())
    commits.reverse()

    changes: Dict[str, Dict[str, Dict[str, str]]] = {}
    for commit in commits:
        if only_versions:
            if not commit.startswith('v'):
                if commit != 'first_commit':
                    continue

        changed = changed_files(previous_commit, commit, changelog_dir=changelog_dir)
        if not changed:
            previous_commit = commit
            continue

        changes[commit] = {}
        for change in changed:
            filename = change.parts[-1]
            split_filename = str(filename).split('.')
            changeid = split_filename[0]
            change_type = split_filename[1]
            if change_type not in CHANGE_TYPES:
                LOG.warning(f'Invalid change type {change_type}')
                previous_commit = commit
                continue
            if change_type not in changes[commit].keys():  # pragma: no cover
                changes[commit][change_type] = {}
            changes[commit][change_type][changeid] = change.read_text().rstrip()

        previous_commit = commit
    return changes


def changelog_contents(changelog_releases: str='') -> str:
    if not changelog_releases:
        changelog_releases = os.environ.get('CHANGELOG_RELEASES', 'all')

    only_versions = bool(env_bool('CHANGELOG_ONLY_VERSION_TAGS', True))
    changelog_dir = os.environ.get('CHANGELOG_DIR', 'changelog.d')
    header_filename = os.path.join(changelog_dir, 'HEADER.md')
    changelog_name = os.environ.get('CHANGELOG_NAME', '')
    if not changelog_name and os.path.exists('setup.py'):
        try:
            changelog_name = setup_query('--name')
        except subprocess.CalledProcessError:
            changelog_name = ''
    if not changelog_name:
        changelog_name = 'Unknown'
    release_dates = git_tag_dates()

    output = ''
    header = ''
    release_changelog = release_changes(changelog_dir, only_versions=only_versions)
    if changelog_releases == 'all':
        if os.path.exists(header_filename):
            with open(header_filename) as fh:
                header = fh.read()
    else:
        if changelog_releases in release_changelog.keys():
            release_changelog = {changelog_releases: release_changelog[changelog_releases]}

    if header:
        output += header + os.linesep

    releases = list(release_changelog.keys())
    releases.reverse()

    for release in releases:
        changes = release_changelog[release]
        if not changes or release in ['first_commit', 'last_commit']:
            continue
        date = datetime.fromtimestamp(int(release_dates[release]))
        output += f'{os.linesep}---{os.linesep}'
        output += f'## {changelog_name} {release} ({date:%Y-%m-%d}){os.linesep}'

        for change_type, change_desc in CHANGE_TYPES.items():
            if change_type not in changes.keys():
                continue

            output += f'### {change_desc}{os.linesep}'
            for changeid, change_text in changes[change_type].items():
                output += f'- {change_text}{os.linesep}'
        output += f'{os.linesep}'
    return output


def write_changelog(filename, changelog_releases: str=''):
    report_dir = os.path.dirname(filename)
    os.makedirs(report_dir, exist_ok=True)
    with open(filename, 'w') as report_handle:
        report_handle.write(changelog_contents(changelog_releases=changelog_releases))


def main():
    artifacts_dir = os.environ.get('SD_ARTIFACTS_DIR', 'artifacts')
    report_dir = os.path.join(artifacts_dir, 'reports/changelog')
    report_filename = os.environ.get('CHANGELOG_FILENAME', os.path.join(report_dir, 'changelog.md'))

    git_fetch_tags()
    write_changelog(report_filename)


if __name__ == '__main__':
    sys.exit(main())
