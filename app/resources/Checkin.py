import sys, string, logging, traceback

from flask import request, json,jsonify, session
from flask_restful import Resource
from flask_security import login_required, roles_required, roles_accepted
from flask_login import current_user
from model import db, Aircraft, Flight, Seat, Ticket, AircraftSchema, FlightSchema, SeatSchema, TicketSchema
from sqlalchemy import exc
from marshmallow import fields, pprint, Schema


flights_schema = FlightSchema(many=True)
flight_schema = FlightSchema()
tickets_schema = TicketSchema(many=True)
ticket_schema = TicketSchema()
seats_schema = SeatSchema(many=True)
seat_schema = SeatSchema()

class CheckinResource(Resource):
    
    @login_required
    def get(self):
        return {}, 204

    @login_required
    @roles_accepted('admin','customer')
    def post(self):
        
        json_data = request.get_json(force=True)
        if not json_data:
            return {'message': 'No input data provided'}, 400
        
        # with flight and ticket, try to do the checkin

        ticket = None

        try:

            # input validation
            if not all (k in json_data for k in ("ticket-number", "flight-number")):
                return {'error': 'Please provide ticket-number and flight-number!'}, 404

            # retrieve ticket & flight for request
            if "ticket-number" in json_data and "flight-number" in json_data:

                ticket = Ticket.query.filter_by(number=json_data['ticket-number']).first()
                flight = Flight.query.filter_by(flightnumber=json_data['flight-number']).first()

                if not ticket is None and not flight is None:
                    logging.info("Retrieved flight [" + flight.flightnumber + "] and ticket [" + ticket.number  + "]")

                if ticket is None:
                    return {'message': 'Ticket does not exist !'}, 400
                if flight is None: 
                    return {'message': 'Flight does not exist !'}, 400
           
            else:
                return {'message': 'Missing either flight-number or ticket-number!'}, 400

            # flight and ticket must both be valid

            # status not present raises AttributeError
            if not ticket.status == "valid" or not flight.status == "valid":
                return {'message': 'Either flight or ticket are invalid!'}, 400

            # a valid seat has to be assigned to ticket
            # is seat preassigned / "reserved" to ticket ? mark checked in
            
            seat = Seat.query.filter_by(ticketnumber=ticket.number).first()
            
            if seat:
                seat.checkinstatus=True
                db.session.add(seat)
                ticket.seat_id=seat.id
                db.session.add(ticket)
            else: # choose random seat and mark checked in 
                seat = Seat.query.filter_by(flightnumber=flight.flightnumber).first()
                if seat:
                    seat.ticketnumber=ticket.number
                    seat.checkinstatus=True
                    db.session.add(seat)
                    ticket.seat_id=seat.id
                    db.session.add(ticket)
                else:
                    return {'message': 'No more seats available on flight!'}, 400
            # return booked seat
            db.session.commit()

            return {"Location": '/v1/ticket/'+ticket.number}, 200

        except AttributeError as attrex:
             return {'message': 'Either flight or ticket are invalid!'}, 400

        except Exception as e:
                db.session.rollback()
                print("Exception:" + str(e))
                return {"Error": 'Exception on seat creation: ' + str(e)}, 400


    @login_required
    def put(self):
        return {}, 204

    @login_required
    def delete(self):
        return {}, 204