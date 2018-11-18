from flask import Blueprint
from flask_restful import Api
from resources.Welcome import Welcome
from resources.Flight import FlightResource
from resources.Aircraft import AircraftResource
from resources.Ticket import TicketResource
from resources.Seat import SeatResource

# https://blog.miguelgrinberg.com/post/designing-a-restful-api-using-flask-restful/page/6
api_bp = Blueprint('api', __name__)
api = Api(api_bp)

# Routes
api.add_resource(Welcome, '/Welcome')
api.add_resource(FlightResource, '/flights')
api.add_resource(TicketResource, '/ticket')
api.add_resource(AircraftResource, '/aircraft')
api.add_resource(SeatResource, '/seat')

