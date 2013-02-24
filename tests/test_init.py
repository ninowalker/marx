'''
Created on Feb 23, 2013

@author: nino
'''
import unittest
from drone import __version__
from distutils.version import StrictVersion


class Test(unittest.TestCase):
    def test_version(self):
        assert StrictVersion(__version__) > StrictVersion('0.0.0')

