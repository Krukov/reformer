Why reformer
============

There are many great python libraries for serialization and data formatting search as marshmallow, DRF  etc.
Usually they base on data validation.

Using reformer you don't need to define fields types, just define fields mapping with operating a reference
to target fields and use it as real object. For example you have the class and an instance::

   class Voter:
       def __init__(self, id, name, country, polls):
            self.id = id
            self.name = name
            self.country = country
            self.pools = pools

        def get_filtered_polls(self, ended):
            return [poll['name'] for poll in self.polls if poll['end'] < ended]

    voter = Voter(1, 'Mr. Lu', 'CN', [{'name': 'test', 'end': now()})

In you object representation you want to use `get_filtered_polls` method result and modify name on fly::

    class VoterReformer(Reformer):
        name = link.name.replace('Mr. ', '')
        polls = link.get_filtered_polls(datetime(2018, 02, 10, 23, 00, 00))

    or

    class VoterReformer(Reformer):
        name = link.name.replace('Mr. ', '')
        polls = link.pools.iter_([item.name], condition=item.end < ended)


`link` is like a reference to the `voter`
Simple? Is it?

Take a look at serializers with DRF::

    class PostSerializer(serializers.ModelSerializer):
        name = serializers.CharField(source='title')
        created = serializers.DateTimeField(format='%Y-%m-%dT%H:%M:%S.%f%z')
        updated = serializers.SerializerMethodField()

        class Meta:
            model = Post
            fields = 'name', 'created', 'updated'

        def get_updated(self, obj):
            return obj.created == obj.updated


    class AuthorSerializer(serializers.ModelSerializer):
        fullname = serializers.SerializerMethodField()
        posts = PostSerializer(many=True)

        class Meta:
            model = Author
            fields = 'name', 'fullname', 'posts'

        def get_fullname(self, obj):
            return obj.name + ' ' + obj.surname

And the same serialization with Reformer::

    class AuthorReformer(Reformer):
        _fields_ = 'name',

        fullname = Field('name') + ' ' + Field('usurname')
        posts = Field('posts').all().iter([
            Field('self', schema=OrderedDict((
                ('name', item.title),
                ('created', item.created.isoformat()),
                ('updated', item.created == item.updated)
            ))
        ])
