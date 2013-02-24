'''
Created on Feb 23, 2013

@author: nino
'''
from drone.workflow.exceptions import Abort


class DefaultContext(object):
    def __init__(self, message):
        self.message = message
        self._replies = []
        
    def reply(self, message):
        self._replies.append(message)
        
    @property
    def replies(self):
        """Returns a copy of the replies."""
        return [] + self._replies


class Workflow(object):
    def __init__(self, 
                 steps, 
                 context_cls=DefaultContext,
                 on_error=None, 
                 on_abort=None):
        self.steps = steps
        self.context_cls = context_cls
        self.on_error = on_error or self.default_on_error
        self.on_abort = on_abort or self.default_on_abort
        
    def __call__(self, message):
        context = self.context_cls(message)
        try:
            for step in self.steps:
                try:
                    step(context=context)
                except Abort, e:
                    self.on_abort(context)
                    break
            return context
        except Exception, e:
            return self.on_error(e, context)
                
    def default_on_error(self, e, context):
        raise e
    
    def default_on_abort(self, context):
        pass