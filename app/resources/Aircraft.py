from flask import request, json,jsonify
from flask_restful import Resource
from flask_security import login_required
from model import db, Aircraft, AircraftSchema, Flight, FlightSchema, Ticket, TicketSchema, Seat, SeatSchema
from marshmallow import ValidationError

aircrafts_schema = AircraftSchema(many=True)
aircraft_schema = AircraftSchema()

class AircraftResource(Resource):
    
    # Get all aircrafts
    @login_required
    def get(self):
        aircrafts = Aircraft.query.all()
        result = aircraft_schema.dump(aircrafts)
        response = jsonify(result)
        response.status_code = 200
        return response

    # Create an aircraft
    @login_required
    def post(self):
        json_data = request.get_json(force=True)
        if not json_data:
               return {'message': 'No input data provided'}, 400
        
        # validate & deserialize input

        data, errors = aircraft_schema.load(json_data)
        if errors:
            return {"status": "error", "data": errors}, 422        
        aircraft = Aircraft.query.filter_by(aircraft=data['aircraft']).first()
        if aircraft:
            return {'message': 'Aircraft already exists'}, 400
        
        aircraft = Aircraft(
            aircraft=data['aircraft'],
            seatcount=data['seatcount']
            )

        db.session.add(aircraft)
        db.session.commit()

        result = aircraft_schema.dump(aircraft).data

        # return 200 OK, 201 would be 'created'
        return {'status': "success", 'data': result}, 200

    @login_required
    def put(self):
        return {}, 204

    @login_required
    def delete(self):
        return {}, 204