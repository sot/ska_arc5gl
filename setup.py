# Licensed under a 3-clause BSD style license - see LICENSE.rst
from setuptools import setup

from ska_helpers.setup_helper import duplicate_package_info

name = "ska_arc5gl"
namespace = "Ska.arc5gl"

packages = ["ska_arc5gl"]
package_dir = {name: name}

duplicate_package_info(packages, name, namespace)
duplicate_package_info(package_dir, name, namespace)

setup(name=name,
      author='Tom Aldcroft',
      description='Use arc5gl to access the Chandra archive',
      author_email='taldcroft@cfa.harvard.edu',
      use_scm_version=True,
      setup_requires=['setuptools_scm', 'setuptools_scm_git_archive'],
      zip_safe=False,
      packages=packages,
      package_dir=package_dir,
      )
