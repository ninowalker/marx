'''
Created on Feb 23, 2013

@author: nino
'''
import inspect
import functools
import threading
import types


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

    def default_arg_mapper(self, context, mapping): # @UnusedVariable
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
    """Defines the the acceptable types for an argument, along with useful things, like
    documentation."""

    __UNSPECIFIED = object()

    def __init__(self, *types_, **kwargs):
        """Constuctor.

        :params *args: a list of python types for input checking
        :param docs: a description of this argument
        :param default: a default value if unspecified
        :param nullable: allow a null/unspecified input; sets the default to None
                         if default is not provided
        """
        self.types = tuple((object,)) if not types_ else tuple(types_)
        self.name = None
        self.docs = kwargs.pop('docs', None)
        self.default = kwargs.pop('default', self.__UNSPECIFIED)
        nullable = kwargs.pop('nullable', False)
        self.normalizer = kwargs.pop('normalizer', self.default_normalizer)

        if nullable:
            self.types += (types.NoneType,)
            if self.default == self.__UNSPECIFIED:
                self.default = None
        if kwargs:
            raise ValueError("unknown keywords: %s" % kwargs.keys())

    def contribute_to_class(self, cls, name):
        call = getattr(cls, '__call__')
        setattr(cls, '__call__', self.check_input(name, call))

    def check_input(self_, name, func): # @NoSelf
        def wrapper(self, **kwargs):
            if name not in kwargs:
                if self_.default == self_.__UNSPECIFIED:
                    raise KeyError("Undefined argument: '%s' for '%s'" % (name, type(self).__name__))
                kwargs[name] = self_.default

            kwargs[name] = self_.normalizer(name, kwargs[name], self_.types)
            return func(self, **kwargs)
        return wrapper

    @classmethod
    def default_normalizer(cls, name, value, types):
        if not isinstance(value, types):
            raise TypeError("Incorrect argument: '%s' for '%s'."
                            "Expected type '%s' but received '%s' of type '%s'." % (name,
                                                                                   cls.__name__,
                                                                                   types,
                                                                                   value,
                                                                                   type(value)))
        return value

    @classmethod
    def as_list(cls, name, value, types):
        if not isinstance(value, (list, tuple)):
            value = [value]
        return [cls.default_normalizer(name, v, types) for v in value]


class ResultObject(dict):
    """
    If using a result spec, the logic unit will return an instance
    of this class. It provides handy dict and object like properties
    with type checking.
    """
    def __init__(self, fields):
        object.__setattr__(self, '_fields', fields)
        object.__setattr__(self, '_values', {name: spec._default for name, spec in fields.iteritems()})

    def __getattr__(self, name):
        return self._values[name]

    def __setattr__(self, name, value):
        self.__setitem__(name, value)

    def __setitem__(self, name, value):
        spec = self._fields[name]
        if not isinstance(value, spec.types):
            raise TypeError((value, spec.types))
        self._values[name] = value

    def __getitem__(self, name):
        return self._values[name]


class ResultSpec(object):
    """
    The result counterpart to an ArgSpec. Defines the return values for a step.
    This provides a hook for documentation and an automatically generated result map.
    """
    def __init__(self, *types_, **kwargs):
        """Constructor.

        :params *args: a list of python types for return value checking
        :param docs: a description of this result
        :param default: a default return value, values begin as none unless specified
        """
        self.types = tuple((object,)) if not types_ else tuple(types_)
        self.docs = kwargs.pop('docs', None)
        self._default = kwargs.pop('default', None)
        if kwargs:
            raise ValueError("unknown keywords: %s" % kwargs.keys())

    def contribute_to_class(self, cls, name):
        setattr(cls, name, self)
        if hasattr(cls, '_result_fields'):
            cls._result_fields[name] = self
            return
        setattr(cls, '_result_fields', {name: self})
        setattr(cls, '_results', threading.local())
        setattr(cls, '__call__', self.manage_result(getattr(cls, '__call__')))
        setattr(cls, 'result', property(lambda self_: self_._results.value))

    def manage_result(_, func): # @NoSelf
        @functools.wraps(func)
        def wrapper(self, **kwargs):
            try:
                self._results.value = ResultObject(self._result_fields)
                res = func(self, **kwargs)
                if res is None:
                    return self._results.value
                return res
            finally:
                self._results.value = None
        return wrapper


class LogicUnit(object):
    __metaclass__ = LogicUnitBase

    def __call__(self):
        abstract # @UndefinedVariable ~ this is a python guru move

    @classmethod
    def AutoMap(cls, overrides=None):
        """
        Provides a mechanism for automatically binding like-named properties of the
        context to like named arguments to eliminate boilerplate, but possibly create
        execution time errors, if care is not taken. With great power comes great
        responsibility - Toby Miguire.

        :param dict overrides: a mapping of arg names to context attributes
           to explicitly map over.
        """
        def auto_map(context):
            spec = cls._args
            overrides_ = overrides or {}
            # populate the kwargs and include defaults
            kwargs = dict(zip(spec.args[-(len(spec.defaults or [])):], spec.defaults or []))
            for arg in spec.args[1:]:
                if arg == 'context': # this is special
                    kwargs['context'] = context
                    continue
                mapped_field = overrides_.get(arg, arg)
                if not hasattr(context, mapped_field):
                    if arg in kwargs: # it was provided by a default value
                        continue
                    raise AttributeError("Context does not have field '%s'. context=%r" % (mapped_field, context))
                kwargs[arg] = getattr(context, mapped_field)
            return kwargs
        return auto_map

    @classmethod
    def ResultMap(cls, ctx_cls, overrides=None):
        spec = {}
        for name, _ in cls._result_fields.iteritems():
            if hasattr(ctx_cls, name):
                spec[name] = name
        if overrides:
            spec.update(overrides)
        return spec
