from flask import request, json,jsonify, session
from flask_restful import Resource
from flask_security import login_required, roles_required
from flask_login import current_user
from model import db, Aircraft, Flight, AircraftSchema, FlightSchema, Ticket, TicketSchema, Seat, SeatSchema
from marshmallow import fields, pprint
import sys

flights_schema = FlightSchema(many=True)
flight_schema = FlightSchema()


class FlightsResource(Resource):


    # dump all flights
    @login_required
    def get(self):
        # flask-restful also allows data, status code, header tuples
        flights = Flight.query.all()
        
        # dump all using schema
        #flight_schema_ex = FlightSchema(exclude=['number'])
        flight_schema_ex = FlightSchema()
        return flight_schema_ex.dump(flights, many=True).data

        # simple dump:
        # result = flight_schema.dump(flights)
        # response = jsonify(result)
        # response.status_code = 200
        # return response

     # Create new flight
    @login_required
    def post(self):
        
        json_data = request.get_json(force=True)
        if not json_data:
            return {'message': 'No input data provided'}, 400
        # Validate & deserialize input
        data, errors = flight_schema.load(json_data)
        if errors:
            return errors, 422
        else:
            #try:
            #    flight = flight_schema.load(data)
            #except BaseException as e:
            #    return {'success': False, 'msg': str(e)}, 400
            #else:
                

            #print('POST add new flight with number=' + json_data['flightnumber'] + \
            #                             ' start=' + json_data['start'] +\
            #                             ' end=' + json_data['end'] +\
            #                             ' departure=' + json_data['departure'] +\
            #                             ' aircraft=' + json_data['aircraft'])

            flight = Flight.query.filter_by(flightnumber=data['flightnumber']).first()
            if flight:
                return {'message': 'Flightnumber already exists'}, 400

            flight = Flight(
                flightnumber=json_data['flightnumber'],
                start=json_data['start'],
                end=json_data['end'],
                date=json_data['departure'],
                aircraft=json_data['aircraft']
                )

            db.session.add(flight)
            db.session.commit()

            result = flight_schema.dump(flight).data

            # return 200 OK, 201 would be created 
            # After the flight is created the URL to the GET request of this flight is given as a response
            #return { "status": 'success', 'data': result }, 200
            return {"status": 'success', "location": '/v1/flight/'+flight.flightnumber}, 200

    @login_required
    def put(self):
        return {}, 204

    @login_required
    def delete(self):
        return {}, 204

class FlightResource(Resource):
    
    @login_required
    def get(self, flightnumber):
        if flightnumber:
            #flights = Flight.query.all()
            flight = Flight.query.filter_by(flightnumber=flightnumber).first()
            result = flight_schema.dump(flight)
            response = jsonify(result)
            response.status_code = 200
            return response
        #return {json.dumps(result)}, 200
        return {'error': 'Missing flight number in request'}, 400

    @login_required
    @roles_required('admin')
    def  delete(self, flightnumber):
        print('Current user is: '+ current_user.email, file=sys.stdout)
        if flightnumber:
            flight = Flight.query.filter_by(flightnumber=flightnumber).first()
            if not flight:
                return {'message': 'Flightnumber does not exist'}, 400
            else:
                db.session.delete(flight)
                db.session.commit()
                