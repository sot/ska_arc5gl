# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Access the Chandra archive via the arc5gl tool.
"""

import six
import pexpect
import os

# Should put in a watchdog timer to exit from arc5gl after a period of inactivity
import ska_helpers

__version__ = ska_helpers.get_version(__name__)


class Arc5gl(object):
    def __init__(self, echo=False, timeout=100000):
        """Create an object for sending commands to arc5gl and waiting for the
        prompt indicating command completion.  Example::

          arc5gl = Ska.arc5gl.Arc5gl()
          arc5gl.sendline('obsid=21151')
          arc5gl.sendline('get acis2{evt2}')
          del arc5gl  # explicitly shut things down, good idea

        If the file ``${HOME}/.arc5gl_user`` exists then the content will be taken
        as the user name to pass to the ``arc5gl`` Perl application for authentication.
        Otherwise the linux username will be used.

        :param echo: echo arc5gl output (default=False)
        :param timeout: wait for up to timeout seconds for response (default=100000)
        """
        args = ['--stdin']

        arc5gl_user_file = os.path.join(os.environ['HOME'], '.arc5gl_user')
        if os.path.exists(arc5gl_user_file):
            user = open(arc5gl_user_file).read().strip()
            args = args + ['--user={}'.format(user)]

        self.prompt = 'ARC5GL> '
        spawn = pexpect.spawn if six.PY2 else pexpect.spawnu
        self.arc5gl = spawn('/proj/sot/ska/bin/arc5gl', args=args, timeout=timeout)
        self.arc5gl.expect(self.prompt)
        self.echo = echo
        self.arc5gl.setecho(echo)

    def sendline(self, line):
        """Send a single line to arc5gl and wait for the return prompt.  There is no return value.

        :param line: line of input
        """
        self.arc5gl.sendline(line)
        self.arc5gl.expect(self.prompt)
        if self.echo:
            print(self.prompt + self.arc5gl.before)

    def __del__(self):
        self.arc5gl.sendline('exit')
        self.arc5gl.expect(pexpect.EOF)
        self.arc5gl.close()
        if self.echo:
            print('Closed arc5gl')
