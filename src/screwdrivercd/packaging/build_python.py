# Copyright 2019, Oath Inc.
# Licensed under the terms of the Apache 2.0 license.  See the LICENSE file in the project root for terms
"""
Python packaging command line wrapper
"""
import os
import shlex
import subprocess  # nosec
import sys

from ..utility.package import setup_query
from ..utility.run import run_and_log_output


def build_sdist_package(package_name, setup_args, build_log_dir, package_artifacts):
    """
    Build a Python sdist format package

    Parameters
    ----------
    package_name
    setup_args
    build_log_dir
    package_artifacts

    Returns
    -------
    str
        Path to the created package or None if creation failed
    """
    before = []
    if os.path.exists('dist'):
        before = os.listdir('dist')

    run_and_log_output(command=[sys.executable, 'setup.py', 'sdist'] + setup_args, logfile=f'{build_log_dir}/sdist_build.log')
    if os.path.exists('dist'):
        for filename in os.listdir('dist'):
            if filename in before:
                continue
            dest_filename = f'{package_artifacts}/{filename}'
            print(f'Moving dist/{filename} -> {dest_filename}')
            os.rename(f'dist/{filename}', dest_filename)
            return [dest_filename]


def build_wheel_packages(package_name, setup_args, build_log_dir, package_artifacts):
    artifacts_dir = os.environ.get('SD_ARTIFACTS_DIR', 'artifacts')
    manylinux = os.environ.get('MANYLINUX', 'True').lower() in ['1', 'true', 'on']
    plat = os.environ.get('AUDITWHEEL_PLAT', '')
    wheel_build_dir = os.path.join(artifacts_dir, 'wheelbuild')

    print('# Generating wheel package', flush=True)
    failed = set()
    built_packages = set()
    before = set(os.listdir('dist'))
    run_and_log_output([sys.executable, 'setup.py', 'bdist_wheel'] + setup_args, logfile=f'{build_log_dir}/wheel_build.log')
    after = set(os.listdir('dist'))
    for filename in after - before:
        if filename.endswith('none-any.whl'):
            print('Package is generating a pure python wheel, skipping manylinux packaging', flush=True)
            dest_filename = f'{package_artifacts}/{filename}'
            print(f'Moving dist/{filename} -> {dest_filename}')
            os.rename(f'dist/{filename}', f'{dest_filename}')
            return [dest_filename]

    if manylinux and plat:
        print('\n# Generating manylinux wheels', flush=True)
        for entry in os.listdir('/opt/python'):
            interpreter_dir = os.path.join('/opt/python', entry)
            pip_command = f'{interpreter_dir}/bin/pip'
            if os.path.isdir(interpreter_dir) and os.path.exists(pip_command):
                print(f'Generating wheel for the {entry!r} python interpreter', flush=True)
                try:
                    run_and_log_output([pip_command, 'wheel', '.', '-w', wheel_build_dir], logfile=f'{build_log_dir}/wheel_build_{entry}.log')
                except subprocess.CalledProcessError:
                    failed.add(entry)

        print('\n## Bundling shared libraries into the wheel packages', flush=True)
        for wheel in os.listdir(wheel_build_dir):
            full_wheel_filename = os.path.join(wheel_build_dir, wheel)
            if not wheel.startswith(package_name + '-'):
                # print(f'Removing dependency wheel {wheel!r}', flush=True)
                os.remove(full_wheel_filename)
                continue
            if wheel.endswith('none-any.whl'):
                # Not a binary wheel
                continue
            print(f'Bundling shared libraries for wheel package {wheel!r}', flush=True)

            # This has to be run in a separate virtualenv using pypirun because auditwheel currently pins the
            # version of the wheel package which creates package dependency conflicts.
            run_and_log_output(
                ['pypirun', 'auditwheel', 'auditwheel', 'repair', full_wheel_filename, '--plat', plat, '-w', wheel_build_dir],
                logfile=f'{build_log_dir}/wheel_auditwheel_{wheel}.log'
            )
            os.remove(full_wheel_filename)

    print('\n# Storing generated packages in the build artifacts')
    for filename in os.listdir(wheel_build_dir):
        dest_filename = f'{package_artifacts}/{filename}'
        print(f'Moving {wheel_build_dir}/{filename} -> {dest_filename}', flush=True)
        os.rename(f'{wheel_build_dir}/{filename}', dest_filename)
        built_packages.add(dest_filename)

    if failed:
        print(f'Package build failed for {failed}')
    return list(built_packages)


def main():
    # Get settings from the environment
    artifacts_dir = os.environ.get('SD_ARTIFACTS_DIR', 'artifacts')
    package_artifacts = os.path.join(artifacts_dir, 'packages')
    wheel_build_dir = os.path.join(artifacts_dir, 'wheelbuild')
    build_log_dir = os.path.join(artifacts_dir, 'logs/build')
    setup_args = shlex.split(os.environ.get('SETUP_ARGS', ''))
    package_types = [_.strip().lower() for _ in os.environ.get('PACKAGE_TYPES', 'sdist,wheel').split(',')]

    # Get values from the setup.py/setup.cfg
    package_name = setup_query('--name')

    os.makedirs(package_artifacts, exist_ok=True)
    os.makedirs(build_log_dir, exist_ok=True)
    os.makedirs(wheel_build_dir, exist_ok=True)
    os.makedirs('dist', exist_ok=True)

    failed = set()
    for package_type in package_types:
        if package_type == 'sdist':
            print(f'# Building sdist package', flush=True)
            result = build_sdist_package(package_name, setup_args, build_log_dir, package_artifacts)
            print(f'    Created package: {result}')
        elif package_type == 'wheel':
            print('Building wheel package(s)', flush=True)
            result = build_wheel_packages(package_name, setup_args, build_log_dir, package_artifacts)
            for package in result:
                print(f'    Created package: {package}')


if __name__ == '__main__':
    main()
