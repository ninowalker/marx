import os
from setuptools import setup

from marx import __version__
import glob

README = "README.md"

base = os.path.dirname(__file__)
local = lambda x: os.path.join(base, x)

def read(fname):
    return open(local(fname)).read()

def hydrate_examples():
    examples = {}
    for f in glob.glob(local('examples/*')):
        examples[os.path.basename(f)] = "\n    ".join(read(f).split("\n"))
    readme = read(README +".in") % examples
    with open(local(README), "w") as f:
        f.write(readme)

hydrate_examples()

setup(
    name="celerybus",
    version=__version__,
    author="Nino Walker",
    author_email="nino.walker@gmail.com",
    description=read(README).split("\n", 1)[0],
    url='https://github.com/ninowalker/marx',
    license="BSD",
    packages=['marx'],
    long_description=read(README),
    setup_requires=['nose>=1.0', 'coverage==3.6', 'nosexcover', 'mock'],
    test_suite='nose.collector',
    classifiers=[
        "License :: OSI Approved :: BSD License",
    ],
)


