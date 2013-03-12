"""
This defines a workflow around the imperative: "Throw a Pie".

In a simple system this is about 5 lines of code. But in others,
where business logic requires the interaction of many systems,
logic is smeared around and duplicated, and not well encapsulated.

The approach here splits execution into discrete units which can be 
composed into other workflows encouraging reuse, testability, etc.
"""


from marx.workflow.step import LogicUnit, ArgSpec, Step
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
    
    def __call__(self, maker):
        maker.increment("pies_made", 1)
        return {'pie': 'lemon'}

class ThrowThing(LogicUnit):
    """Subject Object (Verb) Indirect-object"""
    
    actor = ArgSpec(User)
    
    # we omit target and thing here, because we don't
    # need to enumerate/type constrain the values in this example
    
    def __call__(self, actor, thing, target):
        actor.increment("things_throw")
        print "Throwing", thing
        return {'hit': actor.can_throw()} 


class ThrowPieContext(DefaultContext):
    """The execution context for the ThrowPieWorkflow.""" 
    thrower = Field(User, docs="Somebody has to throw it")
    target = Field(User, docs="At somebody")
    pie = Field(str, docs="A pie, which we make along the way")
    was_hit = Field(bool, docs="Success of the throwing event")

""" A workflow is a series of steps."""
ThrowPieWorkflow = Workflow()

ThrowPieWorkflow.add_step(IsUserAuthorized("throw_pie"),
                          # we bind from the context to the arguments of the method.
                          arg_map={IsUserAuthorized.USER: ThrowPieContext.THROWER})
ThrowPieWorkflow.add_step(MakePie(),
                          arg_map={MakePie.MAKER: ThrowPieContext.THROWER},
                          # we bind from the returned result back to the context
                          result_map={ThrowPieContext.PIE: 'pie'})
ThrowPieWorkflow.add_step(ThrowThing(),
                          arg_map={ThrowThing.ACTOR: ThrowPieContext.THROWER,
                                   ThrowThing.TARGET: ThrowPieContext.TARGET,
                                   ThrowThing.THING: ThrowPieContext.PIE},
                          result_map={ThrowPieContext.WAS_HIT: 'hit'})

def run():
    """To execute a workflow, prepare a context, and pass it through."""
    ctx = ThrowPieContext()
    ctx.thrower = User("bob")
    ctx.target = User("frank")
    try:
        ThrowPieWorkflow(ctx)
        assert ctx.was_hit is not None
        assert ctx.pie == 'lemon'
        return ctx
    except PermissionDeniedError:
        assert False