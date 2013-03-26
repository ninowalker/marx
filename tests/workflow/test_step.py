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
        m._accepts_context = True
        ctx = DefaultContext()
        with patch('inspect.getargspec') as argspec:
            argspec.return_value = [[]]
            Step(m)(ctx)
        
        assert m.called
        m.assert_called_once_with(context=ctx)
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
            Step(m, result_map={'baz': 'returned'})(ctx)
            
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
            Step(m, result_map={'baz': reverse_and_join})(ctx)
            
        assert m.called
        assert ctx.baz == 'rabcba'
        
    def test_result_mapper_list(self):
        m = Mock()
        m.return_value = {'returned': {'bar': 1, 'boz': 2}}
        ctx = DefaultContext()
        ctx.baz = ctx.boz = None
        
        with patch('inspect.getargspec') as argspec:
            argspec.return_value = [[]]
            Step(m, result_map={'baz': ('returned', 'bar'),
                                'boz': ('returned', 'boz')})(ctx)
            
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
        m._accepts_context = False
        m.return_value = {'returned': 'bar'}
        ctx = DefaultContext()
        with patch('inspect.getargspec') as argspec:
            argspec.return_value = [[]]
            Step(m, extra_kwargs=dict(meow=True))(ctx)
            
        assert m.called
        m.assert_called_once_with(meow=True)

    def test_arg_mapper(self):
        m = Mock()
        m._accepts_context = False
        ctx = DefaultContext()
        ctx.message = 1
        ctx.meow = 1
        
        with patch('inspect.getargspec') as argspec:
            argspec.return_value = [[]]
            Step(m, arg_map={'message': 'message'})(ctx)
            Step(m, arg_map={'meow': 'message'})(ctx)
            
        assert m.called
        m.assert_any_call(message=1)
        m.assert_any_call(meow=1)

    def test_arg_mapper_custom(self):
        m = Mock()
        m._accepts_context = None
        m_cm = Mock(return_value={'moo': True})
        ctx = DefaultContext()
        with patch('inspect.getargspec') as argspec:
            argspec.return_value = [[]]
            Step(m, arg_map=m_cm)(ctx)
            
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
            astr = ArgSpec(str, docs="A string value")
            
            def __call__(self, an_arg, astr="s", context=None):
                this.value = an_arg
        
        assert Unit.AN_ARG == "an_arg"
        assert Unit.ASTR == "astr"
        
        u = Unit()
        # this is fine:
        u(an_arg=1, astr="grr")
        assert self.value == 1
        assert Unit._accepts_context
        
        # this should fail type checking
        nose.tools.assert_raises(TypeError, u, an_arg=1, astr=1) #@UndefinedVariable
        
    def test_composition(self):
        class Domain(object): pass
        class UserProfile(object): pass
        
        class IsSameDomainUser(LogicUnit):
            domain = ArgSpec(Domain)
            user = ArgSpec(UserProfile)
            
            def __call__(self, user, domain):
                if not user.domain_id == domain.id:
                    raise Exception()
                
        assert not IsSameDomainUser._accepts_context
                
        s = Step(IsSameDomainUser(), arg_map={IsSameDomainUser.USER: 'actor', 
                                              IsSameDomainUser.DOMAIN: 'domain'})
        
        class Context(DefaultContext):
            domain = Domain()
            actor = 1
        
        assert s
        assert isinstance(s._call, IsSameDomainUser)
        with nose.tools.assert_raises(TypeError): #@UndefinedVariable
            s(Context())
            
        
class TestFlow(unittest.TestCase):
    def test_run_example_1(self):
        #import pdb; pdb.set_trace()
        ctx = run_example_1()
        assert ctx
    
        