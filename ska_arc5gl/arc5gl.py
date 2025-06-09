# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Access the Chandra archive via the arc5gl tool.
"""

import os
import re
from pathlib import Path

import pexpect
import six
from astropy.table import Table

# Should put in a watchdog timer to exit from arc5gl after a period of inactivity


class Arc5gl(object):
    """
    Class to create an object to communicate with arc5gl.

    Create an object for sending commands to arc5gl and waiting for the
    prompt indicating command completion.  Example::

        arc5gl = ska_arc5gl.Arc5gl()
        arc5gl.sendline('obsid=21151')
        arc5gl.sendline('get acis2{evt2}')
        del arc5gl  # explicitly shut things down, good idea

    If the file ``${HOME}/.arc5gl_user`` exists then the content will be taken
    as the user name to pass to the ``arc5gl`` Perl application for authentication.
    Otherwise the linux username will be used.

    :param echo: echo arc5gl output (default=False)
    :param timeout: wait for up to timeout seconds for response (default=100000)
    """
    def __init__(self, echo=False, timeout=100000):
        self.arc5gl = None
        self.echo = echo

        args = ['--stdin']
        arc5gl_user_file = os.path.join(os.environ['HOME'], '.arc5gl_user')
        if os.path.exists(arc5gl_user_file):
            user = open(arc5gl_user_file).read().strip()
            args = args + ['--user={}'.format(user)]

        self.prompt = 'ARC5GL> '
        spawn = pexpect.spawn if six.PY2 else pexpect.spawnu
        self.arc5gl = spawn('arc5gl', args=args, timeout=timeout)
        self.arc5gl.expect(self.prompt)
        self.arc5gl.setecho(echo)

    def sendline(self, line):
        """Send a single line to arc5gl and wait for the return prompt.  There is no return value.

        :param line: line of input
        """
        self.arc5gl.sendline(line)
        self.arc5gl.expect(self.prompt)
        if self.echo:
            print(self.prompt + self.arc5gl.before)

    def browse_(self, obsid, *products):
        import time

        all_products = [
            "acis0",
            "acis05",
            "acis1",
            "acis15",
            "acis2",
            "bias0",
            "hrc0",
            "hrc05",
            "hrc1",
            "hrc15",
            "hrc2",
            "aca0",
            "pcad0",
            "asp05",
            "asp1",
            "sim05",
            "obspar",
        ]
        unknown = [prod for prod in products if prod not in all_products]
        if unknown:
            raise Exception(f"Unknown products: {', '.join(unknown)}")
        if len(products) == 0:
            products = all_products

        self.arc5gl.sendline(f"obsid={obsid}")
        self.arc5gl.expect(self.prompt)

        for prod in products:
            self.arc5gl.sendline(f"obsid={obsid}")
            self.arc5gl.sendline(f"set {prod}")
            self.arc5gl.sendline(f"products={prod}")
            self.arc5gl.sendline("show")
            self.arc5gl.sendline("browse")
            self.arc5gl.sendline("clear")

        text = ""
        n_prompts = 0
        while True:
            line = self.arc5gl.read_nonblocking(10000, 10)
            idx = 0
            while (idx2 := line.find(self.prompt, idx)) >= 0:
                idx = idx2 + 1
                n_prompts += 1
            text += line
            if n_prompts == 6 * len(products):
                break

        files = []
        current = {}
        for line in text.splitlines():
            line = line.replace(self.prompt, "")
            if re.search("------", line):
                file_info = current
                current = {}
            elif not line.strip() or re.search("Filename", line):
                continue
            elif re.search(" = ", line):
                key, val = line.strip().split("=")
                current[key] = val
            else:
                line = line.strip()
                filename, size, date, time = line.split()
                file_info.update({
                    "filename": filename,
                    "size": size,
                    "date": date,
                    "time": time,
                })
                files.append(file_info)

        return Table(files), text



    def browse(self, obsid, *products):
        import re
        import tempfile

        all_products = [
            "acis0",
            "acis05",
            "acis1",
            "acis15",
            "acis2",
            "bias0",
            "hrc0",
            "hrc05",
            "hrc1",
            "hrc15",
            "hrc2",
            "aca0",
            "pcad0",
            "asp05",
            "asp1",
            "sim05",
            "obspar",
        ]
        if len(products) == 0:
            products = all_products

        products = [
            re.match("(?P<products>[a-z0-9]+)({(?P<pattern>[a-z0-9]+)})?", prod).groupdict()
            for prod in products
        ]

        unknown = [prod["products"] for prod in products if prod["products"] not in all_products]
        if unknown:
            raise Exception(f"Unknown products: {', '.join(unknown)}")

        with tempfile.NamedTemporaryFile(mode='w+', dir=os.getcwd()) as tf:
            print(f"tempfile at {tf.name}")
            filename = Path(tf.name)
            for prod in products:
                if prod["pattern"] is None:
                    pattern = prod["products"]
                else:
                    pattern = f"{prod['products']}{{{prod['pattern']}}}"
                tf.write(SCRIPT.format(obsid=obsid, products=prod["products"], prod_pattern=pattern))

            print(f"sourcing {filename.name}")
            self.arc5gl.sendline(f"source {filename.name}")

        text = ""
        while True:
            line = self.arc5gl.read_nonblocking(10000, 10)
            text += line
            if line.find(self.prompt) >= 0:
                break

        files = []
        current = {}
        for line in text.splitlines():
            if re.search("------", line):
                file_info = current
                current = {}
            elif not line.strip() or re.search("Filename", line) or re.search(r"\+\+\+\+\+\+\+\+", line):
                continue
            elif re.search(" = ", line):
                key, val = line.strip().split("=")
                current[key] = val
            elif len(line.split()) == 4:
                line = line.strip()
                filename, size, date, time = line.split()
                file_info.update({
                    "filename": filename,
                    "size": size,
                    "date": date,
                    "time": time,
                })
                files.append(file_info)

        t = Table(files)
        return t, text

    def __del__(self):
        if self.arc5gl is not None:
            self.arc5gl.sendline('exit')
            self.arc5gl.expect(pexpect.EOF)
            self.arc5gl.close()
        if self.echo:
            print('Closed arc5gl')



SCRIPT = """echo ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
obsid={obsid}
set {products}
products={products}
show
browse {prod_pattern}
clear
"""