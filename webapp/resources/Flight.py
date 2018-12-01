import sys, string, logging, traceback

from flask import request, json,jsonify, session
from flask_restful import Resource
from flask_security import login_required, roles_required, roles_accepted
from flask_login import current_user
from sqlalchemy import exc
from marshmallow import fields, pprint
from webapp.model import db, Aircraft, Flight, AircraftSchema, FlightSchema, FlightsSchema, Ticket, TicketSchema, Seat, SeatSchema, Notification, NotificationSchema

flights_schema = FlightSchema(many=True)
flight_schema = FlightSchema()


class FlightsResource(Resource):


    # Dump all flights
    @login_required
    @roles_required('admin')
    def get(self):
        
        flights = Flight.query.all()
        
        # dump all using schema
        flight_schema_ex = FlightsSchema()
        return flight_schema_ex.dump(flights, many=True).data
        

    # Create new flight
    @login_required
    @roles_required('admin')
    def post(self):
        
        json_data = request.get_json(force=True)
        if not json_data:
            return {'message': 'No input data provided'}, 400
        # Validate & deserialize input
        flight_schema = FlightSchema()
        data, errors = flight_schema.load(json_data)
        if errors:
            return errors, 422
        else:
            try:    
                
                # input validation
                if not all (k in data for k in ("start", "end", "aircraft", "date")):
                    return {'message': 'Please provide start, end, aircraft and departure!'}, 404
                
                logging.info('POST add new flight received values:')
                for k,v in json_data.items():
                   logging.info(str(k)+': '  + str(v))

                #flight = Flight.query.filter_by(flightnumber=data['flightnumber']).first()
                #if flight:
                #    return {'message': 'Flightnumber already exists'}, 400

                aircraft = Aircraft.query.filter_by(aircraft=data['aircraft']).first()
                if not aircraft:
                    return {'message': 'Aircraft does not exist'}, 400

                flight = Flight(
                    #flightnumber=json_data['flightnumber'],
                    start=json_data['start'],
                    end=json_data['end'],
                    date=json_data['departure'],
                    aircraft=json_data['aircraft']
                    )

                # commit flights now or else seats wont have flight-id's                
                db.session.add(flight)
                db.session.commit()

                # precreate all seats for the flight (limited by aircraft seatcount)
                # expand all combinations of [A-H][0-9] and insert them into seats.seatlabel seats.seatrow
                count = 0
                logging.info('Aircraft seatcount is: ' + str(aircraft.seatcount))
                #while count <= aircraft.seatcount:
                for label in range(ord('A'), ord('H')): 

                    for row in range(1,20): 
                        if count == aircraft.seatcount:
                            logging.info('Created number of seats: '+ str(count))
                            break
                                                
                        seat = Seat(None,flight.flightnumber,chr(label),row, flight.id)
                    
                        logging.info('Pre-creating seat no. '+ str(count) +' [' + chr(label)+ str(row)+'] for flight '+flight.flightnumber)
                        db.session.add(seat)
                        count+=1
                        
                db.session.commit()
            except (exc.IntegrityError, exc.InvalidRequestError):
                logging.error("ERROR for creating new flight")
				# handle errors
                db.session.rollback()
                return {'message' : 'Exception: foreign key violation ' + str(exc)}, 400

            result = flight_schema.dump(flight).data

            # After the flight is created the URL to the GET request of this flight is given as a response
            return {"location": '/v1/flight/'+flight.flightnumber}, 200

    @login_required
    def put(self):
         return {"message": 'Not implemented'}, 204

    @login_required
    def delete(self):
        return {"message": 'Not implemented'}, 204

class FlightResource(Resource):
    
    # Get a flight by flightnumber
    @login_required
    @roles_accepted('admin','customer')
    def get(self, flightnumber):
        logging.info('Current user is: '+ current_user.email)
        
        if flightnumber:
            #flights = Flight.query.all()
            flight = Flight.query.filter_by(flightnumber=flightnumber).first()
            if flight is None:
                return {'message': 'No flight found with number ' + str(flightnumber)}, 404
            else:
                result = flight_schema.dump(flight).data
                response = jsonify(result)
                response.status_code = 200
                return response
                #return {json.dumps(result)}, 200
        else:
            return {'message': 'Missing flightnumber in request'}, 400

     # Delete a flight by flightnumber ("cancelling flight")
    @login_required
    @roles_required('admin')
    def  delete(self, flightnumber):
        logging.info('Current user is: '+ current_user.email)
        
        try:
            if flightnumber:
                flight = Flight.query.filter_by(flightnumber=flightnumber).first()
                if not flight:
                    return {'message': 'Flightnumber does not exist'}, 400
                else:
                    # flight deletion must: 
                    
                    # a) update existing tickets: 
                    #       - set status cancelled
                    #       - remove seat bookings 
                    #         (do not unset flightnumber - 
                    #          or booking new flight with same passportnumber will fail)
                    tickets = Ticket.query.filter_by(flightnumber=flightnumber).all()
                    for ticket in tickets:
                        ticket.status="cancelled"
                        #ticket.flightnumber=None
                        ticket.seat_id=None
                        db.session.add(ticket)

                        # create notification for each cancelled ticket 
                        notificationstring = "The flight " + flightnumber + " was canceled"
                        logging.info(notificationstring)
                        notification = Notification(
                            title="Flight canceled",
                            message = notificationstring,
                            ticketnumber = ticket.number 
                        )
                        db.session.add(notification)

                    db.session.commit()
                    
                    # b) update existing seats:
                    #       - remove ticket assignments
                    seats = Seat.query.filter_by(flightnumber=flightnumber).all()
                    for seat in seats:
                        seat.ticketnumber=None
                        db.session.add(seat)
                    db.session.commit()
                    
                    # c) delete all seats for the flight
                    Seat.query.filter_by(flightnumber=flightnumber).delete()
                    #db.session.delete(seats)
                    db.session.delete(flight)
                    db.session.commit()

                    return {"message": "Successfully cancelled flight and all seats"}, 200
        except Exception as e:
            db.session.rollback()
            logging.info("Exception:" + str(e))
            return {'message': 'Exception on flight deletion: ' + str(e)}, 400