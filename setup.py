import os
from setuptools import setup, find_packages

from marx import __version__
import glob

README = "README.md"

base = os.path.dirname(__file__)
local = lambda x: os.path.join(base, x)

def read(fname):
    return open(local(fname)).read()

def hydrate_examples():
    examples = {}
    for f in glob.glob(local('examples/*')) + glob.glob(local('tests/*')) + glob.glob(local('tests/*/*')):
        if os.path.isdir(f):
            continue
        examples[os.path.basename(f)] = "\n    ".join(read(f).split("\n"))
    print examples.keys()
    readme = read(README +".in") % examples
    with open(local(README), "w") as f:
        f.write(readme)

hydrate_examples()

setup(
    name="marx",
    version=__version__,
    author="Nino Walker",
    author_email="nino.walker@gmail.com",
    description=read(README).split("\n", 1)[0],
    url='https://github.com/ninowalker/marx',
    license="BSD",
    packages=find_packages(exclude=["tests.*", "tests"]),
    long_description=read(README),
    setup_requires=['nose>=1.0', 'coverage==3.6', 'nosexcover', 'mock'],
    test_suite='nose.collector',
    classifiers=[
        "License :: OSI Approved :: BSD License",
    ],
)


