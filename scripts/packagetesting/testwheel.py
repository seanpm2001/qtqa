#!/usr/bin/env python3
# ###########################################################################
#
# Copyright (C) 2019 The Qt Company Ltd.
# Contact: https://www.qt.io/licensing/
#
# This file is part of the Quality Assurance module of the Qt Toolkit.
#
# $QT_BEGIN_LICENSE:GPL-EXCEPT$
# Commercial License Usage
# Licensees holding valid commercial Qt licenses may use this file in
# accordance with the commercial license agreement provided with the
# Software or, alternatively, in accordance with the terms contained in
# a written agreement between you and The Qt Company. For licensing terms
# and conditions see https://www.qt.io/terms-conditions. For further
# information use the contact form at https://www.qt.io/contact-us.
#
# GNU General Public License Usage
# Alternatively, this file may be used under the terms of the GNU
# General Public License version 3 as published by the Free Software
# Foundation with exceptions as appearing in the file LICENSE.GPL3-EXCEPT
# included in the packaging of this file. Please review the following
# information to ensure the GNU General Public License requirements will
# be met: https://www.gnu.org/licenses/gpl-3.0.html.
#
# $QT_END_LICENSE$
#
# ############################################################################


from argparse import ArgumentParser, RawTextHelpFormatter
import os
import subprocess
import sys
import tempfile


"""
Qt Package testing script for testing Qt for Python wheels
"""

PYINSTALLER_EXAMPLE = 'widgets/widgets/tetrix.py'


VERSION = -1


def examples():
    """Compile a list of examples to be tested"""
    result = ['widgets/mainwindows/mdi/mdi.py']
    if VERSION >= 6:
        result.extend(['declarative/extending/chapter5-listproperties/listproperties.py',
                       '3d/simple3d/simple3d.py'])
    else:
        result.extend(['opengl/hellogl.py',
                       'multimedia/player.py',
                       'charts/donutbreakdown.py',
                       'webenginewidgets/tabbedbrowser/main.py'])
    return result


def execute(args):
    """Execute a command and print output"""
    log_string = '[{}] {}'.format(os.path.basename(os.getcwd()),
                                  ' '.join(args))
    print(log_string)
    exit_code = subprocess.call(args)
    if exit_code != 0:
        raise RuntimeError('FAIL({}): {}'.format(exit_code, log_string))

def run_process(args):
    """Execute a command and return a tuple of exit code/stdout"""
    popen = subprocess.Popen(args, universal_newlines=1,
                             stdout=subprocess.PIPE)
    lines = popen.stdout.readlines()
    popen.wait()
    return popen.returncode, lines


def run_process_output(args):
    """Execute a command and print output"""
    result = run_process(args)
    print(result[1])
    return result[0]


def run_example(root, path):
    print('Launching {}'.format(path))
    exit_code = run_process_output([sys.executable, os.path.join(root, path)])
    print('{} returned {}\n\n'.format(path, exit_code))


def has_pyinstaller():
    """Checks for PyInstaller"""
    code, lines = run_process([sys.executable, "-m", "pip", "list"])
    return any(line.lower().startswith("pyinstaller") for line in lines)


def test_pyinstaller(example):
    name = os.path.splitext(os.path.basename(example))[0]
    print('Running PyInstaller test of {}'.format(name))
    current_dir = os.getcwd()
    result = False
    with tempfile.TemporaryDirectory() as tmpdirname:
        try:
            os.chdir(tmpdirname)
            level = "CRITICAL" if sys.platform == "darwin" else "WARN"
            cmd = ['pyinstaller', '--name={}'.format(name),
                   '--log-level=' + level, example]
            execute(cmd)
            binary = os.path.join(tmpdirname, 'dist', name, name)
            if sys.platform == "win32":
                binary += '.exe'
            execute([binary])
            result = True
        except RuntimeError as e:
            print(str(e))
        finally:
            os.chdir(current_dir)
    return result


if __name__ == "__main__":
    parser = ArgumentParser(description='Qt for Python package tester',
                            formatter_class=RawTextHelpFormatter)
    parser.add_argument('--no-pyinstaller', '-p', action='store_true',
                        help='Skip pyinstaller test')

    options = parser.parse_args()
    do_pyinst = not options.no_pyinstaller

    if do_pyinst and sys.version_info[0] < 3:  # Note: PyInstaller no longer supports Python 2
        print('PyInstaller requires Python 3, test disabled')
        do_pyinst = False
    root = None
    for p in sys.path:
        if os.path.basename(p) == 'site-packages':
            root = os.path.join(p, 'PySide6')
            if os.path.exists(root):
                VERSION = 6
            else:
                root = os.path.join(p, 'PySide2')
                VERSION = 2
            root_ex = os.path.join(root, 'examples')
            break
    if not root or not os.path.exists(root):
        print('Could not locate any PySide module.')
        sys.exit(1)
    if not os.path.exists(root_ex):
        m = "PySide{} module found without examples. Did you forget to install wheels?".format(VERSION)
        print(m)
        sys.exit(1)
    print('Detected PySide{} at {}.'.format(VERSION, root))
    for e in examples():
        run_example(root_ex, e)

    if not do_pyinst:
        sys.exit(0)
    if not has_pyinstaller():
        print('PyInstaller not found, skipping test')
        sys.exit(0)

    if test_pyinstaller(os.path.join(root_ex, PYINSTALLER_EXAMPLE)):
        print("\nPyInstaller test successful")
    else:
        print("\nProblem running PyInstaller")
        sys.exit(1)
