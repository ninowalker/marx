'''
Created on Feb 23, 2013

@author: nino
'''
import unittest
from mock import Mock, patch
from marx.workflow.step import Step, LogicUnit, ArgSpec, ResultSpec
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

        def reverse_and_join(result, context): #@UnusedVariable
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

    def test_auto_map(self):
        m_cm = Mock()
        m_cm.moo = True
        m_cm.meow = False
        this = self

        class Unit(LogicUnit):
            def __call__(self, moo, meow, context):
                this.success = (moo, meow, context)

        Step(Unit(), arg_map=Unit.AutoMap())(m_cm)
        assert this.success == (True, False, m_cm), this.success

    def test_auto_map_override(self):
        class Ctx:
            moo = True
        this = self

        class Unit(LogicUnit):
            def __call__(self, cow):
                this.success = cow

        Step(Unit(), arg_map=Unit.AutoMap({Unit.COW: 'moo'}))(Ctx())
        assert this.success == (True), this.success

    def test_auto_map_bad_field(self):
        class Ctx:
            cow = True
        this = self

        class Unit(LogicUnit):
            def __call__(self, cow, pig):
                this.success = cow, pig

        nose.tools.assert_raises(AttributeError, Step(Unit(), arg_map=Unit.AutoMap()), Ctx())  # @UndefinedVariable

    def test_auto_map_default(self):
        class Ctx:
            cow = True
        this = self

        class Unit(LogicUnit):
            def __call__(self, cow, pig="not kosher"):
                this.success = cow, pig

        Step(Unit(), arg_map=Unit.AutoMap())(Ctx())
        assert self.success == (True, "not kosher")

    def test_callable_by_str(self):
        ctx = DefaultContext()
        with patch('inspect.getargspec') as argspec:
            argspec.return_value = [[]]
            Step('%s.a_callable' % __name__)(ctx)
        assert a_callable.called

    def test_results_declaration(self):

        class Unit(LogicUnit):

            meow = ArgSpec(bool, docs="The meow.")
            the_cat_has_spoken = ResultSpec(bool, docs="Has the cat spoken?")

            def __call__(self, meow):
                self.the_cat_has_spoken.value = meow

                return self.get_result_map()

        test = Unit()
        result = test(meow=True)
        assert isinstance(result, dict)
        assert result['the_cat_has_spoken']

        result = test(meow=False)
        assert not result['the_cat_has_spoken']

    def test_default_result_value(self):

        class Unit(LogicUnit):

            meow = ArgSpec(bool, docs="The meow.")
            the_cat_has_spoken = ResultSpec(bool, default=True, docs="Has the cat spoken?")

            def __call__(self, meow):
                return self.get_result_map()

        test = Unit()
        result = test(meow=True)
        assert isinstance(result, dict)
        assert result['the_cat_has_spoken']

    def test_wrong_type_result_value(self):

        class Unit(LogicUnit):

            the_cat_has_spoken = ResultSpec(bool, default=True, docs="Has the cat spoken?")

            def __call__(self):
                self.the_cat_has_spoken.value = 'meow'
                return self.get_result_map()

        test = Unit()
        nose.tools.assert_raises(TypeError, test)

    def test_resultspec_in_multiple_instances(self):

        class Unit(LogicUnit):

            meow = ArgSpec(bool, docs="The meow.")
            the_cat_has_spoken = ResultSpec(bool, docs="Has the cat spoken?")

            def __call__(self, meow):
                self.the_cat_has_spoken.value = meow
                return self.get_result_map()

        test = Unit()
        doppelganger_test = Unit()
        result_1 = test(meow=True)
        result_2 = doppelganger_test(meow=False)
        assert result_1['the_cat_has_spoken']
        assert not result_2['the_cat_has_spoken']

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

    def test_default_value(self):
        class HasADefault(LogicUnit):
            meow = ArgSpec(int, default=1)

            def __call__(self, meow):
                if meow == 1:
                    raise ValueError()
                raise IndexError()

        assert HasADefault.MEOW is not None
        nose.tools.assert_raises(ValueError, HasADefault()) #@UndefinedVariable
        nose.tools.assert_raises(ValueError, HasADefault(), meow=1) #@UndefinedVariable
        nose.tools.assert_raises(IndexError, HasADefault(), meow=10) #@UndefinedVariable

    def test_nullable(self):
        class Nullable(LogicUnit):
            meow = ArgSpec(int, nullable=True)

            def __call__(self, meow):
                if meow is None:
                    raise ValueError()
                return meow

        # the default is none
        nose.tools.assert_raises(ValueError, Nullable()) #@UndefinedVariable
        nose.tools.assert_raises(ValueError, Nullable(), meow=None) #@UndefinedVariable

        assert Nullable()(meow=10) == 10


class TestArgSpec(unittest.TestCase):
    def test_any_arg(self):
        s = ArgSpec(default="meow")
        assert s.default == 'meow'
        assert s.types == (object,)
        self.assertRaises(ValueError, ArgSpec, int, meow="bad arg")

    def test_bad_kwarg(self):
        self.assertRaises(ValueError, ArgSpec, int, meow="bad arg")



class TestFlow(unittest.TestCase):
    def test_run_example_1(self):
        #import pdb; pdb.set_trace()
        ctx = run_example_1()
        assert ctx

