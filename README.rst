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
There are many great python libraries for serialization and data formatting search as marshmallow, DRF  etc.
Usually they base on data validation.

Using reformer you don't need to define fields types, just define fields mapping with operating a reference
to target fields and use it as real object

How to use
----------
To define schema you need to create Reformer base class.
The main abstraction of the reformer is a `link`.  It represent access to the target object.
You can manipulate fields as you would do it with a real object, except a few operations that
have alias in `link` object. This methods are: `iter_`, `in_`, `contains_`, `to_`, `choice_`,
`call_`::

    from reformer import Reformer, link

    class Schema(Reformer):
        fullname = link.name.replace('_', '-')  + ' ' + link.surname
        admin = link.username.in_(['admin', 'root'])
        welcome = link.username.choice_(
            {'admin': 'Hi bro', 'root': 'God?'},
            default='who are you?'
        )

    target = {
        'name': 'John',
        'surname': 'Black',
        'username': 'admin',
    }

    print(Schema.transform(target))
    # OrderedDict([('fullname', 'John Black'), ('admin', True), ('welcome', 'Hi bro')])


`item` - another child abstraction as `link`, but for item of iterated object::

    from reformer import Reformer, link, item

    class Schema(Reformer):
        posts_titles = link.posts.iter_([item.title])


    class Author:
        @property
        def posts(self):
            return [
                {'title': 'New', 'id': 10},
                {'title': 'My first post', 'id': 11},
            ]


    print(Schema.transform(Author()))
    # OrderedDict([('posts_titles', ['New', 'My first post'])])


*FUTURE*
========
 - errors
