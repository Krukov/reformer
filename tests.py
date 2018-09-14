
from collections import OrderedDict

import pytest

from reformer import Reformer as R, item, link


def test_simple_value_field():
    target = {'name': 'test'}
    expect = {'test': 'test'}

    class Map(R):
        test = link.name

    assert Map.transform(target) == expect


def test_simple_int_field():
    target = {'value': 10, 'zero': 0}
    expect = {'test': 10, 'zero': 0}

    class Map(R):
        test = link.value
        zero = link.zero

    assert Map.transform(target) == expect


def test_simple_bool_field():
    target = {'true': True, 'false': False}
    expect = {'test_t': True, 'test_f': False}

    class Map(R):
        test_t = link.true
        test_f = link.false

    assert Map.transform(target) == expect


def test_simple_dict_field():
    target = {'dict': {'key': 10}}
    expect = {
        'test': {'key': 10},
        'value': 10,
    }

    class Map(R):
        test = link.dict
        value = link.dict.key

    assert Map.transform(target) == expect


def test_item_list_field():
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
        res = link.fields.iter_({
            item.type: item.N
        })
        res_ = link.fields.iter_([
            item.N
        ])
    assert Map.transform(target) == expect


def test_item_dict_field():
    target = {
        'fields': OrderedDict((('field_1', 'str'), ('field_2', 'kg'))),
    }
    expect = {
        'res': {'str': 'field_1', 'kg': 'field_2'},
        'res_': ['str', 'kg'],
    }

    class Map(R):
        res = link.fields.iter_({
            item.value: item.key
        })
        res_ = link.fields.iter_([
            item.value
        ])
    assert Map.transform(target) == expect


def test_item_field():
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
        res = link.fields.iter_([
            item.value.to_(int)
        ])
        res_ = link.fields.iter_([
            item.iter_({
                item.value: item.key
            })
        ])
    assert Map.transform(target) == expect


def test_simple_list_field():
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


def test_simple_as_dict_field():
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


def test_simple_as_list_field():
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
    target = type('TestObject', (), {'name': 'Test', 'params': {'new': True, 'value': 122}})
    expect = {
        'value': 1.22,
        'new': True,
        'name': 'Test',
    }

    class Map(R):
        value = link.params.value * 0.01
        new = link.params.new
        name = link.name

    assert Map.transform(target) == expect


def test_nullable_fields():
    target = {'name': 'test', 'gender': 'm', 'empty': None}
    expect = {'alias': 'test', 'test': None, 'empty': None}

    class Map(R):
        alias = link.name
        test = link.null_.test
        empty = link.empty

    assert Map.transform(target, blank=True) == expect
    assert Map.transform(target, blank=False) == {'alias': 'test'}


def test_exception_at_wrong_field():
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
        alias = link.type.choice_(['str', 'bool', 'int'])
        g = link.gender.choice_({'m': 'Man', 'w': 'Woman'})

    assert Map.transform(target) == expect


def test_in_fields():
    target = {'gender': 'w'}
    expect = {'woman': True, 'check': False}

    class Map(R):
        woman = link.gender.in_(['w', 'woman'])
        check = link.gender.contains_('t')

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
        one_two = link.one.compare_(link.two)
        one_is_one = link.one.compare_(1)
        one_more_two = link.one.compare_(link.two, gt)

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
