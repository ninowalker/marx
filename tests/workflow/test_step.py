'''
Created on Feb 23, 2013

@author: nino
'''
import unittest
from mock import Mock, patch
from marx.workflow.step import Step, LogicUnit, ArgSpec
import nose.tools
from tests.workflow.example_1 import run as run_example_1
from marx.workflow.context import DefaultContext


class Test(unittest.TestCase):
    def test_call_context(self):
        m = Mock()
        ctx = DefaultContext()
        with patch('inspect.getargspec') as argspec:
            argspec.return_value = [[]]
            Step(m)(ctx)
        
        assert m.called
        m.assert_called_once_with()
        m.reset_mock()

        with patch('inspect.getargspec') as argspec:
            argspec.return_value = [['context']]
            Step(m)(ctx)
        
        assert m.called
        m.assert_called_once_with(context=ctx)

    def test_result_mapper_str(self):
        m = Mock()
        m.return_value = {'returned': 'bar'}
        ctx = DefaultContext()
        ctx.baz = None
        with patch('inspect.getargspec') as argspec:
            argspec.return_value = [[]]
            Step(m, result_map={'returned': 'baz'})(ctx)
            
        assert m.called
        assert ctx.baz == 'bar'

    def test_result_mapper_callable(self):
        m = Mock()
        m.return_value = {'returned': ['abc', 'bar']}
        ctx = DefaultContext()
        ctx.baz = None
        
        def reverse_and_join(result, context):
            return "".join(result['returned'])[::-1]
        
        with patch('inspect.getargspec') as argspec:
            argspec.return_value = [[]]
            Step(m, result_map={reverse_and_join: 'baz'})(ctx)
            
        assert m.called
        assert ctx.baz == 'rabcba'
        
    def test_result_mapper_list(self):
        m = Mock()
        m.return_value = {'returned': {'bar': 1, 'boz': 2}}
        ctx = DefaultContext()
        ctx.baz = ctx.boz = None
        
        with patch('inspect.getargspec') as argspec:
            argspec.return_value = [[]]
            Step(m, result_map={('returned', 'bar'): 'baz',
                                ('returned', 'boz'): 'boz'})(ctx)
            
        assert m.called
        print ctx.__dict__
        assert ctx.baz == 1
        assert ctx.boz == 2
        
    def test_result_mapper_custom(self):
        m = Mock()
        m.return_value = {'returned': 'bar'}
        m_rm = Mock()
        ctx = DefaultContext()
        with patch('inspect.getargspec') as argspec:
            argspec.return_value = [[]]
            Step(m, result_map=m_rm)(ctx)
            
        assert m.called
        assert m_rm.called
        m_rm.assert_called_once_with(m.return_value, ctx)

    def test_extra_kwargs(self):
        m = Mock()
        m.return_value = {'returned': 'bar'}
        ctx = DefaultContext()
        with patch('inspect.getargspec') as argspec:
            argspec.return_value = [[]]
            Step(m, extra_kwargs=dict(meow=True))(ctx)
            
        assert m.called
        m.assert_called_once_with(meow=True)

    def test_context_mapper(self):
        m = Mock()
        ctx = DefaultContext()
        ctx.message = 1
        ctx.meow = 1
        
        with patch('inspect.getargspec') as argspec:
            argspec.return_value = [[]]
            Step(m, context_map={'message': 'message'})(ctx)
            Step(m, context_map={'message': 'meow'})(ctx)
            
        assert m.called
        m.assert_any_call(message=1)
        m.assert_any_call(meow=1)

    def test_context_mapper_custom(self):
        m = Mock()
        m_cm = Mock(return_value={'moo': True})
        ctx = DefaultContext()
        with patch('inspect.getargspec') as argspec:
            argspec.return_value = [[]]
            Step(m, context_map=m_cm)(ctx)
            
        assert m.called
        m.assert_called_once_with(**m_cm.return_value)

    def test_callable_by_str(self):
        m = Mock()
        ctx = DefaultContext()
        with patch('inspect.getargspec') as argspec:
            argspec.return_value = [[]]
            Step('%s.a_callable' % __name__)(ctx)
            
        assert a_callable.called

# don't change this name, test above depends on it. 
a_callable = Mock()


class TestLogicUnit(unittest.TestCase):
    def test_args(self):
        this = self
        class Unit(LogicUnit):
            astr = ArgSpec([str], docs="A string value")
            
            def __call__(self, an_arg, astr="s"):
                this.value = an_arg
        
        assert Unit.AN_ARG == "an_arg"
        assert Unit.ASTR == "astr"
        
        u = Unit()
        # this is fine:
        u(an_arg=1, astr="grr")
        assert self.value == 1
        
        # this should fail type checking
        nose.tools.assert_raises(TypeError, u, an_arg=1, astr=1) #@UndefinedVariable
        
    def test_composition(self):
        class Domain(object): pass
        class UserProfile(object): pass
        
        class IsSameDomainUser(LogicUnit):
            domain = ArgSpec([Domain])
            user = ArgSpec([UserProfile])
            
            def __call__(self, user, domain):
                if not user.domain_id == domain.id:
                    raise Exception()
                
        s = Step(IsSameDomainUser(), context_map={'actor': IsSameDomainUser.USER, 
                                                  'domain': IsSameDomainUser.DOMAIN})
        
        class Context(DefaultContext):
            domain = Domain()
            actor = 1
        
        assert s
        assert isinstance(s._call, IsSameDomainUser)
        with nose.tools.assert_raises(TypeError):
            s(Context())
        
class TestFlow(unittest.TestCase):
    def test_run_example_1(self):
        #import pdb; pdb.set_trace()
        ctx = run_example_1()
        assert ctx
    
        