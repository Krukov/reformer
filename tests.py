
from collections import OrderedDict

import pytest

from reformer import Reformer as R, _Item, _Link, Field, MethodField

link = _Link()
item = _Item()


def test_simple_value_link():
    target = {'name': 'test'}
    expect = {'test': 'test'}

    class Map(R):
        test = link.name

    assert Map.transform(target) == expect


def test_simple_int_link():
    target = {'value': 10, 'zero': 0}
    expect = {'test': 10, 'zero': 0}

    class Map(R):
        test = link.value
        zero = link.zero

    assert Map.transform(target) == expect


def test_simple_bool_link():
    target = {'true': True, 'false': False}
    expect = {'test_t': True, 'test_f': False}

    class Map(R):
        test_t = link.true
        test_f = link.false

    assert Map.transform(target) == expect


def test_simple_dict_link():
    target = {'dict': {'key': 10}}
    expect = {
        'test': {'key': 10},
        'value': 10,
    }

    class Map(R):
        test = link.dict
        value = link.dict.key

    assert Map.transform(target) == expect


def test_to_type():
    target = {'value': '10', 'zero': 0}
    expect = {'value': 10, 'zero': '0'}

    class Map(R):
        value = link.value.to_int()
        zero = link.zero.to_str()

    assert Map.transform(target) == expect


def test_item_list_link():
    target = {
        'fields': [
            {'type': 'str', 'N': 'kg'},
            {'type': 'int', 'N': '1'},
        ]
    }
    expect = {
        'res': {
            'str': 'kg',
            'int': '1'
        },
        'res_': ['kg', '1'],
    }

    class Map(R):
        res = link.fields.iter({
            item.type: item.N
        })
        res_ = link.fields.iter([
            item.N
        ])
    assert Map.transform(target) == expect


def test_item_dict_link():
    target = {
        'fields': OrderedDict((('field_1', 'str'), ('field_2', 'kg'))),
    }
    expect = {
        'res': {'str': 'field_1', 'kg': 'field_2'},
        'res_': ['str', 'kg'],
    }

    class Map(R):
        res = link.fields.iter({
            item.value: item.key
        })
        res_ = link.fields.iter([
            item.value
        ])
    assert Map.transform(target) == expect


def test_item_link():
    target = {
        'fields': [
            {'type': 'int', 'value': '10'},
            {'type': 'int', 'value': '1'},
        ]
    }
    expect = {
        'res': [10, 1],
        'res_': [
            {'int': 'type', '10': 'value'},
            {'int': 'type', '1': 'value'}
        ],
    }

    class Map(R):
        res = link.fields.iter([
            item.value.to(int)
        ])
        res_ = link.fields.iter([
            item.iter({
                item.value: item.key
            })
        ])
    assert Map.transform(target) == expect


def test_iter_link():
    target = {
        'fields': [
            {'type': 'int', 'val': '10'},
            {'type': 'int', 'val': '1'},
        ]
    }
    expect = {
        'res': [
            {'type': 'int', 'check': True},
            {'type': 'int', 'check': False}
        ],
    }

    class Map(R):
        res = link.fields.iter([
            item.as_({
                'type': item.type,
                'check': item.val.to(int) > 5,
            })
        ])
    assert Map.transform(target) == expect


def test_iter_field_with_filter():
    target = {
        'fields': [
            {'type': 'int', 'val': '10'},
            {'type': 'int', 'val': '1'},
            {'type': 'str', 'val': 'ilove'},
        ]
    }
    expect = {
        'res': [
            {'type': 'int', 'val': 10},
            {'type': 'int', 'val': 1}
        ],
    }

    class Map(R):
        res = link.fields.iter([
            item.as_({
                'type': item.type,
                'val': item.val.to(int),
            })
        ], item.type == 'int')
    assert Map.transform(target) == expect


def test_simple_list_link():
    target = {'list': ['Hello', 'world', '!!!']}
    expect = {
        'all': ['Hello', 'world', '!!!'],
        'res': 'Hello',
        'last': '!!!',
    }

    class Map(R):
        all = link.list
        res = link.list[0]
        last = link.list[-1]

    assert Map.transform(target) == expect


def test_simple_value_field_mul():
    target = {'name': 'test', 'val': 10}
    expect = {'test': 'testtesttest', 'val': 20}

    class Map(R):
        test = link.name * 3
        val = link.val * 2

    assert Map.transform(target) == expect


def test_simple_value_field_add():
    target = {'name': 'test', 'val': 10}
    expect = {'test': '* test_10', 'val': 15}

    class Map(R):
        test = '* ' + link.name + '_' + link.val.to_str()
        val = 5 + link.val

    assert Map.transform(target) == expect


def test_simple_value_field_methods():
    target = {'name': 'test', 'val': 100, 'list': [1, 2, 3, 2]}
    expect = {'name': '*es*', 'val': 7, 'i': 2}

    class Map(R):
        name = link.name.replace('t', '*')
        val = link.val.bit_length()
        i = link.list.count(2)

    assert Map.transform(target) == expect


