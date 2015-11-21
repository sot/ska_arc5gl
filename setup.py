from setuptools import setup

setup(name='Ska.arc5gl',
      author = 'Tom Aldcroft',
      description='Use arc5gl to access the Chandra archive',
      author_email = 'aldcroft@head.cfa.harvard.edu',
      py_modules = ['Ska.arc5gl'],
      version='0.1.1',
      zip_safe=False,
      packages=['Ska'],
      package_dir={'Ska' : 'Ska'},
      package_data={}
      )
