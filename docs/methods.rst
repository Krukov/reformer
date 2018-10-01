
Link Methods
=============

There are a few methods of `link` object (`item` too), that help to achieve the desired conversion.

* ``to_(type)``, convert linked field to given type::

    class Map(Reformer):
        value = link.value.to_(float)

    print(Map.transform({'value': '1.008'})) # {'value': 1.008}

* ``to_int()``, shortcut for to_(int).
* ``to_str()``, shortcut for to_(str).
* ``as_(schema)``, like to_ but for data structures::

    class Map(Reformer):
        user = link['user1'].as_({item.name: item.age})
        names = link['user1'].as_((item.name, ))

    print(Map.transform({'user1': {'name': 'John', 'age': 10}}))  # {'user'{'John': 10}, 'names': ['John']}

* ``iter_(schema, condition=None)``, iterates on a linked object, condition used for filter items::


* ``in_(container)``, checks that linked value in container.
* ``contains_(item)``, check that linked value contain `item`
* ``choice_(choices, default=None)``, returns the corresponding value from choices for linked value.

* ``call_(func)``, calling givven function with linked value as argument.


Markers:
* ``null_``, marks that if the target of the link is missing, then return None (do not fall with error).
