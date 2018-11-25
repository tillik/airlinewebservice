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
from resources.Checkin import CheckinResource

# Read db settings from environment for Azure deployment
database_uri = 'postgresql+psycopg2://{dbuser}:{dbpass}@{dbhost}/{dbname}'.format(
    dbuser=os.environ['DBUSER'],
    dbpass=os.environ['DBPASS'],
    dbhost=os.environ['DBHOST'],
    dbname=os.environ['DBNAME']
)

# Alternatively, could read from a settings file (config.py):
# app.config.from_object("config")

app = Flask(__name__)

app.config.update(
    SQLALCHEMY_DATABASE_URI=database_uri,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
)

db.init_app(app)

# Initialize database migration management
migrate = Migrate(app, db)
    

api_bp = Blueprint('api', __name__)
api = Api(api_bp)

app.register_blueprint(api_bp, url_prefix='/v1')

# Routes
api.add_resource(Welcome, '/welcome')
api.add_resource(FlightsResource, '/flights')
api.add_resource(FlightResource, '/flight/<string:flightnumber>')
api.add_resource(AircraftsResource, '/aircrafts')
api.add_resource(AircraftResource, '/aircraft/<string:aircraft>')
api.add_resource(TicketsResource, '/ticket')
api.add_resource(TicketResource, '/ticket/<string:ticketnumber>')
api.add_resource(SeatsResource, '/seat')
api.add_resource(SeatResource, '/seat/<string:seatcode>')
api.add_resource(UserResource, '/user')
api.add_resource(CheckinResource, '/checkin')

# Secret key for signing session cookies 
app.config['SECRET_KEY'] = 'coolairlinewebservice"'
# Set config values for Flask-Security (using PBKDF2 with salt)
app.config['SECURITY_PASSWORD_HASH'] = 'pbkdf2_sha512'
# Replace this with your own hmac salt
app.config['SECURITY_PASSWORD_SALT'] = '12345678123456781234567812345678123456781234567812345678123456781234567812345678123456781234567812345678123456781234567812345678'

# Flask-Security optionally sends email notification to users upon registration, password reset, etc.
# It uses Flask-Mail behind the scenes.
# Set mail-related config values.
# Replace this with your own "from" address
app.config['SECURITY_EMAIL_SENDER'] = 'admin@airws.com'

# for db tables see model.py

# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

# Executes before the first request is processed
@app.before_first_request
def before_first_request():

    try:
        # Create any database tables that don't exist yet
        db.create_all()

        # Create the Roles "admin" and "customeer" unless they already exist
        user_datastore.find_or_create_role(name='admin', description='Administrator')
        user_datastore.find_or_create_role(name='customer', description='Customer')

        # Create two Users for testing purposes (unless they already exist)
        # Use Flask-Security util-function to encrypt the password
        encrypted_password = utils.encrypt_password('p@ssw0rd')
        
        if not user_datastore.get_user('customer@airlinews.com'):
            user_datastore.create_user(email='customer@airlinews.com', password=encrypted_password)
        if not user_datastore.get_user('admin@airlinews.com'):
            user_datastore.create_user(email='admin@airlinews.com', password=encrypted_password)

        # Commit any database changes (User and Roles must exist before we can add a Role to the User)
        db.session.commit()

        # Give one User has the "customer" and another the "admin" role
        # (This will have no effect if the users already have these roles)
        user_datastore.add_role_to_user('customer@airlinews.com', 'customer')
        user_datastore.add_role_to_user('admin@airlinews.com', 'admin')
        db.session.commit()
    
    except Exception as e:
            db.session.rollback()
            print("Exception:" + str(e))
            return {"Error": 'Exception on before_first_request (the webservice will not be usable!): ' + str(e)}, 400

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
    session.clear()
    return redirect(url_for('index'))

# Set optional bootswatch theme for flask admin
app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'

# Initialize Flask-Admin
admin = Admin(app, template_mode='bootstrap3')

# Add Flask-Admin views for Users and Roles
admin.add_view(UserAdmin(User, db.session))
admin.add_view(RoleAdmin(Role, db.session))

# Logging to the console
root = logging.getLogger()
root.setLevel(logging.DEBUG)

if __name__ == "__main__":
    app.run()