def test_simple_value_field_call():
    target = {'name': 'test', 'val': 100, 'list': [1, 2, 3, 2]}
    expect = {'name': 'tset', 'count': 3}

    class Map(R):
        name = link.name.call(lambda name: ''.join(reversed(name)))
        count = link.call(lambda obj: len(obj))

    assert Map.transform(target) == expect


def test_simple_as_dict_link():
    target = {'key1': 'val1', 'key2': 'val2'}
    expect = {
        'test': {'key1': 'val2', 'key2': 'val1'},
    }

    class Map(R):
        test = link.as_({
            'key2': link.key1,
            'key1': link.key2,
        })

    assert Map.transform(target) == expect


def test_simple_as_list_link():
    target = {'key1': 'val1', 'key2': 'val2'}
    expect = {
        'test': ['val1', 'val2'],
    }

    class Map(R):
        test = link.as_([
            link.key1, link.key2,
        ])

    assert Map.transform(target) == expect


def test_simple_with_many():
    targets = [
        {'name': 'test', 'gender': 'm'},
        {'name': 'second', 'gender': 'f'},
    ]
    expect = [
        {'alias': 'test M'},
        {'alias': 'second F'},
    ]

    class Map(R):
        alias = link.name + ' ' + link.gender.upper()

    assert Map.transform(targets, many=True) == expect


def test_simple_with_object():
    target = type('TestObject', (), {
        'name': 'Test',
        'params': {'new': True, 'value': 122},
        'get_reversed_name': lambda x: ''.join(reversed(x.name))})()

    expect = {
        'value': 1.22,
        'new': True,
        'name': 'Test',
        'reversed_name': 'tseT',
    }

    class Map(R):
        value = link.params.value * 0.01
        new = link.params.new
        name = link.name
        reversed_name = link.get_reversed_name()

    assert Map.transform(target) == expect


def test_nullable_fields():
    target = {'name': 'test', 'gender': 'm', 'empty': None}
    expect = {'alias': 'test', 'test': None, 'empty': None}

    class Map(R):
        alias = link.name
        test = link.test.set_null()
        empty = link.empty

    assert Map.transform(target, blank=True) == expect
    assert Map.transform(target, blank=False) == {'alias': 'test'}


def test_exception_at_wrong_link():
    target = {'name': 'test', 'gender': 'm', 'empty': None}

    class Map(R):
        test = link.test
        empty = link.empty

    with pytest.raises(KeyError):
        Map.transform(target)


def test_choice_fields():
    target = {'type': 0, 'gender': 'w', }
    expect = {'alias': 'str', 'g': 'Woman'}

    class Map(R):
        alias = link.type.map(['str', 'bool', 'int'])
        g = link.gender.map({'m': 'Man', 'w': 'Woman'})

    assert Map.transform(target) == expect


def test_in_fields():
    target = {'gender': 'w'}
    expect = {'woman': True, 'check': False}

    class Map(R):
        woman = link.gender.at(['w', 'woman'])
        check = link.gender.contains('t')

    assert Map.transform(target) == expect


def test_slice_fields():
    target = {'list': list(range(5)), 'text': 'my test here'}
    expect = {'list': [3, 4], 'text': 'here'}

    class Map(R):
        list = link.list[3:5]
        text = link.text[-4:]

    assert Map.transform(target) == expect


def test_compare():
    from operator import gt
    target = {'one': 1, 'two': 2}
    expect = {'one_two': False, 'one_is_one': True, 'one_more_two': False}

    class Map(R):
        one_two = link.one.compare(link.two)
        one_is_one = link.one.compare(1)
        one_more_two = link.one.compare(link.two, gt)

    assert Map.transform(target) == expect


def test_compare_2():
    target = {'one': 1, 'two': 2}
    expect = {'one_two': False, 'one_is_one': True, 'one_more_two': False}

    class Map(R):
        one_two = link.one == link.two
        one_is_one = link.one == 1
        one_more_two = link.one >= link.two

    assert Map.transform(target) == expect


def test_default_fields():
    target = {'a': 1, 'b': 2, 'c': 'c'}
    expect = {'a': 1, 'c': 'c', 'o': 2}

    class Map(R):
        _fields_ = 'a', 'c'
        o = link.b

    assert Map.transform(target) == expect


def test_simple_field():
    target = {'name': 'hello'}
    expect = {'test': 'hello'}

    class Map(R):
        test = Field('name')

    assert Map.transform(target) == expect


def test_auto_source_field():
    target = {'name': 'hello'}
    expect = {'name': 'hello'}

    class Map(R):
        name = Field()

    assert Map.transform(target) == expect


def test_self_field():
    target = {'name': 'hello'}
    expect = {'test': target}

    class Map(R):
        test = Field('self')

    assert Map.transform(target) == expect


def test_simple_with_method_field():
    target = {'name': 'hello'}
    expect = {'test': 'hel', 'count': 2}

    class Map(R):
        test = Field('name')[:3]
        count = Field('name').count('l')

    assert Map.transform(target) == expect


