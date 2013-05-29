'''
Created on Feb 23, 2013

@author: nino
'''
import unittest
from marx.workflow.flow import Workflow
from marx.workflow.exceptions import Abort, SkipStep
import nose.tools
from mock import Mock
from marx.workflow.context import DefaultContext


class TestAbort(unittest.TestCase):
    def abort_if_not_none(self, context):
        if self.x != None:
            raise Abort()

    def skip(self, context):
        raise SkipStep()
        context.reply(1)

    def reply(self, context):
        context.reply(1)

    def assign(self, v):
        self.x = v

    def test_abort(self):
        self.x = None

        abort_if_not_none = self.abort_if_not_none
        assign = self.assign

        m = Mock()

        # test unaborted workflow 
        w = Workflow(steps=[abort_if_not_none, m])
        w(DefaultContext())
        assert m.called

        # test simple aborted workflow
        m.reset_mock()
        self.x = 1
        w = Workflow(steps=[abort_if_not_none, m])
        w(DefaultContext())
        assert not m.called

        # test mid workflow abort
        m.reset_mock()
        self.x = None
        w = Workflow(steps=[abort_if_not_none,
                            lambda context: assign(True),
                            abort_if_not_none,
                            m])
        w(DefaultContext())
        assert self.x is True
        assert not m.called

    def test_custom_on_abort(self):
        # test custom abort
        m = Mock()
        m_a = Mock()
        self.x = 1
        w = Workflow(steps=[self.abort_if_not_none, m],
                     on_abort=m_a)
        w(DefaultContext())
        assert not m.called
        assert m_a.called

    def test_reply_abort(self):
        self.x = None
        abort_if_not_none = self.abort_if_not_none
        assign = self.assign
        reply = self.reply

        # assert that replies carry through
        self.x = None
        w = Workflow(steps=[abort_if_not_none, reply, reply,
                            lambda context: assign(True),
                            abort_if_not_none, reply])
        ctx = w(DefaultContext())
        assert ctx.replies == [1, 1]

    def test_skip(self):
        w = Workflow(steps=[self.skip])
        ctx = w(DefaultContext())
        assert ctx.replies == []


class TestProgrammerError(unittest.TestCase):
    def test_bad_concatenation(self):
        with nose.tools.assert_raises(TypeError):
            Workflow() + 10


class TestOnError(unittest.TestCase):
    def test_default_on_error(self):
        m = Mock(side_effect=ValueError)

        w = Workflow(steps=[m])
        with nose.tools.assert_raises(ValueError):  # @UndefinedVariable
            w(DefaultContext())

    def test_custom_on_error(self):
        m = Mock(side_effect=ValueError)
        m_f = Mock(return_value=1)
        w = Workflow(steps=[m], on_error=m_f)
        r = w(DefaultContext())
        assert m.called
        assert m_f.called
        assert r == 1
        
