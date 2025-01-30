import unittest
from bson.objectid import ObjectId
from mongoengine import connect
from controller.user_data import UserDataController
from model.map_data import Marker
from mongomock import MongoClient

class UserDataControllerTestCase(unittest.TestCase):

    db = None
    player_singleton = None

    @classmethod
    def setUpClass(cls):
        UserDataControllerTestCase.db = connect('testdb', host="localhost", port=27017, mongo_client_class=MongoClient, uuidRepresentation="standard")
        UserDataControllerTestCase.db.drop_database('testdb')
        UserDataControllerTestCase._create_player()

    @classmethod
    def tearDownClass(cls):
        UserDataControllerTestCase.db.drop_database('testdb')
        UserDataControllerTestCase.db.close()

    def setUp(self):
        self.player = UserDataControllerTestCase.player_singleton
        self.player.map_data = []
        self.player.save()

    def test_create_new_player(self):
        created_player = UserDataController.create_new_player(
            player_id='player id',
            name='name',
            email='email',
            profile_pic='picture',
            email_verified=False,
        )

        self.assertIsNotNone(created_player)
        self.assertEqual(1, len(created_player.map_data))

    def test_update_marker_type_when_marker_existed(self):
        old_type_name = 'Old Type Name'
        self._create_marker(name='Test Marker', marker_type_name=old_type_name, color='Old Color')

        new_type_name = 'New Type Name'
        new_color = 'New Color'
        UserDataController.update_marker_type(self.player, old_type_name, new_type_name, new_color)

        self._force_db_map_data_reload()
        self.assertEqual(1, len(self.player.map_data))
        self.assertEqual(new_type_name, self.player.map_data[0].marker_type_name)
        self.assertEqual(new_color, self.player.map_data[0].color)

    def test_update_marker_type_when_multiple_markers_exist(self):
        old_type_name = 'Old Type Name'
        self._create_marker(bearing=100, distance=456, depth=123, x=5, y=5,
                            name='First Marker', marker_type_name=old_type_name, color='Old Color')
        self._create_marker(bearing=100, distance=456, depth=123, x=5, y=5,
                            name='Second Marker', marker_type_name=old_type_name, color='Old Color')

        new_type_name = 'New Type Name'
        new_color = 'New Color'
        UserDataController.update_marker_type(self.player, old_type_name, new_type_name, new_color)

        self._force_db_map_data_reload()
        self.assertEqual(2, len(self.player.map_data))

        for marker in self.player.map_data:
            self.assertEqual(new_type_name, marker.marker_type_name)
            self.assertEqual(new_color, marker.color)

    def test_update_marker_type_when_other_marker_types_should_be_ignored(self):
        type_name_to_replace = 'Old Type Name'
        type_name_which_should_not_be_changed = 'Very different from the old type name'
        self._create_marker(name='Test Marker',
                            marker_type_name=type_name_which_should_not_be_changed,
                            color='A Completely Different Color')

        new_type_name = 'New Type Name'
        new_color = 'New Color'
        UserDataController.update_marker_type(self.player, type_name_to_replace, new_type_name, new_color)

        # Force a reload from the database, should find our one marker
        self._force_db_map_data_reload()
        self.assertEqual(1, len(self.player.map_data))
        self.assertEqual(type_name_which_should_not_be_changed, self.player.map_data[0].marker_type_name)

    def _create_marker(self,  # bearing, distance, depth, x, y, name, marker_type_name, color, marker_id=None):
                       bearing=100, distance=456, depth=123, x=5, y=5,
                       marker_id=ObjectId(), name='Marker name',
                       marker_type_name='Marker Type Name', color='Marker Type Color'):
        if not marker_id:
            marker_id = ObjectId()

        new_marker = Marker(
            id=marker_id, bearing=bearing, distance=distance, depth=depth, x=x, y=y,
            name=name, marker_type_name=marker_type_name, color=color)
        if not hasattr(self.player, 'map_data'):
            self.player.map_data = []

        self.player.map_data.append(new_marker)
        self.player.save(cascade=True)

    def test_find_existing_markers_of_type_name_happy_path(self):
        marker_type_name_to_find = 'Old Type Name'
        self._create_marker(name='First Marker', marker_type_name=marker_type_name_to_find, color='Color')
        self._create_marker(name='Second Marker', marker_type_name='Different marker type', color='Color')
        self._create_marker(name='Third Marker', marker_type_name=marker_type_name_to_find, color='Color')

        found_markers = UserDataController.find_existing_markers_of_type_name(self.player, marker_type_name_to_find)

        self.assertEqual(2, len(found_markers))
        found_marker_names = set(list(map(lambda marker: marker.name, found_markers)))
        self.assertSetEqual(set(['First Marker', 'Third Marker']), found_marker_names)

    def test_find_existing_markers_of_type_name_when_missing(self):
        marker_type_name_to_find = 'Type Name'
        self._create_marker(bearing=100, distance=456, depth=123, x=5, y=5,
                            name='Second Marker', marker_type_name='Different marker type', color='Color')

        found_markers = UserDataController.find_existing_markers_of_type_name(self.player, marker_type_name_to_find)
        self.assertEqual(0, len(found_markers))

    def test_find_existing_marker_with_id_happy_path(self):
        marker_id_to_find = ObjectId()
        self._create_marker(marker_id=marker_id_to_find, name='Marker Name')

        found_marker = UserDataController.find_existing_marker_with_id(self.player, marker_id_to_find)
        self.assertEqual(marker_id_to_find, found_marker.id)

    def test_find_existing_marker_with_id_when_missing(self):
        marker_id_to_find = '000000000000000000000000'
        self._create_marker(marker_id=ObjectId('61421fc22222fd8ed85283ac'), name='Marker Name')

        found_marker = UserDataController.find_existing_marker_with_id(self.player, marker_id_to_find)
        self.assertIsNone(found_marker)

    @staticmethod
    def _create_player():
        player = UserDataController.create_new_player(
            player_id='test_id',
            name='Test Player',
            email='test@example.com',
            profile_pic='/static/test_user.svg',
            email_verified=True,
        )
        UserDataControllerTestCase.player_singleton = player

    def _force_db_map_data_reload(self):
        self.player.map_data = []
        self.assertEqual(0, len(self.player.map_data))
        self.player.reload()


if __name__ == '__main__':
    unittest.main()