def test_dot_sep_field():
    target = {'name': {'first': 'Jack', 'last': 'Brown'}}
    expect = {'last': 'Brown', 'first': 'Jack'}

    class Map(R):
        last = Field('name').last
        first = Field('name.first')

    assert Map.transform(target) == expect


def test_to_type_field():
    target = {'value': '10', 'zero': 0}
    expect = {'value': 10, 'zero': '0'}

    class Map(R):
        value = Field().to_int()
        zero = Field('zero', to=str)

    assert Map.transform(target) == expect


def test_field_mul():
    target = {'name': 'test', 'val': 10}
    expect = {'test': 'testtesttest', 'val': 20}

    class Map(R):
        test = Field('name') * 3
        val = Field() * 2

    assert Map.transform(target) == expect


def test_field_con():
    target = {'val': 10}
    expect = {'res': ['api.com', 'user', '10']}

    class Map(R):
        res = ('api.com/user/' + Field('val', to=str)).split('/')

    assert Map.transform(target) == expect


def test_fields_compare():
    target = {'one': 1, 'two': 2}
    expect = {'one_two': False, 'one_is_one': True, 'one_more_two': False}

    class Map(R):
        one_two = Field('one') == Field('two')
        one_is_one = Field('one') == 1
        one_more_two = Field('one') >= Field('two')

    assert Map.transform(target) == expect


def test_fields_choices():
    target = {'one': 1, 'two': 2}
    expect = {'one_choices': 'one'}

    class Map(R):
        one_choices = Field('one', choices={1: 'one', 2: 'two'})

    assert Map.transform(target) == expect


def test_field_call():
    target = {'name': 'test', 'val': 100, 'list': [1, 2, 3, 2]}
    expect = {'name': 'tset', 'count': 3}

    class Map(R):
        name = Field('name').handle(lambda name: ''.join(reversed(name)))
        count = Field('self', handler=lambda obj: len(obj))

    assert Map.transform(target) == expect


def test_field_as_dict():
    target = {'key1': 'val1', 'key2': 'val2'}
    expect = {
        'test': {'key1': 'val2', 'key2': 'val1'},
    }

    class Map(R):
        test = Field('self', schema={
            'key2': Field('key1'),
            'key1': Field('key2'),
        })

    assert Map.transform(target) == expect


def test_field_as_dict_item():
    target = {'key': {'key2': 'val2', 'key': 'name'}}
    expect = {
        'test': {'name': 'val2'},
    }

    class Map(R):
        test = Field('key', schema={
            Field('key'): Field('key2'),
        })

    assert Map.transform(target) == expect


def test_field_item_link():
    target = {
        'fields': [
            {'type': 'int', 'value': '10'},
            {'type': 'int', 'value': '1'},
        ]
    }
    expect = {
        'res': [
            {'int': 'type', '10': 'value'},
            {'int': 'type', '1': 'value'}
        ],
    }

    class Map(R):
        res = Field('fields').iter([{
            Field('type'): 'type',
            Field('value'): 'value',
        }])
    assert Map.transform(target) == expect


def test_field_item_link2():
    target = {
        'fields': [
            {'type': 'int', 'value': '10'},
            {'type': 'int', 'value': '1'},
        ]
    }
    expect = {
        'res': [
            {'value': 10},
            {'value': 1},
        ],
    }

    class Map(R):
        res = Field('fields').iter([{
            'value': Field('value').to(Field('type')),
        }])
    assert Map.transform(target) == expect


def test_field_item_link3():
    target = {
        'fields': [
            {'type': 'int', 'value': '10'},
            {'type': 'int', 'value': '1'},
        ]
    }
    expect = {'res': ['10', '1']}

    class Map(R):
        res = Field('fields').iter(['value'])

    assert Map.transform(target) == expect


def test_field_item_link4():
    target = {
        'fields': [
            {'type': 'int', 'value': '10.1', 'name': 'x'},
            {'type': 'int', 'value': '1', 'name': 'z'},
        ]
    }
    expect = {
        'res': [
            {'value': '10.1', 'name': 'x'},
            {'value': '1', 'name': 'z'},
        ],
        'res2': [
            {'value': 10.1, 'type': 'int'},
            {'value': 1.0, 'type': 'int'},
        ]
    }

    class Map(R):
        res = Field('fields').iter({'value', 'name'})
        res2 = Field('fields').iter({Field('value', to=float), 'type'})

    assert Map.transform(target) == expect


def test_method_field():
    target = {'type': 'int', 'value': '1'}
    expect = {'hash': 'int1'}

    class Map(R):
        hash = MethodField()

        def get_hash(self, obj):
            return ''.join([obj['type'], obj['value']])

    assert Map.transform(target)['hash'] == expect['hash']


def test_field_sub_map():
    target = {'key': {'key2': 'val2', 'key': 'name'}}
    expect = {
        'test': {'name': 'val2'},
    }

    class SubMap(R):
        name = Field('key2')

    class Map(R):
        test = Field('key').as_(SubMap())

    assert Map.transform(target) == expect
