from flask import request
from flask_restful import Resource
from model import db, Aircraft, Flight, AircraftSchema, FlightSchema, Ticket, TicketSchema, Seat, SeatSchema

seat_schema = SeatSchema(many=True)
seat_schema = SeatSchema()

class SeatResource(Resource):
    def get(self):
        return {}, 200

    # Create new seat
    def post(self):
       json_data = request.get_json(force=True)
       if not json_data:
              return {'message': 'No input data provided'}, 400
       # Validate & deserialize input
       data, errors = seat_schema.load(json_data)
       if errors:
           return errors, 422
       
       seat = Flight.query.filter_by(name=data['ticketnumber']).first()
       if seat:
           return {'message': 'Seat already exists'}, 400
       seat = Seat(
           ticketnumber=json_data['ticket-number'],
           flightnumber=json_data['Flight-number'],
           seatlabel=json_data['Seat-label'],
           seatrow=json_data['Seat-row']
           )

       db.session.add(seat)
       db.session.commit()

       result = seat_schema.dump(seat).data

       # return 200 OK, 201 would be created 
       return { "status": 'success', 'data': result }, 200

    def put(self):
        return {}, 204

    def delete(self):
        return {}, 204