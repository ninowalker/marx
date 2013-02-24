'''
Created on Feb 23, 2013

@author: nino
'''
import inspect
import functools

class Step(object):
    def __init__(self, 
                 call, 
                 result_map=None,
                 context_map=None,
                 extra_kwargs=None):
        
        if isinstance(call, basestring):
            mod, func = call.rsplit('.', 1)
            call = getattr(__import__(mod, fromlist=[func]), func)
        self._call = call
        
        if result_map is None:
            result_map = {}
        if isinstance(result_map, dict):
            self.result_mapper = functools.partial(self.default_result_mapper, mapping=result_map)
        else:
            self.result_mapper = result_map
        
        if context_map is None:
            context_map = {}
        if isinstance(context_map, dict):
            self.context_mapper = functools.partial(self.default_context_mapper, mapping=context_map)
        else:
            self.context_mapper = context_map
        
        self.extra_kwargs = extra_kwargs
        # figure out if the callable accepts context
        # as a parameter as not to enforce a strict contract
        self._pass_context = 'context' in inspect.getargspec(call)[0]
        
    def __call__(self, context):
        kwargs = {}
        if self._pass_context:
            kwargs['context'] = context
        kwargs.update(self.context_mapper(context))
        if self.extra_kwargs:
            kwargs.update(self.extra_kwargs)
        result = self._call(**kwargs)
        self.result_mapper(result, context)

    def default_result_mapper(self, result, context, mapping):
        for to_key, from_mapper in mapping.iteritems():
            if callable(from_mapper):
                value = from_mapper(result, context)
            elif isinstance(from_mapper, basestring):
                value = result[from_mapper]
            elif isinstance(from_mapper, (list, tuple)):
                value = result
                for k in from_mapper:
                    value = value[k]
            setattr(context, to_key, value)
            
    def default_context_mapper(self, context, mapping):
        kwargs = {}
        for from_key, to_kwarg in mapping.iteritems():
            kwargs[to_kwarg] = getattr(context, from_key)
        return kwargs
    
