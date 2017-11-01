#!/usr/bin/env python

import exceptions
import logging
import os
import pytest
import shlex
import subprocess
import sys
import threading


SLEEP_TIME = sys.argv[1:] or '1'
TIMEOUT = 3
LOGGER = None


def setup_logging(name=__name__, level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'):  # noqa: E501
    global LOGGER

    formatter = logging.Formatter(format)
    logger = logging.getLogger(name)
    logger.setLevel(level)

    sh = logging.StreamHandler()
    sh.setFormatter(formatter)
    sh.setLevel(level)

    logger.addHandler(sh)

    logger.debug('test message')

    LOGGER = logger
    return logger


class Command(object):

    def __init__(self, cmd, timeout=3):
        self.cmd = shlex.split(cmd)
        self.cmd[0] = self._find_executable(self.cmd[0])
        self.timeout = timeout
        self.p = None
        self.logger = logging.getLogger(__name__)
        self.rc = None

    def run(self, timeout=None):
        if timeout:
            self.timeout = timeout

        self.rc = None
        self.logger.info('Command: %s', self.cmd)
        self.logger.info('Starting thread')
        self.p = subprocess.Popen(self.cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)  # noqa: E501

        def communicate():
            self.stdout, self.stderr = self.p.communicate()
            self.logger.info('Finished thread')

        thread = threading.Thread(target=communicate)
        thread.start()
        thread.join(self.timeout)

        self.logger.info('Thread alive: %s', thread.is_alive())
        if thread.is_alive():
            self.logger.info('Terminating process')
            self.p.terminate()
            self.logger.info('RC: %s', self.p.returncode)  # noqa: E501
            thread.join()
            raise Exception('Timer expired')

        self.rc = self.p.returncode
        self.logger.info('Returning RC: %s', self.rc)
        return self.rc

    def _find_executable(self, executable):
        path_dirs = os.environ.get('PATH')

        if not path_dirs:
            raise exceptions.PathEnvironmentVariableNotSetError()

        orig_dir = os.getcwd()
        for path_dir in path_dirs.split(os.pathsep):
            if not os.path.exists(path_dir):
                continue

            os.chdir(path_dir)
            if os.path.exists(executable):
                exec_path = os.path.abspath(executable)
                os.chdir(orig_dir)
                return exec_path

        os.chdir(orig_dir)
        raise exceptions.ExecutableNotFoundError(executable)


class TestCommand(object):
    def test_command_happy_path(self):
        """Testing happy path that command executes successfully"""

        cmd = Command('sleep 0.1')
        rc = cmd.run(timeout=1)
        assert rc == 0

    def test_command_times_out(self):
        """Test sleep 10 will timeout after 1 second and raise Exception"""

        with pytest.raises(Exception) as exp:
            cmd = Command('sleep 10')
            cmd.run(timeout=1)
        exp.match('Timer expired')


if __name__ == '__main__':
    setup_logging(__name__)
    cmd = Command('sleep 1')
    print(cmd.run(timeout=3))
