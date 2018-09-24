import operator
from collections import OrderedDict

__all__ = ['Reformer', 'Field']
ATTR_NAME = '__fields__'
TARGET_ALIAS = 'target'


class _Target:

    def __init__(self, getter=lambda obj: obj):
        self._initial_getter = getter
        self._getter = lambda obj: self._initial_getter(obj)
        self.__item = False
        self.__null = False

    @staticmethod
    def __get_value(value, obj, item=None):
        if isinstance(value, _Target):
            if item is not None and value.__item:
                return value._get(item)
            else:
                return value._get(obj)
        return value

    def as_(self, schema):
        getter = self._getter

        def _getter(obj):
            item = getter(obj)
            if isinstance(schema, dict):
                res = OrderedDict()
                for key, value in schema.items():
                    res[self.__get_value(key, obj, item)] = self.__get_value(value, obj, item)
                return res
            if isinstance(schema, (list, tuple)):
                res = []
                for value in schema:
                    res.append(self.__get_value(value, obj, item))
                return type(schema)(res)
            raise NotImplementedError
        self._getter = _getter
        return self

    in_form = as_

    def iter(self, schema, condition=None):
        getter = self._getter

        def _getter(obj):
            obj = getter(obj)
            if isinstance(obj, dict):
                obj = [{'key': k, 'value': v} for k, v in obj.items()]

            if isinstance(schema, dict):
                res = OrderedDict()
                _key, _value = list(schema.items())[0]
                for item in obj:
                    if condition and not self.__get_value(condition, obj, item):
                        continue
                    res[self.__get_value(_key, obj, item)] = self.__get_value(_value, obj, item)
                return res
            if isinstance(schema, (tuple, list)):
                res = []
                _value = schema[0]

                for item in obj:
                    if condition and not self.__get_value(condition, obj, item):
                        continue
                    res.append(self.__get_value(_value, obj, item))
                return type(schema)(res)

        self._getter = _getter
        return self

    def compare(self, item, operator=operator.eq):
        getter = self._getter
        self._getter = lambda obj: operator(getter(obj), self.__get_value(item, obj))
        return self

    def at(self, container):
        getter = self._getter
        self._getter = lambda obj: (getter(obj) in container)
        return self

    def contains(self, item):
        getter = self._getter
        self._getter = lambda obj: (item in getter(obj))
        return self

    def to(self, type):
        getter = self._getter
        self._getter = lambda obj: type(getter(obj))
        return self

    def to_str(self):
        return self.to(str)

    def to_int(self):
        return self.to(int)

    def map(self, choices, default=None):
        getter = self._getter

        def _getter(obj):
            obj = getter(obj)
            if isinstance(choices, (list, tuple)):
                assert isinstance(obj, int)
                if len(choices) > obj:
                    return choices[obj]
                return default
            if isinstance(choices, dict):
                return choices.get(obj, default)
            return getattr(choices, obj, default)
        self._getter = _getter
        return self

    def call(self, function):
        getter = self._getter

        def _getter(obj):
            obj = getter(obj)
            return function(obj)

        self._getter = _getter
        return self

    handle = call

    def set_null(self):
        self.__null = True
        return self

    def set_as_item(self, value=True):
        self.__item = value
        return self

    def __getattr__(self, item):
        getter = self._getter

        def _getter(obj):
            obj = getter(obj)
            if isinstance(item, str) and hasattr(obj, item):
                return getattr(obj, item)
            return obj[item]
        self._getter = _getter
        return self

    __getitem__ = __getattr__

    def __call__(self, *args, **kwargs):
        getter = self._getter

        def _getter(obj):
            _args = [a._get(obj) if isinstance(a, _Target) else a for a in args]
            _kw = {k._get(obj) if isinstance(k, _Target) else k: v._get(obj) if isinstance(v, _Target) else v
                   for k, v in kwargs.items()}
            return getter(obj)(*_args, **_kw)
        self._getter = _getter
        return self

    def __iter__(self):
        raise NotImplementedError

    def __add__(self, other):
        getter = self._getter
        if isinstance(other, _Target):
            self._getter = lambda obj: (getter(obj) + other._getter(obj))
        else:
            self._getter = lambda obj: (getter(obj) + other)
        return self

    def __radd__(self, other):
        getter = self._getter
        if isinstance(other, _Target):
            self._getter = lambda obj: (other._getter(obj) + getter(obj))
        else:
            self._getter = lambda obj: (other + getter(obj))
        return self

    def __mul__(self, other):
        getter = self._getter
        if isinstance(other, _Target):
            self._getter = lambda obj: (getter(obj) * other._getter(obj))
        else:
            self._getter = lambda obj: (getter(obj) * other)
        return self

    def __rmul__(self, other):
        getter = self._getter
        if isinstance(other, _Target):
            self._getter = lambda obj: (other._getter(obj) * getter(obj))
        else:
            self._getter = lambda obj: (other * getter(obj))
        return self

    def __eq__(self, other):
        return self.compare(other)

    def __gt__(self, other):
        return self.compare(other, operator.gt)

    def __ge__(self, other):
        return self.compare(other, operator.ge)

    def __lt__(self, other):
        return self.compare(other, operator.lt)

    def __le__(self, other):
        return self.compare(other, operator.le)

    def __hash__(self):
        return hash(self._getter)

    def _get(self, obj):
        try:
            return self._getter(obj)
        except (KeyError, AttributeError, TypeError):
            if self.__null:
                return
            raise


