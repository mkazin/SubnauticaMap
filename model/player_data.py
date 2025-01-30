from mongoengine import *
from .map_data import Marker
from flask_login import UserMixin


class PlayerData(Document, UserMixin):

    name = StringField()
    map_data = EmbeddedDocumentListField(Marker)
    google_id = StringField(db_field="_id", required=True, primary_key=True)
    email = StringField()
    email_verified = BooleanField()
    profile_pic = StringField()

    meta = {
        'collection': 'users'
    }

    """ Methods required by flask_login.LoginManager """
    def get_id(self):
        return str(self.google_id)
    """ End flask_login.LoginManager requirements """

    def __repr__(self):
        return ";".join([f"{field}={getattr(self, field)}" for field in self._fields])

    @staticmethod
    def load_player(player_id):
        player = PlayerData.objects.get(google_id=player_id)
        return player

    @staticmethod
    def save_player(player):

        if 'id' in player:
            print('PlayerData.save_player: Player already exists. Updating')
            player.save()
        else:
            print('PlayerData.save_player: Creating new player document')
            pd, _ = PlayerData.objects.create(player)
