====================================================================
:ledger: Reformer
====================================================================

.. image:: https://travis-ci.org/Krukov/reformer.svg?branch=master
    :target: https://travis-ci.org/Krukov/reformer
.. image:: https://img.shields.io/coveralls/Krukov/reformer.svg
    :target: https://coveralls.io/r/Krukov/reformer

Simple and beautiful library for data formatting/convert/serialize
------------------------------------------------------------------


Installation
------------
::

    pip install reformer



How to use
----------
To define schema you need to create Reformer base class::

    from reformer import Reformer, link

    class Schema(Reformer):

        fullname = link.name.replace('_', '-')  + ' ' + link.surname


The main abstraction of the reformer is a `link`.  It represent access to the target object.
You can manipulate fields as you would do it with a real object, except a few operations that
have alias in `link` object. This methods are: `iter_`, `in_`, `contains_`, `to_`, `choice_`,
`call_`::

    from reformer import Reformer, link, item

    class Schema(Reformer):

        admin = link.username.in_(['admin', 'root'])
        welcome = link.username.choice_(
            {'admin': 'Hi bro', 'root': 'God?'},
            default='who are you?'
        )


`item` - another child abstraction as `link`, but for item of iterated object::

    from reformer import Reformer, link, item

    class Schema(Reformer):

        fullname = link.name + ' ' + link.surname
        posts_titles = link.posts.iter_([item.title])



*FUTURE*
========
 - errors
