from setuptools import setup
import sys
import os

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    try:
        return open(os.path.join(os.path.dirname(__file__), fname)).read()
    except Exception:
        return ''

install_requires = ['distribute', 'blessings', 'requests', 'rauth']
if sys.hexversion < 0x2070000:
    install_requires += ['argparse']
setup(name="gitticket",
      version='0.4',
      description="Git and issue tracking system integration",
      long_description=read('README.rst'),
      author='Hiroyuki Tanaka',
      author_email='aflc0x@gmail.com',
      url='https://www.github.com/aflc/git-ticket',
      packages=['gitticket'],
      install_requires=install_requires,
      entry_points=dict(console_scripts=['git-ticket=gitticket:main']),
      classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Natural Language :: Japanese',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2 :: Only',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
#        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Bug Tracking',
        'Topic :: Software Development :: Version Control',
        ],
      zip_safe=False)

