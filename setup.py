import os
from setuptools import setup

from marx import __version__

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "celerybus",
    version = __version__,
    author = "Nino Walker",
    author_email = "nino.walker@gmail.com",
    description = read("README.md").split("\n", 1)[0],
    url='https://github.com/ninowalker/marx',
    license = "BSD",
    packages=['marx'],
    long_description=read('README.md'),
    setup_requires=['nose>=1.0', 'coverage==3.6', 'nosexcover', 'mock'],
    test_suite = 'nose.collector',
    classifiers=[
        "License :: OSI Approved :: BSD License",
    ],
    #entry_points = {'console_scripts': ['']}
)
