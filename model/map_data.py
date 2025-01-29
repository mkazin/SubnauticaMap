from mongoengine import *


class Marker(EmbeddedDocument):
    bearing = IntField()
    distance = IntField()
    depth = IntField()
    name = StringField()

    marker_type_name = StringField(required=False, db_field="type")
    color = StringField(required=False)

    x = IntField()
    y = IntField()

    id = ObjectIdField()
