'''
Created on Feb 23, 2013

@author: nino
'''
from marx.workflow.exceptions import Abort, SkipStep
import sys
from marx.workflow.step import Step


class Workflow(object):
    def __init__(self,
                 steps=None,
                 on_error=None,
                 on_abort=None,
                 on_reply=None):
        self.steps = steps or []
        self.on_error = on_error or self.default_on_error
        self.on_abort = on_abort or self.default_on_abort
        self.reply = on_reply or self.default_on_reply

    def __call__(self, context):
        context.workflow = self
        try:
            for step in self.steps:
                try:
                    step(context=context)
                except SkipStep, e:
                    continue
            return context
        except Abort, a:
            return self.on_abort(context, a)
        except Exception, e:
            return self.on_error(e, context)

    def add_step(self, *args, **kwargs):
        self.steps.append(Step(*args, **kwargs))
        return self

    def default_on_error(self, e, context):
        raise type(e), e.message, sys.exc_info()[2]

    def default_on_abort(self, context, abort):
        return context

    def default_on_reply(self, reply, context):
        pass

    def __add__(self, rhs):
        '''
        The + operator returns a new Workflow instance,
            with the same steps as this one,
            followed by either the given right hand step,
            or the steps of the given right hand Workflow.
        '''
        if isinstance(rhs, Step):
            incoming = [rhs]
        elif isinstance(rhs, Workflow):
            incoming = rhs.steps
        else:
            raise TypeError('Only Steps or other Workflows can be '
                'concatenated to form new Workflows.')

        outgoing = self.steps + incoming
        return Workflow(steps=outgoing,
                        on_error=self.on_error,
                        on_abort=self.on_abort,
                        on_reply=self.reply)