class _ReformerMeta(type):
    @classmethod
    def __prepare__(mcs, name, bases):
        return OrderedDict()

    def __new__(mcs, name, bases, attrs):
        attrs.setdefault(ATTR_NAME, [])
        for base in bases:
            for _name in getattr(base, ATTR_NAME, []):
                if _name not in attrs:
                    attrs[ATTR_NAME].append(_name)
        if '_fields_' in attrs:
            for name in attrs['_fields_']:
                attrs[name] = Field(name)
        for key, value in attrs.items():
            if isinstance(value, _Target):
                if isinstance(value, Field):
                    value.set_as_item(False)
                    value._name = key
                    if value._source is None:
                        value._source = key
                attrs[ATTR_NAME].append(key)
        return type.__new__(mcs, name, bases, attrs)


class _Link:

    def __getattr__(self, item):
        return getattr(_Target(), item)

    __getitem__ = __getattr__


class _Item:

    def __getattr__(self, item):
        return getattr(_Target(), item).set_as_item()

    __getitem__ = __getattr__

    def iter(self, *args, **kwargs):
        return _Target().iter(*args, **kwargs).set_as_item()

    def as_(self, *args, **kwargs):
        return _Target().as_(*args, **kwargs).set_as_item()


class Field(_Target):

    def __init__(self, source=None, schema=None, to=None,
                 handler=None, choices=None, required=True):
        self._name = None
        self._source = source

        def initial_getter(obj):
            result = obj
            for _source in self._source.split('.'):
                if _source in ['self']:
                    continue
                if hasattr(result, _source):
                    result = getattr(result, _source)
                result = result[_source]
            return result
        super().__init__(getter=initial_getter)
        self.set_as_item()
        if not required:
            self.set_null()
        if to is not None:
            self.to(to)
        if handler is not None:
            self.handle(handler)
        if schema is not None:
            self.as_(schema=schema)
        if choices is not None:
            self.map(choices)

    def iter(self, schema, condition=None):
        if isinstance(schema, (list, tuple)):
            return super().iter(schema, condition=condition)
        return super().iter([Field('self', schema=schema), ], condition=condition)


class MapField(Field):

    def __init__(self, source, choices):
        super().__init__(source, choices=choices)
        if choices is not None:
            self.map(choices)


class SchemaField(Field):

    def __init__(self, source, schema):
        super().__init__(source, schema=schema)


class TypeField(Field):
    def __init__(self, source, to):
        super().__init__(source, to=to)


class HandleField(Field):

    def __init__(self, source, handler):
        super().__init__(source, handler=handler)


class MethodField(Field):

    def __init__(self):
        self.__instance = None
        super().__init__('self', handler=self.__handler)

    def __handler(self, obj):
        method_name = 'get_' + self._name
        method = getattr(self.__instance, method_name)
        return method(obj)

    def __get__(self, instance, owner):
        if owner is None:
            return self
        self.__instance = instance
        return self


class Reformer(metaclass=_ReformerMeta):
    _fields_ = ()

    @classmethod
    def transform(cls, _target, **kwargs):
        return cls()._transform(_target, **kwargs)

    def _transform(self, target, many=False, blank=True):
        if many:
            return [self._transform(item, blank=blank) for item in target]
        result = OrderedDict()
        for attr in self.__fields__:
            if attr not in [TARGET_ALIAS]:
                value = getattr(self, attr)._get(target)
                if value is None:
                    if blank and blank is not True:
                        result[attr] = blank
                    elif blank:
                        result[attr] = None
                else:
                    result[attr] = value
        return result

    __call__ = _transform
