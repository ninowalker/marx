'''
Created on Feb 23, 2013

@author: nino
'''

#PostCommentIsValidParent = Step(IsValidParent, 
#   result_map={'context_parent': Mapping('parent', [Message], required=True, default=Ponies)}, 
#   context_map={'collection_context': ('collectionContext', 
#                                       [None, ContentSourceMeta])}), #@UndefinedVariable

class Mapping(object):  
    def __init__(self, key, types, required=False, default=None):
        self.key = key
        self.types = types
        self.required = required
        self.default = default
    
    def apply(self, map_to, result, context_object):
        if self.required and self.key not in result:
            #raise ProgrammerFail()
            pass
        if self.key not in result:
            return self.default
        value = result[self.key]
        if value is None:
            setattr(context_object, map_to, value)
            return
        if self.types and not isinstance(value, self.types):
            pass
