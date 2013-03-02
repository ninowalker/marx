'''
Created on Mar 2, 2013

@author: nino
'''

class PermissionDeniedError(Exception):
    pass

class User(object):
    def __init__(self, name):
        self.name = name
    
    def is_authorized(self, action): return True
    def can_throw(self): return False
    def increment(self, stat, count=1): pass


