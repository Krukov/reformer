========
Reformer
========

.. image:: https://travis-ci.org/Krukov/reformer.svg?branch=master
    :target: https://travis-ci.org/Krukov/reformer

Simple and beautiful library for data formatting/convert/serialize
------------------------------------------------------------------

::

    pip install reformer


Why
---
There are many great python libraries for validation, serialization and data formatting search as marshmallow, DRF  etc.
Usually they base on data validation.

Otherwise reformer design only for data formatting, and in a schema you need to define type of transformation and data source.

How to use
----------
To define schema you need to create Reformer base class::

    from reformer import Reformer, Field, MapField, MethodField

    class Schema(Reformer):
        _fields_ = ('name', 'surname')
        fullname = Field('name').replace('_', '-')  + ' ' + Field('surname')
        admin = Field('username').at(['admin', 'root'])
        welcome = MapField('username', {
            'admin': 'Hi bro',
            'root':  'God?'
        })
        posts_titles = Field('posts').iter(['title'])
        status = ('http://api.com/get_user_status/' + Field('id', to=str)).handle(requests.get)


    target = {
        'id': 353,
        'name': 'John',
        'surname': 'Black',
        'username': 'admin',
        'posts': [
            {'title': 'New', 'id': 10},
            {'title': 'My first post', 'id': 11},
        ]
    }

    print(Schema.transform(target))
    # OrderedDict([
    #    ('name', 'John'),
    #    ('surname', 'Black'),
    #    ('fullname', 'John Black'),
    #    ('admin', True),
    #    ('welcome', 'Hi bro'),
    #    ('posts_titles', ['New', 'My first post']),
    #    ('status', 'INIT'),
    # ])


*FUTURE*
========
 - errors
