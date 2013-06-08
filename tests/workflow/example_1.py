"""
This defines a workflow around the imperative: "Throw a Pie".

In a simple system this is about 5 lines of code. But in others,
where business logic requires the interaction of many systems,
logic is smeared around and duplicated, and not well encapsulated.

The approach here splits execution into discrete units which can be
composed into other workflows encouraging reuse, testability, etc.
"""


from marx.workflow.step import LogicUnit, ArgSpec, Step, ResultSpec
from marx.workflow.flow import Workflow
from marx.workflow.context import DefaultContext, Field
from tests.workflow.example_objects import User, PermissionDeniedError


class IsUserAuthorized(LogicUnit):
    """Checks permission for a user+action, and notifies authorities
    if it fails."""

    user = ArgSpec(User, docs="The user performing the action")

    def __init__(self, action):
        """
        @param action: The action that will be checked.
        """
        self.action = action

    def __call__(self, user):
        """
        @param user: The user performing the action.
        """
        if self.is_authorized(user):
            return
        self.notify_authorities(user, self.action)
        raise PermissionDeniedError(self.action)

    def is_authorized(self, user):
        return user.name in ("bob", "mary")

    def notify_authorities(self, user, action):
        print "AUTHORITIES!!!", user, " attempted illegal action", self.action


class MakePie(LogicUnit):
    """Makes the pie."""

    maker = ArgSpec(User, docs="The person making pie.")
    pie = ResultSpec(basestring, docs="Kind of pie")

    def __call__(self, maker):
        maker.increment("pies_made", 1)
        self.result.pie = 'lemon'


class ThrowThing(LogicUnit):
    """Subject Object (Verb) Indirect-object"""

    actor = ArgSpec(User)
    hit = ResultSpec(bool, default=False, docs="Did we get 'em?")

    # we omit target and thing here, because we don't
    # need to enumerate/type constrain the values in this example

    def __call__(self, actor, thing, target):
        actor.increment("things_throw")
        print "Throwing", thing
        self.result.hit = actor.can_throw()
        # we don't need to return, but we can.
        return self.result


class ThrowPieContext(DefaultContext):
    """The execution context for the ThrowPieWorkflow."""
    thrower = Field(User, docs="Somebody has to throw it")
    target = Field(User, docs="At somebody")
    pie = Field(str, docs="A pie, which we make along the way")
    was_hit = Field(bool, docs="Success of the throwing event")

""" A workflow is a series of steps."""
IsUserAuthorizedStep = Step(
    IsUserAuthorized("throw_pie"),
    # we bind from the context to the arguments of the method.
    arg_map={IsUserAuthorized.USER: ThrowPieContext.THROWER}
)
MakePieStep = Step(
    MakePie(),
    arg_map={MakePie.MAKER: ThrowPieContext.THROWER},
    # we bind from the returned result back to the context
    result_map=MakePie.ResultMap(ThrowPieContext)
)
ThrowThingStep = Step(
    ThrowThing(),
    arg_map=ThrowThing.AutoMap({ThrowThing.ACTOR: ThrowPieContext.THROWER,
                                ThrowThing.THING: ThrowPieContext.PIE}),
    result_map={ThrowPieContext.WAS_HIT: 'hit'}
)


""" There are a few ways to build up a workflow. By constructor..."""
ThrowPieWorkflowA = Workflow(steps=[
    IsUserAuthorizedStep,
    MakePieStep,
    ThrowThingStep,
])

""" Or using add_step..."""
ThrowPieWorkflowB = Workflow().add_step(
    IsUserAuthorizedStep
).add_step(
    MakePieStep
).add_step(
    ThrowThingStep
)

""" Or using the overloaded addition operator."""
EmptyWorkflow = Workflow()
ThrowPieWorkflowC_A = EmptyWorkflow + IsUserAuthorizedStep + MakePieStep
ThrowPieWorkflowC_B = EmptyWorkflow + ThrowThingStep
ThrowPieWorkflowC = ThrowPieWorkflowC_A + ThrowPieWorkflowC_B


def run():
    """To execute a workflow, prepare a context, and pass it through."""
    ctx = ThrowPieContext()
    ctx.thrower = User("bob")
    ctx.target = User("frank")
    for WorkflowType in (ThrowPieWorkflowA,
                         ThrowPieWorkflowB,
                         ThrowPieWorkflowC):
        try:
            WorkflowType(ctx)
            assert ctx.was_hit is not None
            assert ctx.pie == 'lemon'
            return ctx
        except PermissionDeniedError:
            assert False

    # Ensure that our ThrowPieWorkflowC did not modify its components
    assert EmptyWorkflow.steps == []
    assert ThrowThingStep not in ThrowPieWorkflowC_A.steps
