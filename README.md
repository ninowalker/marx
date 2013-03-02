marx
=====

Framework/tools for python that get work done, make code easy to test, and turn spaghetti code back into something you can love.


Example
-------

    from marx.workflow.step import LogicUnit, ArgSpec, Step
    from marx.workflow.flow import Workflow
    from marx.workflow.context import DefaultContext, Field
    
    
    class User(object):
        def is_authorized(self, action): return True
        def can_throw(self): return False
    
    class IsUserAuthorized(LogicUnit):
        user = ArgSpec([User])
        
        def __init__(self, action):
            self.action = action
        
        def __call__(self, user):
            if user.is_authorized(self.action):
                return
            self.notify_authorities(user, self.action)
            raise PermissionDeniedError(self.action)
        
        def notify_authorities(self, user, action):
            print "AUTHORITIES!!!"
    
    class MakePie(LogicUnit):
        def __call__(self, maker):
            return {'pie': 'lemon'}
    
    class ThrowPie(LogicUnit):
        def __call__(self, target, pie, actor):
            print "Yummy", pie
            return {'hit': actor.can_throw()} 
    
    class ThrowPieContext(DefaultContext):
        thrower = Field([User])
        target = Field([User])
        pie = Field([str])
        was_hit = Field([bool])
    
    ThrowPieWorkflow = Workflow(
        steps=[Step(IsUserAuthorized("throw_pie"),
                    context_map={ThrowPieContext.THROWER: IsUserAuthorized.USER}),
               Step(MakePie(),
                    context_map={ThrowPieContext.THROWER: MakePie.MAKER},
                    result_map={'pie': ThrowPieContext.PIE}),
               Step(ThrowPie(),
                    context_map={ThrowPieContext.THROWER: ThrowPie.ACTOR,
                                 ThrowPieContext.TARGET: ThrowPie.TARGET,
                                 ThrowPieContext.PIE: ThrowPie.PIE},
                    result_map={'hit': ThrowPieContext.WAS_HIT})
               ]
    )
            
    class PermissionDeniedError(Exception):
        pass
    
    
    def run():
        ctx = ThrowPieContext(None)
        ctx.thrower = User()
        ctx.target = User()
        
        ThrowPieWorkflow(ctx)
        return ctx