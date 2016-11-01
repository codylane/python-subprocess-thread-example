#!/usr/bin/env python

import time
import threading
import subprocess
import os
import sys

import pytest

SLEEP_TIME=sys.argv[1:] or '1'
TIMEOUT=3


def timestamp():
    return time.strftime('%Y-%m-%dT%H:%M:%S')

class Command(object):
    def __init__(self, cmd, timeout=3):
        self.cmd = cmd
        self.timeout = timeout
        self.p = None

    def run(self, timeout):
        print '{0} Starting thread'.format(timestamp())
        self.p = subprocess.Popen(self.cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        def communicate():
            self.stdout, self.stderr = self.p.communicate()
            print '{0} thread finished'.format(timestamp())

        thread = threading.Thread(target=communicate)
        thread.start()
        thread.join(timeout)

        print 'is_alive={0}'.format(thread.is_alive())
        if thread.is_alive():
            print '{0} Terminating process'.format(timestamp())
	    self.p.terminate()
            print '{0} rc={0}'.format(timestamp(), self.p.returncode)
            thread.join()
	    raise Exception('timer expired')
	return self.p.returncode


class TestCommand(object):
    def test_command_happy_path(self):
        """Testing happy path that command executes successfully"""
        cmd = Command(['sleep', '0.1'])
        rc = cmd.run(timeout=1)
        assert rc == 0

    def test_command_times_out(self):
        """Test sleep 10 will timeout after 1 second and raise Exception"""
        with pytest.raises(Exception) as exp:
            cmd = Command(['sleep', '10'])
            cmd.run(timeout=1)
	exp.match('timer expired')
