import random, string, logging
from flask import Flask
from marshmallow import Schema, fields, pre_load, post_load, post_dump, validate
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from flask_security import UserMixin, RoleMixin, login_required, utils
from flask_login import current_user
from sqlalchemy import Table, Column, PrimaryKeyConstraint, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from enum import Enum
from passlib.apps import custom_app_context as pwd_context
from flask_admin.contrib import sqla
from datetime import datetime
from wtforms import PasswordField


db = SQLAlchemy()
ma = Marshmallow()

class Aircraft(db.Model):
    __tablename__ = 'aircrafts'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    aircraft = db.Column(db.String(15), unique=True, nullable=False)
    seatcount = db.Column(db.Integer, nullable=False)

    def __init__(self, aircraft, seatcount):
        self.aircraft = aircraft
        self.seatcount = seatcount

# schema for serialization / serialization of aircrafts
class AircraftSchema(ma.Schema):
    aircraft = fields.Str()
    seatcount = fields.Integer()

class Seat(db.Model):
    __tablename__ = 'seats'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # define foreign key for one:many relationship parent(Flight):child(Seat) 
    parent_id = Column(db.Integer, db.ForeignKey('flights.id'))
    # enable backref for many-to-one relationship
    flight = db.relationship("Flight", back_populates="seats")
    #flight = db.relationship('Flight', backref=db.backref('seats', lazy='dynamic' ))

    # TODO: only one seat per ticket?
    ticketnumber = db.Column(db.String(15), db.ForeignKey('tickets.number'), nullable=True)

    # Enum constraint seats labeled from A - H
    seatlabel = db.Column(db.Enum('A','B','C','D','E','F','G','H', name="seatlabelenum", create_type=True), nullable=False)
    seatrow = db.Column(db.Integer, nullable=False)
    checkinstatus =db.Column(db.Boolean, nullable=False)
    flightnumber =  db.Column(db.String(10), nullable=False)
    

    def __init__(self, ticketnumber, flightnumber, seatlabel, seatrow, parentid):
        self.ticketnumber = ticketnumber
        self.flightnumber = flightnumber
        self.seatlabel = seatlabel
        self.seatrow = seatrow
        self.checkinstatus = False
        self.parent_id = parentid

# schema for serialization / serialization of seats
class SeatSchema(ma.Schema):
    number = fields.String(validate=validate.Length(10))
    ticketnumber = fields.String(required=True, validate=validate.Length(1))
    seatlabel = fields.String(required=True, validate=validate.Length(1))
    seatrow = fields.String(required=True, validate=validate.Length(1))
    flightnumber = fields.String(required=True, validate=validate.Length(1))

    @pre_load
    def formatJsonKeys(self, data):
       
        ticketnumber = data.get('ticket-number')
        if ticketnumber:
            data['ticketnumber'] = data.pop('ticket-number')

        seatlabel = data.get('Seat-label')
        if seatlabel:
            data['seatlabel'] = data.pop('Seat-label')

        seatrow = data.get('Seat-row')
        if seatrow:
            data['seatrow'] = data.pop('Seat-row')

        flightnumber = data.get('Flight-number')
        if flightnumber:
            data['flightnumber'] = data.pop('Flight-number')
            
        return data

class Ticket(db.Model):
    __tablename__ = 'tickets'
    
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    number = db.Column(db.String(10),unique=True, nullable=False)
    flightnumber = db.Column(db.String(10),nullable=False)
    passengername = db.Column(db.String(25),nullable=False)
    passportnumber = db.Column(db.String(10),nullable=False)
    status = db.Column(db.Enum('valid','cancelled',name="ticketstatusenum", create_type=True), nullable=False)
    seat_id = db.Column(db.Integer, db.ForeignKey('seats.id'))

    def idgenerator(self, size=7, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))

    def __init__(self, flightnumber, passengername, passportnumber):
        self.number = self.idgenerator(7, string.ascii_uppercase + string.digits)
        self.flightnumber = flightnumber
        self.passengername = passengername
        self.passportnumber = passportnumber
        self.status = "valid"

    # TODO:  Add a column-property for returning the "full" ticketnumber <number>-<seatlabelseatrow> when seat is booked?

# schema for serialization / serialization of tickets
class TicketSchema(ma.Schema):
    
    id = fields.Integer()
    number = fields.String(required=False)
    flightnumber = fields.String(required=True, validate=validate.Length(1))
    passengername = fields.String(required=True, validate=validate.Length(1))
    passportnumber = fields.String(required=True, validate=validate.Length(1))
    status = fields.String()
    seat_id = fields.String() # default to "None" if no seatnumber is given?
   
    @pre_load
    def formatKeys(self, data):
        number = data.get('ticket-number')
        if number:
            data['number'] = data.pop('ticket-number')

        flightnumber = data.get('flight-number')
        if flightnumber:
                data['flightnumber'] = data.pop('flight-number')

        passengername = data.get('name')
        if passengername:
                data['passengername'] = data.pop('name')

        passportnumber = data.get('pass-number')
        if passportnumber:
            data['passportnumber'] = data.pop('pass-number')
        
        seatnumber = data.get('seat_number')
        if seatnumber:
            data['seatnumber'] = data.pop('seat_number')

        return data

    # raise a custom exception when (de)serialization fails
    def handle_error(self, exc, data):
        logging.error(exc.messages)
        raise AppError('An error occurred with input: {0}'.format(data))

