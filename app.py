import os
import pathlib

import certifi
import requests
from mongoengine import DoesNotExist
from pip._vendor import cachecontrol
from flask import Flask, request, jsonify, render_template, abort, url_for, redirect, session, flash
from flask_mongoengine import MongoEngine
from flask_login import LoginManager, current_user, login_user, login_required, logout_user
from oauthlib.oauth2 import WebApplicationClient
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
import google.auth.transport.requests

import subnautical
from model.map_data import Marker
from model.player_data import PlayerData
from controller.charting import Charting
from controller.user_data import UserDataController


# To run this from PyCharm's Python Console prompt (which lets you hit ^C):
# > runfile('D:/Work/SubnauticaMap/app.py', wdir='D:/Work/SubnauticaMap')


app = Flask(__name__)
app.config['SERVER_NAME'] = f"{subnautical.app_domain}:{subnautical.app_port}"
app.config['SESSION_COOKIE_DOMAIN'] = subnautical.app_domain

app.static_folder = subnautical.app_config['ROOT_PATH'] + '/static'
app.template_folder = subnautical.app_config['ROOT_PATH'].split('controller')[0] + '/view/templates'
app.config.from_object('subnautical.config')
app.config['MONGODB_SETTINGS'] = subnautical.config
app.config['MONGODB_SETTINGS']['connectTimeoutMS'] = 200
app.config['MONGODB_SETTINGS']['tlsCAFile'] = certifi.where()

db = MongoEngine(app, app.config)

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "config", "client_secrets.json")


login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.init_app(app)
app.secret_key = subnautical.GOOGLE_CLIENT_SECRET
client = WebApplicationClient(subnautical.GOOGLE_CLIENT_ID)



from bson.objectid import ObjectId
def populate_marker_id(user):
    user_changed = False
    for marker in user.map_data:
        if not hasattr(marker, 'id') or marker.id is None:
            marker.id = ObjectId()
            user_changed = True
            print(f"{marker.name} assigned ObjectId: {marker.id}")

    return user_changed

def upgrade_all_users():
    print(f"Upgrading users data...")
    for user in PlayerData.objects:
        print(f"Upgrading user: {user.name}")
        if populate_marker_id(user):
            print(f"-- Saving upgraded record for user {user.name}")
            user.save(cascade=True)
    print(f"Upgrading complete.")

upgrade_all_users()


@app.route('/')
def hello_world():
    if current_user.is_authenticated and not current_user.is_anonymous:
        return render_template('map.html')
    else:
        print('User not logged in. Redirecting to /login')
        logout_user()
        session.clear()
        return redirect('/login')  # render_template('login.html')


@app.route('/marker', methods=['PUT', 'POST'])
@login_required
def add_marker():
    print("add_marker called")
    try:
        heading = float(request.form['heading'])
        distance = int(request.form['distance'])
        depth = int(request.form['depth'])
        marker_name = request.form['name']
        marker_id = request.form.get('marker_id', None)

        marker_type_name = request.form['new_type'] or request.form['marker_type']
        marker_color = request.form.get('color', '555555')

        x, y = Charting.get_cartesean_coords(distance, depth, heading)

        print(f"Searched for marker with id {marker_id}")
        existing_marker = UserDataController.find_existing_marker_with_id(current_user, marker_id)
        if existing_marker:
            print('Found existing marker: ' + existing_marker.name)

            existing_marker.bearing = heading
            existing_marker.distance = distance
            existing_marker.depth = depth
            existing_marker.x = x
            existing_marker.y = y
            existing_marker.name = marker_name

            # old_type_name = existing_marker.marker_type_name
            # old_type_color = existing_marker.color
            existing_marker.marker_type_name = marker_type_name
            current_user.save(cascade=True)

            # This is a rename functionality that does not have a UI yet (above too)
            # if old_type_name == marker_type_name:
            #     UserDataController.update_marker_type(
            #         current_user, old_type_name, marker_type_name, marker_color)
            #     flash("Marker Type updated")
        else:
            print('Adding new marker: ' + marker_name)
            new_marker = Marker(
                bearing=heading, distance=distance, depth=depth, x=x, y=y,
                name=marker_name, marker_type_name=marker_type_name, color=marker_color)
            current_user.map_data.append(new_marker)
            current_user.save(cascade=True)
            flash("Marker added")

    except KeyError:
        abort(400, description="Missing value - please make sure to fill in all fields")
    except ValueError:
        print('Bad form data in request: ', request.form)
        abort(400, description="Bad value - please use integers in all numeric fields")

    return redirect('/map')


@app.route(rule='/mapdata', methods=['GET'])
@login_required
def output_map_data():
    return jsonify(Charting.get_plot_data(current_user.map_data))


# When querying non-map user data, use partial querying:
# https://docs.mongoengine.org/guide/querying.html#retrieving-a-subset-of-fields
# Film(title='The Shawshank Redemption', year=1994, rating=5).save()
# f = Film.objects.only('title').first()

@app.route(rule='/map', methods=['GET'])
@login_required
def generate_map():
    return render_template('map.html', markers=Charting.get_plot_data(current_user.map_data))


@app.route('/login', methods=['GET', 'POST'])
def login():
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)

    # if current_user.is_authenticated:
    #     return redirect(url_for('index'))
    # form = LoginForm()
    # if form.validate_on_submit():
    #     user = PlayerData.load_player(form.username.data)
    #     if user is None or not user.check_password(form.password.data):
    #         flash('Invalid username or password')
    #         return redirect(url_for('login'))
    #     login_user(user, remember=form.remember_me.data)
    #     return redirect(url_for('index'))
    # return render_template('login.html', title='Sign In', form=form)


@app.route('/callback')
def callback():
    flow.fetch_token(authorization_response=request.url)

    if not session["state"] == request.args["state"]:
        abort(500, "State does not match!  Session: " + session["state"] + " , Request: " + request.args["state"])

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=subnautical.GOOGLE_CLIENT_ID
    )

    player_id = id_info['sub']

    try:
        player = load_player_from_db(player_id)
        print(f"Callback: trying to load {player_id} resulted in: ", repr(player))
        login_user(player, force=True)
    except (DoesNotExist, AttributeError) as e:
        print(f"Callback: trying to load {player_id} threw exception. Creating new document for: {id_info['name']}", e)

        player = UserDataController.create_new_player(
            player_id=player_id,
            name=id_info['name'],
            email=id_info['email'],
            profile_pic=id_info['picture'],
            email_verified=id_info['email_verified'],
        )

        login_user(player, force=True)

    return redirect('/')


@login_required
@app.route('/protected_area')
def protected_area():
    return f"Hello {session}! <br/> <a href='/logout'><button>Logout</button></a>"


@app.route('/logout')
def logout():
    logout_user()
    session.clear()
    return redirect("/")


@login_manager.user_loader
def load_player_from_db(player_id):
    player = None
    try:
        player = PlayerData.load_player(player_id)
    except DoesNotExist:
        pass

    return player


with app.app_context():
    flow = Flow.from_client_secrets_file(
        client_secrets_file=client_secrets_file,
        scopes=["https://www.googleapis.com/auth/userinfo.profile",
                "https://www.googleapis.com/auth/userinfo.email",
                "openid"],
        redirect_uri=url_for('callback'),
        )


if __name__ == '__main__':
    print(f"Starting app on host={subnautical.app_host}, port={subnautical.app_port}")
    app.run(host=subnautical.app_host, port=subnautical.app_port, debug=False)
