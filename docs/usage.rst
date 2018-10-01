How to use
==========

To define schema you need to create Reformer base class.
The main abstraction of the reformer is a `link`.  It represent access to the target object.
You can manipulate fields as you would do it with a real object, except a few operations that
have alias in `link` object. This methods are: `iter_`, `in_`, `contains_`, `to_`, `choice_`,
`call_`, `as_`::

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

The class method ``transform(target, many=False, blank=True)`` produces the described conversions for target and
return OrderedDict (or list of them for many=True) with result. If many=True transform expect array of base targets.
if blank=False keys with the `None` value will be remove.