from flask import Flask
from marshmallow import Schema, fields, pre_load, validate
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from flask_security import UserMixin, RoleMixin, login_required, utils
from flask_login import current_user
from sqlalchemy import PrimaryKeyConstraint, UniqueConstraint, CheckConstraint
from enum import Enum
from passlib.apps import custom_app_context as pwd_context
from flask_admin.contrib import sqla
from wtforms import PasswordField

# https://www.sqlalchemy.org/
# https://github.com/zzzeek/sqlalchemy
db = SQLAlchemy()

# https://marshmallow.readthedocs.io/en/3.0/
ma = Marshmallow()

class Aircraft(db.Model):
    __tablename__ = 'aircrafts'
    
    aircraft = db.Column(db.String(15), unique=True, nullable=False, primary_key=True)
    seatcount = db.Column(db.Integer, nullable=False)

    def __init__(self, aircraft, seatcount):
        self.aircraft = aircraft
        self.seatcount = seatcount

class AircraftSchema(ma.Schema):
    #aircrafttype = fields.String(required=True, validate=validate.Length(1))
    aircraft = fields.Str()
    seatcount = fields.Integer()

class Seat(db.Model):
    __tablename__ = 'seats'

    # TODO: only one seat per ticket
    ticketnumber = db.Column(db.String(15), db.ForeignKey('tickets.number', ondelete='CASCADE'), nullable=False)
    ticket= db.relationship('Ticket', backref=db.backref('seats', lazy='dynamic' ))
    
    # Enum constraint seats labeled from A - H
    seatlabel = db.Column(db.Enum('A','B','C','D','E','F','G','H', name="seatlabelenum", create_type=False), nullable=False)
    
    # See above check constraint greater than 1
    seatrow = db.Column(db.Integer, nullable=False)
    
    flightnumber =  db.Column(db.String(10), db.ForeignKey('flights.number', ondelete='CASCADE'), nullable=False)
    flight = db.relationship('Flight', backref=db.backref('seats', lazy='dynamic' ))

    # Compound primary key of setlabel & seatrow:
    # https://docs.sqlalchemy.org/en/latest/core/constraints.html 
    # https://stackoverflow.com/questions/11168492/composite-keys-in-sqlalchemy
    __table_args__ = (
        PrimaryKeyConstraint(seatlabel, seatrow),
        UniqueConstraint(seatlabel, seatrow, name="check_seatlabelrow_unique"),
        CheckConstraint(seatrow>=1, name='check_seatrow_minimumone'),
        {})

    def __init__(self, ticketnumber, seatlabel, seatrow, flightnumber):
        self.ticketnumber = ticketnumber
        self.seatlabel = seatlabel
        self.seatrow = seatrow
        self.flightnumber = flightnumber

class SeatSchema(ma.Schema):
    ticketnumber = fields.String(required=True, validate=validate.Length(1))
    seatlabel = fields.String(required=True, validate=validate.Length(1))
    seatrow = fields.String(required=True, validate=validate.Length(1))
    flightnumber = fields.String(required=True, validate=validate.Length(1))

class Ticket(db.Model):
    __tablename__ = 'tickets'
    
    number = db.Column(db.String(10),unique=True, nullable=False, primary_key=True)
    
    flightnumber = db.Column(db.String(10), db.ForeignKey('flights.number', ondelete='CASCADE'), nullable=False)
    flight = db.relationship('Flight', backref=db.backref('tickets', lazy='dynamic' ))
    
    passengername = db.Column(db.String(25),nullable=False)
    
    passportnumber = db.Column(db.String(10),nullable=False)

    #    PrimaryKeyConstraint(number),
    #    {})

    def __init__(self, number, flightnumber, passengername, passportnumber):
        self.number = number
        self.flightnumber = flightnumber
        self.passengername = passengername
        self.passportnumber = passportnumber

class TicketSchema(ma.Schema):
    flightnumber = fields.String(required=True, validate=validate.Length(1))
    passenbername = fields.String(required=True)
    passenbernumber = fields.String(required=True)

