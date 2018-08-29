
from collections import OrderedDict
from typing import Callable, Any, Optional, List, Tuple, Dict

__all__ = ['Reformer', 'link', 'item']
ATTR_NAME: str = '__fields__'
TARGET_ALIAS: str = 'target'


class _Target:

    def __init__(self, getter: Optional[Callable[[Any], Any]]=lambda obj: obj) -> None:
        self._getter: Callable[[Any], Any] = getter
        self.__item: bool = False
        self.__null: bool = False

    @staticmethod
    def __get_value(value, obj, item=None) -> Any:
        if isinstance(value, _Target):
            if item is not None and value.__item:
                return value._get(item)
            else:
                return value._get(obj)
        return value

    @classmethod
    def as_(cls, schema) -> Any:
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

    def iter_(self, schema):
        getter = self._getter

        def _getter(obj):
            obj = getter(obj)
            if isinstance(obj, dict):
                obj = [{'key': k, 'value': v} for k, v in obj.items()]

            if isinstance(schema, dict):
                res = {}
                _key, _value = list(schema.items())[0]
                for item in obj:
                    res[self.__get_value(_key, obj, item)] = self.__get_value(_value, obj, item)
                return res
            if isinstance(schema, (tuple, list)):
                res = []
                _value = schema[0]
                for item in obj:
                    res.append(self.__get_value(_value, obj, item))
                return res

        self._getter = _getter
        return self

    def to_(self, type):
        getter = self._getter
        self._getter = lambda obj: type(getter(obj))
        return self

    def to_str(self):
        return self.to_(str)

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
        attrs[ATTR_NAME] = list(set(attrs[ATTR_NAME]))
        return type.__new__(mcs, name, bases, attrs)


class _Link:

    def __getattr__(self, item):
        return getattr(_Target(), item)


class _Item:

    def __getattr__(self, item):
        return getattr(_Target(), item).item_

    def iter_(self, *args, **kwargs):
        return _Target().iter_(*args, **kwargs).item_


link = _Link()
item = _Item()


class Reformer(metaclass=_ReformerMeta):

    @classmethod
    def transform(cls, _target: Any, **kwargs):
        return cls()._transform(_target, **kwargs)

    link = link
    item = item

    def _transform(self, target: Any, many: bool=False, blank=True):
        if many:
            return [self._transform(item, blank=blank) for item in target]
        result = {}
        for attr in self.__fields__:
            if attr not in [TARGET_ALIAS]:
                value = getattr(self, attr)._get(target)
                if not value and blank:
                    result[attr] = blank if blank is not True else None
                elif value:
                    result[attr] = value
        return result

    __call__ = _transform
