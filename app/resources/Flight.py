from flask import request
from flask_restful import Resource
from model import db, Aircraft, Flight, AircraftSchema, FlightSchema, Ticket, TicketSchema, Seat, SeatSchema

flights_schema = FlightSchema(many=True)
flight_schema = FlightSchema()

class FlightResource(Resource):
    def get(self):
        return {}, 200

    # Create new flight
    def post(self):
       json_data = request.get_json(force=True)
       if not json_data:
              return {'message': 'No input data provided'}, 400
       # Validate & deserialize input
       data, errors = flight_schema.load(json_data)
       if errors:
           return errors, 422
       
       flight = Flight.query.filter_by(number=data['flightnumber']).first()
       if flight:
           return {'message': 'Flight already exists'}, 400
       flight = Flight(
           number=json_data['flightnumbernumber'],
           start=json_data['start'],
           end=json_data['end'],
           departure=json_data['departure'],
           aircraft=json_data['aircraft']
           )

       db.session.add(flight)
       db.session.commit()

       result = flight_schema.dump(flight).data

       # return 200 OK, 201 would be created 
       # After the flight is created the URL to the GET request of this flight is given as a response
       #return { "status": 'success', 'data': result }, 200
       return {"status": 'success', "location": '/v1/flight/'+flight.number}, 200

    def put(self):
        return {}, 204

    def delete(self):
        return {}, 204