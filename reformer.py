import operator
from collections import OrderedDict

__all__ = ['Reformer', 'link', 'item']
ATTR_NAME = '__fields__'
TARGET_ALIAS = 'target'


class _Target:

    def __init__(self, getter=lambda obj: obj):
        self._getter = getter
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

    @classmethod
    def as_(cls, schema):
        def _getter(obj):
            if isinstance(schema, dict):
                res = {}
                for key, value in schema.items():
                    res[cls.__get_value(key, obj)] = cls.__get_value(value, obj)
                return res
            if isinstance(schema, (list, tuple)):
                res = []
                for value in schema:
                    res.append(cls.__get_value(value, obj))
                return res
            raise NotImplementedError
        return cls(getter=_getter)

    def iter_(self, schema, condition=None):
        getter = self._getter

        def _getter(obj):
            obj = getter(obj)
            if isinstance(obj, dict):
                obj = [{'key': k, 'value': v} for k, v in obj.items()]

            if isinstance(schema, dict):
                res = {}
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
                return res

        self._getter = _getter
        return self

    def compare_(self, item, operator=operator.eq):
        getter = self._getter
        self._getter = lambda obj: operator(getter(obj), self.__get_value(item, obj))
        return self

    def in_(self, container):
        getter = self._getter
        self._getter = lambda obj: (getter(obj) in container)
        return self

    def contains_(self, item):
        getter = self._getter
        self._getter = lambda obj: (item in getter(obj))
        return self

    def to_(self, type):
        getter = self._getter
        self._getter = lambda obj: type(getter(obj))
        return self

    def to_str(self):
        return self.to_(str)

    def to_int(self):
        return self.to_(int)

    def choice_(self, choices, default=None):
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

    def call_(self, function):
        getter = self._getter

        def _getter(obj):
            obj = getter(obj)
            return function(obj)

        self._getter = _getter
        return self

    @property
    def null_(self):
        self.__null = True
        return self

    @property
    def item_(self):
        self.__item = True
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

    def __call__(self, *args, **kwargs):
        getter = self._getter

        def _getter(obj):
            _args = [a._get(obj) if isinstance(a, _Target) else a for a in args]
            _kw = {k._get(obj) if isinstance(k, _Target) else k: v._get(obj) if isinstance(v, _Target) else v
                   for k, v in kwargs.items()}
            return getter(obj)(*_args, **_kw)
        self._getter = _getter
        return self

    __getitem__ = __getattr__

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
        return self.compare_(other)

    def __gt__(self, other):
        return self.compare_(other, operator.gt)

    def __ge__(self, other):
        return self.compare_(other, operator.ge)

    def __lt__(self, other):
        return self.compare_(other, operator.lt)

    def __le__(self, other):
        return self.compare_(other, operator.le)

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

        attrs[ATTR_NAME].extend([key for key, value in attrs.items() if isinstance(value, _Target)])
        return type.__new__(mcs, name, bases, attrs)


class _Link:

    def __getattr__(self, item):
        return getattr(_Target(), item)


class _Item:

    def __getattr__(self, item):
        return getattr(_Target(), item).item_

    def iter_(self, *args, **kwargs):
        return _Target().iter_(*args, **kwargs).item_

    def as_(self, *args, **kwargs):
        return _Target().as_(*args, **kwargs).item_


link = _Link()
item = _Item()


class Reformer(metaclass=_ReformerMeta):
    _fields_ = ()

    @classmethod
    def transform(cls, _target, **kwargs):
        return cls()._transform(_target, **kwargs)

    link = link
    item = item

    def _transform(self, target, many=False, blank=True):
        if many:
            return [self._transform(item, blank=blank) for item in target]
        result = OrderedDict()
        for field in self._fields_:
            result[field] = target[field]
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
