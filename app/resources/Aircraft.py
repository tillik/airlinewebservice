from flask import request, json,jsonify
from flask_restful import Resource
from flask_security import login_required
from model import db, Aircraft, AircraftSchema, Flight, FlightSchema, Ticket, TicketSchema, Seat, SeatSchema
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
        return aircraft_schema.dump(aircrafts, many=True).data

        # result = aircraft_schema.dump(aircrafts)
        # response = jsonify(result)
        # response.status_code = 200
        # return response

     # Create an aircraft
    @login_required
    def post(self):
        
        json_data = request.get_json(force=True)
        
        if not json_data:
               return {'message': 'No input data provided'}, 400
        
        if not 'aircraft' in json_data:
            return {"success": False, "msg": "must specify aircraft in request"}, 400

        #else:
        #    # remember QuoteSchema.make_object causes an assert
        #    try:
        #       # q = aircraft_schema.load(request['json']).data
        #        q = aircraft_schema.load(json_data)
        #    except AssertionError as e:
        #        return {'success': False, 'msg': str(e)}, 400
        #    else:
        #        print('POST add new aircraft=' + json_data['aircraft'] + ' with seatcount=' +str(json_data['seatcount']), file=sys.stdout)
        #        Aircraft.append(q)
        #        #return {"success": True, "msg": "Quote added."}
        #        #TODO: return 200 ok with create aircraft

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
class AircraftResource(Resource):
    
    # Get all aircrafts
    @login_required
    def get(self, aircraft):
        
        print('GET aircraft by name: ' + aircraft, file=sys.stdout)
        #json_data = request.get_json(force=True)
        #if not json_data:
        #       return {'message': 'No input data provided'}, 400

        if aircraft:
            aircraft = Aircraft.query.filter_by(aircraft=aircraft).first()
            result = aircraft_schema.dump(aircraft).data
            # return 200 OK, 201 would be 'created'
            return {'status': "success", 'data': result}, 200
        else:
            return {"Success": True, "msg": "aircraft not foung in database!"}
    
   