# table storing all notifications for transactions
class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    ticketnumber = db.Column(db.String(10), nullable=False)
    title = db.Column(db.String(250), nullable=False)
    message = db.Column(db.String(250), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __init__(self, title, message, ticketnumber):
        # use first seven chars of passport to create the ticketnumber
        self.title = title
        self.message = message
        self.ticketnumber = ticketnumber

# schema forserialization / serialization of flights
class NotificationSchema(ma.Schema):
    class Meta:
        ordered = True

    title = fields.String(required=True, validate=validate.Length(1))
    message = fields.String(required=True, validate=validate.Length(1))
    timestamp = fields.DateTime(required=True)
    
class Flight(db.Model):
    __tablename__ = 'flights'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # define one:many parent/child relationship
    # one way: 
    # seats = relationship("Seat", cascade="all,delete", backref="parent")
    seats = db.relationship("Seat", back_populates="flight")

    flightnumber = db.Column(db.String(10), unique=True, nullable=False)
    start = db.Column(db.String(3), nullable=False)
    end = db.Column(db.String(3), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    aircraft  = db.Column(db.String(15), db.ForeignKey('aircrafts.aircraft'), nullable=False)
    status = db.Column(db.Enum('valid','cancelled',name="ticketstatusenum", create_type=True), nullable=False)
    
    def idgenerator(self, size=6, chars=string.ascii_uppercase + string.digits):
            return ''.join(random.choice(chars) for _ in range(size))

    def __init__(self, start, end, date, aircraft):
        self.flightnumber = self.idgenerator(6, string.ascii_uppercase + string.digits)
        self.start = start
        self.end = end
        self.date = date
        self.aircraft = aircraft
        self.status = "valid"

# schema for serialization / serialization of flights
class FlightSchema(ma.Schema):
    class Meta:
        ordered = True
    
    #id = fields.Integer()
    #flightnumber = fields.String(required=True, validate=validate.Length(1))
    start = fields.String(required=True, validate=validate.Length(1))
    end = fields.String(required=True, validate=validate.Length(1))
    departure = fields.DateTime(required=True, attribute="date")
    aircraft = fields.String(required=True, validate=validate.Length(1))

# schema for serialization / serialization of a single flight
class FlightsSchema(ma.Schema):
    class Meta:
        ordered = True
    
    flightnumber = fields.String(required=True, validate=validate.Length(1))
    start = fields.String(required=True)
    end = fields.String(required=True)
    date = fields.DateTime(required=True)
    aircraft = fields.String(required=True)
    # same value with different encodings. Z and +00:00 are equivalent.
    #departure = fields.DateTime('%Y-%m-%dT%H:%M:%SZ')
    #departure.dateformat("ISO8601")

    @post_dump
    def flightnumber(self, item):
        flightnumber = item.get('flightnumber')
        if flightnumber:
            item['flight-number'] = item.pop('flightnumber')
    
# Create an association table to support a many-to-many relationship between Users and Roles
roles_users = db.Table(
    'roles_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('role.id'))
)


class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

     # __str__ is required by Flask-Admin to have human-readable values for the Role when editing a User
    def __str__(self):
        return self.name

    # __hash__ is required to avoid the exception TypeError: unhashable type: 'Role' when saving a User
    def __hash__(self):
        return hash(self.name)

# schema for serialization / serialization of roles
class RoleSchema(ma.Schema):
    id = fields.Int()
    name = fields.String(required=True, validate=validate.Length(1))
    description = fields.String()
   
class User(db.Model, UserMixin):
    __tablename__ = 'user'

    # the User has six fields: ID, email, password, active, confirmed_at and roles. The roles field represents a
    # many-to-many relationship using the roles_users table. Each user may have no role, one role, or multiple roles.
    id = db.Column(db.Integer, primary_key=True)
    
    # secondary enables many:many
    roles = db.relationship('Role',secondary=roles_users,backref=db.backref('users', lazy='dynamic'))

    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    
    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

# schema for serialization / serialization of users
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

    # Automatically display human-readable names for  current and available Roles when creating or editing a User
    column_auto_select_related = True

    # Prevent administration of Users unless currently logged-in user has "admin" role
    def is_accessible(self):
        return current_user.has_role('admin')

    # On the form for creating or editing a User, don't display a field corresponding to the model's password field.
    # There are two reasons for this. First, we want to encrypt the password before storing in the database. Second,
    # we want to use a password field (with the input masked) rather than a regular text field.
    def scaffold_form(self):

        # Start with the standard form as provided by Flask-Admin. 
        # (above we already excluded the password field from this form)
        form_class = super(UserAdmin, self).scaffold_form()

        # Add a password field, naming it "password2" and labeling it "New Password".
        form_class.password2 = PasswordField('New Password')
        return form_class

    # This callback executes when the user saves changes to a newly-created or edited User 
    # -- before the changes are committed to the database.
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

# custom exception
class AppError(Exception):
    pass