import sys, re, logging, sqlalchemy

from flask import request, jsonify
from flask_restful import Resource
from flask_security import login_required
from flask_login import current_user
from model import db, Aircraft, Flight, AircraftSchema, FlightSchema, Ticket, TicketSchema, Seat, SeatSchema, Notification, NotificationSchema

seat_schema = SeatSchema(many=True)
seat_schema = SeatSchema()
ticket_schema = TicketSchema()

class SeatsResource(Resource):
    
    # Return all seats
    @login_required
    def get(self):
        seats = Seat.query.all()
        result = seat_schema.dump(seats)
        response = jsonify(result)
        response.status_code = 200
        return response

    # Create new seat
    @login_required
    def post(self):
        json_data = request.get_json(force=True)
        if not json_data:
            return {'message': 'No input data provided'}, 400
        # Validate & deserialize input
        seat_postdata, errors = seat_schema.load(json_data)
        if errors:
           return errors, 422
       
        # input validation
        if not all (k in seat_postdata for k in ("ticketnumber", "flightnumber", "seatlabel", "seatrow")):
            return {'error': 'Please provide ticketnumber, flightnumber, seatlabel and seatrow !'}, 404

        # is this a valid flight?
        flight = Flight.query.filter_by(flightnumber=seat_postdata['flightnumber']).first()
        if not flight:
            return {'message': 'Flight number does not exist'}, 422

        # is this a valid ticket?
        ticket = Ticket.query.filter_by(number=seat_postdata['ticketnumber']).first()
        if not ticket or ticket.status!="valid":
            return {'message': 'Ticket number does not exist'}, 422
        
        try:
            
             # is this ticketnumber already booked for a another seat?
            seat = Seat.query.filter_by(flightnumber=seat_postdata["flightnumber"]).filter_by(ticketnumber=seat_postdata['ticketnumber']).first()
            if seat:
                return {'message': 'Ticket already booked for another seat'}, 422

            # is this requested ticketnumber already stored for a seat?
            seat = Seat.query.filter_by(flightnumber=seat_postdata["flightnumber"]).filter_by(seatlabel=seat_postdata['seatlabel'], seatrow=seat_postdata['seatrow']).filter_by(ticketnumber=seat_postdata['ticketnumber']).first()
            if seat:
                return {'message': 'Ticket already booked for requested seat'}, 422

            # is the requested seat already booked by someone else?
            seat = Seat.query.filter_by(flightnumber=seat_postdata["flightnumber"]).filter_by(seatlabel=seat_postdata['seatlabel'], seatrow=seat_postdata['seatrow']).filter(Seat.ticketnumber != None).first()
            if seat:
                return {'message': 'Seat already taken for this flight!'}, 422    
                
            # is this a valid seat for this flight? 
            seat = Seat.query.filter_by(flightnumber=seat_postdata["flightnumber"]).filter_by(seatlabel=seat_postdata['seatlabel'], seatrow=seat_postdata['seatrow']).first()
            if not seat:
                return {'message': 'Seat does not exist'}, 422
            else:

                # seat exists and is not taken yet

                seat.ticketnumber=seat_postdata['ticketnumber']
                seatcode = seat.ticketnumber+'-'+seat_postdata['seatlabel']+seat_postdata['seatrow']

                # TODO: How can I also enter the seat.id into ticket.seat_id ??
                ticket.seat_it=seat.id  
                db.session.add(ticket)

                db.session.commit()
                    
                # create a notification for seat booking
                notificationstring = "Seat " + seat.seatlabel + str(seat.seatrow) + " is booked for your ticket " + seat.ticketnumber + "."
                logging.info(notificationstring)
                notification = Notification(
                    title="Seat Booking",
                    message = notificationstring,
                    ticketnumber = seat.ticketnumber
                )

                db.session.add(notification)
                db.session.commit()

            # return 200 OK, 201 would be created 
            return {"Location": '/v1/seat/'+seatcode}, 200

        except (sqlalchemy.exc.SQLAlchemyError, sqlalchemy.exc.DBAPIError) as dex:
            print("Exception:" + str(dex))
            return {"Error": 'Invalid seatlabel or seatrow selected! (Only A-H for seatlabel and one numeric digit for seatrow allowed)'}, 404

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

class SeatResource(Resource):
    @login_required
    def delete(self, seatcode):
        print('Current user is: '+ current_user.email, file=sys.stdout)
        
        try:

            # only match seatcodes like T123456-B8
            pattern = re.compile("^([A-Z0-9]{7}-[A-Z0-9]{2})$")

            if pattern.match(seatcode):
                # split the seatcode into three parts <Ticketnumber>-<Leatlabel><Seatrow>
                parts = seatcode.partition('-')
                ticketnumber = parts[0]
                seatlabel = parts[2][-2]
                seatrow = parts[2][-1]
                
                seat = Seat.query.filter_by(ticketnumber=ticketnumber).first()
                
                if not seat:
                    return {'message': 'No seat booked for ticket'}, 422
                else:
                    #update the seats for the flight by removing the ticketnumber from the entries
                    seat.ticketnumber = None
                    db.session.commit()
                    return {"status": "Successfully cancelled booking of seat"}, 200
            else:
                return {"Error": 'Ticketnumber has wrong format. Expecting <Ticketnumber>-<Leatlabel><Seatrow>'}, 404

        except Exception as e:
            db.session.rollback()
            print("Exception:" + str(e))
            return {"Error": 'Exception on seat cancellation: ' + str(e)}, 400