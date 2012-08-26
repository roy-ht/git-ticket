from setuptools import setup

setup(name="gitticket",
      version='0.1',
      description="git-ticket",
      author='Hiroyuki Tanaka',
      author_email='aflc0x@gmail.com',
      url='https://www.github.com/aflc/git-ticket',
      packages=['gitticket'],
      entry_points=dict(console_scripts=['git-ticket=gitticket:main']),
      zip_safe=False)
