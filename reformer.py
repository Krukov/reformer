import operator
from collections import OrderedDict

ATTR_NAME = '__fields__'


class _Target:

    def __init__(self, getter=lambda obj: obj):
        self._initial_getter = getter
        self._getter = self._initial_getter
        self.__item = False
        self.__null = False
        self.__default = None

    def __get_value(self, value, obj, item=None):
        if isinstance(value, _Target):
            if item is not None and value.__item:
                return value._get(item)
            else:
                return value._get(obj)
        if isinstance(value, dict):
            res = OrderedDict()
            for key, value in value.items():
                res[self.__get_value(key, obj, item)] = self.__get_value(value, obj, item)
            return res
        if isinstance(value, Reformer):
            value.content['parent'] = obj
            return value._transform(item or obj)
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
            return self.__get_value(schema, obj, item)
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

    def set_default(self, value):
        self.__default = value
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
            if self.__null or self.__default is not None:
                return self.__default
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
                attrs[ATTR_NAME].append(name)
        for key, value in attrs.items():
            if isinstance(value, _Target):
                if isinstance(value, Field):
                    value.set_as_item(False)
                    value._name = key
                    if value._source is None:
                        value._source = key
                if key not in attrs[ATTR_NAME]:
                    attrs[ATTR_NAME].append(key)
        return type.__new__(mcs, name, bases, attrs)




class Field(_Target):

    def __init__(self, source=None, schema=None, to=None,
                 handler=None, choices=None, required=True, default=None):
        self._name = None
        self._source = source

        def initial_getter(obj):
            result = obj
            for _source in self._source.split('.'):
                if _source in ['self']:
                    continue
                if hasattr(result, _source):
                    result = getattr(result, _source)
                else:
                    result = result[_source]
            return result
        super().__init__(getter=initial_getter)
        self.set_as_item()
        self.set_default(default)
        if not required:
            self.set_null()

        if to is not None:
            self.to(to)
        if handler is not None:
            self.handle(handler)
        if schema is not None:
            self.as_(schema=schema)
        if choices is not None:
            self.map(choices, default=default)

    def iter(self, schema, condition=None):
        if isinstance(schema, set):
            _schema = {}
            for source in schema:
                if isinstance(source, _Target):
                    _schema[source._source] = source
                else:
                    _schema[source] = Field(source)
            schema = [_schema]
        elif isinstance(schema, (list, tuple)):
            _schema = []
            for source in schema:
                if isinstance(source, _Target):
                    _schema.append(source)
                elif isinstance(source, dict):
                    _schema.append(Field('self', schema=source))
                else:
                    _schema.append(Field(source))
            schema = _schema
        return super().iter(schema, condition=condition)


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

    def __init__(self, source=None):
        self._method_source = source
        self.__instance = None
        super().__init__('self', handler=self.__handler)

    def __handler(self, obj):
        method_name = self._method_source or'get_' + self._name
        method = getattr(self.__instance, method_name)
        return method(obj)

    def __get__(self, instance, owner):
        if owner is None:
            return self
        self.__instance = instance
        return self


class Reformer(metaclass=_ReformerMeta):
    _fields_ = ()

    def __init__(self, many=False, blank=True, content=None):
        self.content = content or {}
        self._blank = blank
        self._many = many

    @classmethod
    def transform(cls, _target, **kwargs):
        return cls(**kwargs)._transform(_target)

    def _transform(self, target):
        if self._many:
            self._many = False
            return [self._transform(item) for item in target]
        result = OrderedDict()
        for attr in self.__fields__:
            value = getattr(self, attr)._get(target)
            if value is None:
                if self._blank and self._blank is not True:
                    result[attr] = self._blank
                elif self._blank:
                    result[attr] = None
            else:
                result[attr] = value
        return result

    __call__ = _transform
