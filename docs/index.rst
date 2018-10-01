
Reformer
========

Reformer is a transformer/formatter/converter for objects.
Reformer use magic mapping for target fields that
looks declarative and simple::

   >>> from reformer import Reformer, link
   >>>
   >>> class UserInfo(Reformer):
   >>>    _fields_ = 'first_name', 'last_name'
   >>>
   >>>    fullname = link.sex.choice_({'m': 'Mr.', 'w': 'Mrs.'}) + ' ' + link.first_name + ' ' + link.last_name
   >>>    role = link.Role
   >>>    gender = link.sex.choice_({'m': 'Male', 'w': 'Female'})
   >>>    updated = link.created == link.updated
   >>>
   >>> target = {'first_name': 'John', 'last_name': 'Black', 'sex': 'm', 'created': now, 'updated':  now}

   >>> UserInfo.transform(target)
   {
       'first_name': 'John',
       'last_name': 'Black',
       'fullname' 'Mr. John Black',
       'gender': 'Male',
       'updated': False,
   }


Reformer is available on PyPI - to install it, just run::

    pip install reformer


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   why
   usage
   api


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
