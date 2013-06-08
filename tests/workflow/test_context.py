'''
Created on Feb 24, 2013

@author: nino
'''
import unittest
from marx.workflow.context import DefaultContext, Field
from marx.workflow.exceptions import InvalidContextAssignment
import nose.tools


class TestField(unittest.TestCase):
    def test1(self):
        class Context(DefaultContext):
            user = Field(int)
            str_or_float = Field(str, float)

        assert hasattr(Context, 'USER')
        assert Context.USER == 'user'
        assert hasattr(Context, 'user')
        c = Context(None)
        c.user = 1
        c.str_or_float = "s"
        c.str_or_float = 1.
        assert c.user == 1
        with nose.tools.assert_raises(InvalidContextAssignment): #@UndefinedVariable
            c.user = "s"

        with nose.tools.assert_raises(InvalidContextAssignment): #@UndefinedVariable
            c.str_or_float = 1

        # check that we haven't corrupted the class
        c2 = Context(None)
        assert c2.user is None

    def test_contribute_to_class(self):
        pass

    def test_multiple_inheritance(self):
        class A(DefaultContext):
            a = Field(int)

        class B(DefaultContext):
            b = Field(str)

        class C(A, B):
            c = Field(int)

        c = C()
        for f in "abc":
            assert hasattr(c, f)

        assert not hasattr(c, "d")
