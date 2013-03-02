'''
Created on Feb 24, 2013

@author: nino
'''
from marx.workflow.exceptions import InvalidContextAssignment

class Field(object):
    def __init__(self, types=None, docs=None):
        if types:
            assert isinstance(types, (list, tuple))
        self.types = types if not types else tuple(types)
        self.name = None
        self.docs = docs
        
    def _get(self, instance):
        return getattr(instance, "_" + self.name, None)
    
    def _set(self, instance, value):
        if self.types and not isinstance(value, self.types):
            raise InvalidContextAssignment((self.name, value))
        setattr(instance, "_" + self.name, value)
        
    def contribute_to_class(self, cls, name):
        self.name = name
        setattr(cls, name, property(self._get, self._set))
        setattr(cls, name.upper(), name)
        

class ContextBase(type):
    def __new__(cls, name, bases, attrs):
        contributors = {}
        for k, v in attrs.iteritems():
            if hasattr(v, 'contribute_to_class'):
                contributors[k] = v
        for k in contributors:
            attrs.pop(k)
        cls = super(ContextBase, cls).__new__(cls, name, bases, attrs)
        for k, v in contributors.iteritems():
            v.contribute_to_class(cls, k)
        return cls


class DefaultContext(object):
    __metaclass__ = ContextBase
    
    message = Field()
    
    def __init__(self, workflow=None):
        self.workflow = workflow
        self._replies = []
        
    def reply(self, message):
        self.workflow.reply(message, self)
        self._replies.append(message)
        
    @property
    def replies(self):
        """Returns a copy of the replies."""
        return [] + self._replies



