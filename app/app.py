import os,sys, logging

from flask import Flask, Blueprint, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_security import Security, SQLAlchemyUserDatastore, UserMixin, RoleMixin, login_required, utils
from flask_restful import Api
from flask_migrate import Migrate
from flask_admin import Admin
from flask_login import logout_user
from model import db, User, Role, UserAdmin, RoleAdmin
from resources.Welcome import Welcome
from resources.Flight import FlightResource, FlightsResource
from resources.Aircraft import AircraftResource, AircraftsResource
from resources.Ticket import TicketResource, TicketsResource
from resources.Seat import SeatResource, SeatsResource
from resources.User import UserResource


# read db settings from environment
database_uri = 'postgresql+psycopg2://{dbuser}:{dbpass}@{dbhost}/{dbname}'.format(
    dbuser=os.environ['DBUSER'],
    dbpass=os.environ['DBPASS'],
    dbhost=os.environ['DBHOST'],
    dbname=os.environ['DBNAME']
)

app = Flask(__name__)

# app.config.from_object("config")

app.config.update(
    SQLALCHEMY_DATABASE_URI=database_uri,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
)

db.init_app(app)

# initialize database migration management
migrate = Migrate(app, db)

#https://stackoverflow.com/questions/24420857/what-are-flask-blueprints-exactly
#from app import api_bp
    
# https://blog.miguelgrinberg.com/post/designing-a-restful-api-using-flask-restful/page/6
api_bp = Blueprint('api', __name__)
api = Api(api_bp)

app.register_blueprint(api_bp, url_prefix='/v1')

# Routes
api.add_resource(Welcome, '/Welcome')
api.add_resource(FlightsResource, '/flights')
api.add_resource(FlightResource, '/flight/<string:flightnumber>')
api.add_resource(AircraftsResource, '/aircrafts')
api.add_resource(AircraftResource, '/aircraft/<string:aircraft>')
api.add_resource(TicketsResource, '/ticket')
api.add_resource(TicketResource, '/ticket/<string:ticketnumber>')
api.add_resource(SeatsResource, '/seat')
api.add_resource(SeatResource, '/seat/<string:seatcode>')
api.add_resource(UserResource, '/user')



# Replace this with your own secret key
app.config['SECRET_KEY'] = 'super-secret'
# Set config values for Flask-Security.
# We're using PBKDF2 with salt.
app.config['SECURITY_PASSWORD_HASH'] = 'pbkdf2_sha512'
# Replace this with your own salt.
app.config['SECURITY_PASSWORD_SALT'] = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

# Flask-Security optionally sends email notification to users upon registration, password reset, etc.
# It uses Flask-Mail behind the scenes.
# Set mail-related config values.
# Replace this with your own "from" address
app.config['SECURITY_EMAIL_SENDER'] = 'admin@airws.com'

# for db tables see model.py

# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

# Executes before the first request is processed.
@app.before_first_request
def before_first_request():

    # Create any database tables that don't exist yet.
    db.create_all()

    # Create the Roles "admin" and "end-user" -- unless they already exist
    user_datastore.find_or_create_role(name='admin', description='Administrator')
    user_datastore.find_or_create_role(name='end-user', description='End user')

    # Create two Users for testing purposes -- unless they already exists.
    # In each case, use Flask-Security utility function to encrypt the password.
    encrypted_password = utils.encrypt_password('password')
    if not user_datastore.get_user('user@airws.com'):
        user_datastore.create_user(email='user@airws.com', password=encrypted_password)
    if not user_datastore.get_user('admin@airws.com'):
        user_datastore.create_user(email='admin@airws.com', password=encrypted_password)

    # Commit any database changes; the User and Roles must exist before we can add a Role to the User
    db.session.commit()

    # Give one User has the "end-user" role, while the other has the "admin" role. (This will have no effect if the
    # Users already have these Roles.) Again, commit any database changes.
    user_datastore.add_role_to_user('user@airws.com', 'end-user')
    user_datastore.add_role_to_user('admin@airws.com', 'admin')
    db.session.commit()

# Displays the home page.
@app.route('/')
# Users must be authenticated to view the home page, but they don't have to have any particular role.
# Flask-Security will display a login form if the user isn't already authenticated.
@login_required
def index():
    return render_template('index.html')

# Create a logout URL
@app.route("/logout")
#@login_required
def logout():
    logout_user()
    #return redirect(index.html)
    session.clear()
    return redirect(url_for('index'))

# set optional bootswatch theme for flask admin
app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'

# Initialize Flask-Admin
admin = Admin(app, template_mode='bootstrap3')

# Add Flask-Admin views for Users and Roles
admin.add_view(UserAdmin(User, db.session))
admin.add_view(RoleAdmin(Role, db.session))

# logging to the console
root = logging.getLogger()
root.setLevel(logging.DEBUG)

if __name__ == "__main__":
    #app.run(debug=True)
    app.run()

    # listen on all ips
    #app.run(
    #    host='0.0.0.0',
    #    port=int('8080'),
    #    debug=app.config['DEBUG']
    #)