from bson import ObjectId
from model.map_data import Marker
from model.player_data import PlayerData


class UserDataController:

    @staticmethod
    def create_new_player(player_id, name, email, profile_pic, email_verified):
        player = PlayerData(
            id=player_id,
            name=name,
            email=email,
            profile_pic=profile_pic,
            email_verified=email_verified,
            map_data=UserDataController._init_map_data_(),
        )
        player.validate()
        PlayerData.save_player(player)
        return player

    @staticmethod
    def update_marker_type(current_user, old_type_name, new_type_name, color):
        markers_to_update = UserDataController.find_existing_markers_of_type_name(current_user, old_type_name)
        for marker in markers_to_update:
            marker.marker_type_name = new_type_name
            marker.color = color
        current_user.save()

    @staticmethod
    def find_existing_markers_of_type_name(current_user, name):
        return list(filter(lambda marker: marker.marker_type_name is name, current_user.map_data))

    @staticmethod
    def find_existing_marker_with_id(current_user, marker_id):
        for marker in current_user.map_data:
            if marker.id == ObjectId(marker_id):
                return marker
        return None

    @staticmethod
    def _init_map_data_():
        return [Marker(name='Lifepod', bearing=0, distance=0, depth=0, x=0, y=0,
                       marker_type_name="Lifepod", color="00FF00")]
