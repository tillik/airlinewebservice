from flask import request, json,jsonify
from flask_restful import Resource
from flask_security import login_required
from app.model import db, Aircraft, AircraftSchema, Flight, FlightSchema, Ticket, TicketSchema, Seat, SeatSchema
from marshmallow import ValidationError
import sys

# schemas can also be used as a Serializer
aircrafts_schema = AircraftSchema(many=True)
aircraft_schema = AircraftSchema()


class AircraftsResource(Resource):

    # dump all aircrafts
    @login_required
    def get(self):
        aircrafts = Aircraft.query.all()
        # return aircraft_schema.dump(aircrafts, many=True).data
        result = aircraft_schema.dump(aircrafts, many=True).data
        response = jsonify(result)
        response.status_code = 200
        return response

     # Create an aircraft
    @login_required
    def post(self):
        
        json_data = request.get_json(force=True)
        
        if not json_data:
               return {'message': 'No input data provided'}, 400
        
        # input validation
        if not all (k in json_data for k in ("aircraft", "seatcount")):
            return {'message': 'Please provide aircraft and seatcount!'}, 404
        
        # validate & deserialize input
        data, errors = aircraft_schema.load(json_data)
        if errors:
            return {'message' : 'error', 'data': errors}, 422        
        aircraft = Aircraft.query.filter_by(aircraft=data['aircraft']).first()
        if aircraft:
            return {'message': 'Aircraft already exists'}, 400
         
        # TODO: creating an object could be done via the pre_load method in the schema
        aircraft = Aircraft(
            aircraft=data['aircraft'],
            seatcount=data['seatcount']
            )

        db.session.add(aircraft)
        db.session.commit()
        result = aircraft_schema.dump(aircraft).data
        # return 200 OK, 201 would be 'created'
        return {'message': "success", 'data': result}, 200
       
    @login_required
    def put(self):
        return {}, 204

    @login_required
    def delete(self):
        return {}, 204
class AircraftResource(Resource):
    
    # Get all aircrafts
    @login_required
    def get(self, aircraft):
        
        logging.info('GET aircraft by name: ' + aircraft)
        
        #json_data = request.get_json(force=True)
        #if not json_data:
        #       return {'message': 'No input data provided'}, 400

        if aircraft:
            aircraft = Aircraft.query.filter_by(aircraft=aircraft).first()
            result = aircraft_schema.dump(aircraft).data
            # return 200 OK, 201 would be 'created'
            return {'message': "success", 'data': result}, 200
        else:
            return {"Success": True, "msg": "aircraft not foung in database!"}
    
   