class Flight(db.Model):
    __tablename__ = 'flights'

    number = db.Column(db.String(10), unique=True, nullable=False, primary_key=True)
    start = db.Column(db.String(3), nullable=False)
    end = db.Column(db.String(3), nullable=False)
    departure = db.Column(db.DateTime, nullable=False)
    aircrafttype  = db.Column(db.String(15), db.ForeignKey('aircrafts.aircraft', ondelete='CASCADE'), nullable=False)
    aircraft = db.relationship('Aircraft', backref=db.backref('flights', lazy='dynamic' ))

     # flights should have a combined key of departure / start / end / aircrafttype ? 
    __table_args__ = (
        UniqueConstraint(start, end, 'departure', name="check_deptstartend_unique"),
        {})

    def __init__(self, number, start, end, date):
        self.number = number
        self.start = start
        self.end = end
        self.date = date

class FlightSchema(ma.Schema):
    number = fields.String(required=True, validate=validate.Length(1))
    start = fields.String()
    end = fields.String()
    date = fields.DateTime()

# Create a table to support a many-to-many relationship between Users and Roles
roles_users = db.Table(
    'roles_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('role.id'))
)

class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

     # __str__ is required by Flask-Admin, so we can have human-readable values for the Role when editing a User.
    def __str__(self):
        return self.name

    # __hash__ is required to avoid the exception TypeError: unhashable type: 'Role' when saving a User
    def __hash__(self):
        return hash(self.name)

class RoleSchema(ma.Schema):
    id = fields.Int()
    name = fields.String(required=True, validate=validate.Length(1))
    description = fields.String()
   
class User(db.Model, UserMixin):
    __tablename__ = 'user'

    # the User has six fields: ID, email, password, active, confirmed_at and roles. The roles field represents a
    # many-to-many relationship using the roles_users table. Each user may have no role, one role, or multiple roles.
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship(
        'Role',
        secondary=roles_users,
        backref=db.backref('users', lazy='dynamic')
    )
    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

class UserSchema(ma.Schema):
    id = fields.Int()
    email = fields.String(required=True, validate=validate.Length(1))
    password = fields.String(required=True, validate=validate.Length(1))
    roles = fields.String() 

# Customized User model for SQL-Admin
class UserAdmin(sqla.ModelView):

    # Don't display the password on the list of Users
    column_exclude_list = list = ('password',)

    # Don't include the standard password field when creating or editing a User (but see below)
    form_excluded_columns = ('password',)

    # Automatically display human-readable names for the current and available Roles when creating or editing a User
    column_auto_select_related = True

    # Prevent administration of Users unless the currently logged-in user has the "admin" role
    def is_accessible(self):
        return current_user.has_role('admin')

    # On the form for creating or editing a User, don't display a field corresponding to the model's password field.
    # There are two reasons for this. First, we want to encrypt the password before storing in the database. Second,
    # we want to use a password field (with the input masked) rather than a regular text field.
    def scaffold_form(self):

        # Start with the standard form as provided by Flask-Admin. We've already told Flask-Admin to exclude the
        # password field from this form.
        form_class = super(UserAdmin, self).scaffold_form()

        # Add a password field, naming it "password2" and labeling it "New Password".
        form_class.password2 = PasswordField('New Password')
        return form_class

    # This callback executes when the user saves changes to a newly-created or edited User -- before the changes are
    # committed to the database.
    def on_model_change(self, form, model, is_created):

        # If the password field isn't blank...
        if len(model.password2):

            # ... then encrypt the new password prior to storing it in the database. If the password field is blank,
            # the existing password in the database will be retained.
            model.password = utils.encrypt_password(model.password2)


# Customized Role model for SQL-Admin
class RoleAdmin(sqla.ModelView):

    # Prevent administration of Roles unless the currently logged-in user has the "admin" role
    def is_accessible(self):
        return current_user.has_role('admin')