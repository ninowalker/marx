'''
Created on Feb 23, 2013

@author: nino
'''
import inspect
import functools


class Step(object):
    def __init__(self,
                 call,
                 arg_map=None,
                 result_map=None,
                 extra_kwargs=None,
                 docs=None):
        """
        :param call: A callable or a string that can be resolved to a callable.
        :param arg_map: A mapping from fields in the context to arguments of the callable.
        :param result_map: A dict that defines translation from the returned object to the context.
        :param extra_kwargs: Additional kwargs to pass to the callable; useful for config at bind time.
        :param docs: A doc string.
        """

        # allow late binding by providing a string
        if isinstance(call, basestring):
            mod, func = call.rsplit('.', 1)
            call = getattr(__import__(mod, fromlist=[func]), func)
        assert callable(call)
        self._call = call

        if result_map is None:
            result_map = {}
        if isinstance(result_map, dict):
            self.result_mapper = functools.partial(self.default_result_mapper, mapping=result_map)
        else:
            self.result_mapper = result_map

        if arg_map is None:
            arg_map = {}
        if isinstance(arg_map, dict):
            self.arg_mapper = functools.partial(self.default_arg_mapper, mapping=arg_map)
        else:
            self.arg_mapper = arg_map

        self.extra_kwargs = extra_kwargs
        # figure out if the callable accepts context
        # as a parameter as not to enforce a strict contract
        pass_context = getattr(call, '_accepts_context', None)
        if pass_context is None:
            pass_context = 'context' in inspect.getargspec(getattr(call, '__call__', call))[0]
        self._pass_context = pass_context
        self.docs = docs

    def __call__(self, context):
        kwargs = {}
        if self._pass_context:
            kwargs['context'] = context
        kwargs.update(self.arg_mapper(context))
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

    def default_arg_mapper(self, context, mapping):  # @UnusedVariable
        kwargs = {}
        for to_kwarg, from_key in mapping.iteritems():
            kwargs[to_kwarg] = getattr(context, from_key)
        return kwargs


class LogicUnitBase(type):
    """Provides the class-declare-time magic for a logical unit."""
    def __new__(cls, name, bases, attrs):
        specs = [s for s in attrs.items() if hasattr(s[1], 'contribute_to_class')]
        attrs = dict(s for s in attrs.items() if not hasattr(s[1], 'contribute_to_class'))

        cls = super(LogicUnitBase, cls).__new__(cls, name, bases, attrs)
        call = attrs.get('__call__')
        if not call:
            return cls

        args = inspect.getargspec(call)

        # add the constants representing each argument.
        for arg in args.args[1:]:
            setattr(cls, arg.upper(), arg)
        if args.keywords:
            setattr(cls, 'KWARGS', args.keywords)
        if args.varargs:
            setattr(cls, 'ARGS', args.varargs)

        # keep track of whether the invocation expects a context
        setattr(cls, '_accepts_context', 'context' in args.args)
        setattr(cls, '_args', args)

        # let them contribute to the class
        for arg, spec in specs:
            spec.contribute_to_class(cls, arg)
        return cls


class ArgSpec(object):
    def __init__(self, *types, **kwargs):
        assert isinstance(types, (list, tuple))
        self.types = types if not types else tuple(types)
        isinstance(None, self.types)
        self.name = None
        self.docs = kwargs.pop('docs', None)

    def contribute_to_class(self, cls, name):
        call = getattr(cls, '__call__')
        setattr(cls, '__call__', self.check_input(name, call))

    def check_input(self_, name, func):  # @NoSelf
        def wrapper(self, **kwargs):
            if name not in kwargs:
                raise KeyError(name)
            if not isinstance(kwargs[name], self_.types):
                raise TypeError((name, self_.types))
            return func(self, **kwargs)
        return wrapper


class LogicUnit(object):
    __metaclass__ = LogicUnitBase

    def __call__(self):
        abstract  # @UndefinedVariable ~ this is a python guru move

    @classmethod
    def AutoMap(cls, overrides=None):
        """Provides a mechanism for automatically binding like-named properties of the
        context to like named arguments to eliminate boilerplate, but possibly create
        execution time errors, if care is not taken. With great power comes great
        responsibility - Toby Miguire.
        """
        def auto_map(context):
            args = cls._args
            overrides_ = overrides or {}
            kwargs = {}
            for arg in args.args[1:]:
                if arg == 'context':
                    # this is special
                    continue
                kwargs[arg] = getattr(context, overrides_.get(arg, arg))
            return kwargs
        return auto_map
