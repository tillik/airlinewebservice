import sys, re, logging

from flask import request, jsonify
from flask_restful import Resource
from flask_security import login_required, roles_required, roles_accepted
from flask_login import current_user
from webapp.model import db, Aircraft, Flight, AircraftSchema, FlightSchema, Ticket, TicketSchema, Seat, SeatSchema, Notification, NotificationSchema, InvalidPassport
import webapp

tickets_schema = TicketSchema(many=True)
ticket_schema = TicketSchema(partial=True)

class TicketsResource(Resource):
    
    # Get all tickets
    @login_required
    def get(self):

        tickets = Ticket.query.all()
        result = ticket_schema.dump(tickets)
        if result is not None:
            response = jsonify(result)
            response.status_code = 200
            return response
        else:
            return '', 204

    @login_required
    def post(self):
        json_data = request.get_json(force=True)
        if not json_data:
               return {'message': 'No input data provided'}, 400
        
        # deserialize input: map json fields to schema fields
        # specifying partial=True to enable seatnumber being optional
        
        # the sample requests contain dashes in the JSON fieldnames which prevents simply mapping them 
        # to schema fields. This collides when I try to deserialize them (to renamed json fields)  with some fields beinf optional like seatnumber
        # this does not work:
        # data, errors = ticket_schema.load({"flightnumber":json_data["flight-number"],"passengername":json_data["passengername"],"passportnumber":json_data["pass-number"],"seatnumber":json_data["seat_number"]}, partial=True)
        # TODO: overload the serializer for each schema / create propert objects in schema pre_load?
        data, errors = ticket_schema.load(json_data, partial=True)

        # only match 7-digit ticketnumbers like T123456
        pattern = re.compile("^([A-Z0-9]{7})$")

        if errors:
            return {"message": "error", "data": errors}, 422

        try:
            # input validation
            if not all (k in data for k in ("flightnumber", "passengername", "passportnumber")):
                return {'message': 'Please provide flightnumber, passengername and passportnumber !'}, 404
            elif not pattern.match(data["passportnumber"]):
                return {'message': 'Please provide valid passportnumber (7-digit numbers and uppercase characters) !'}, 404

            # only one ticket (that is not canceled) per passport for a flight 
            if "passportnumber" in data:
                ticket = Ticket.query.filter_by(passportnumber=data["passportnumber"]).filter_by(flightnumber=data["flightnumber"]).filter(Ticket.status != "cancelled").first()
                if ticket:
                    return {'message': 'Passport-number already booked a ticket for this flight'}, 404

            # check ticket-db if seatnumber is already taken (seatnumber is optional)
            if "seatnumber" in data:
                seatnr=data["seatnumber"]
                # try to find tickets with requested seatnumber
                # ticket = Ticket.query.filter_by(seat.number=seatnr).first()
                ticket = Seat.query(Ticket).join(Seat, Ticket.id).filter(Seat.number==seatnr)
                if ticket:
                    return {'message': 'Seatnumber already booked'}, 404
            
            # get seatcount from aircraft specified in ticket 
            if "flightnumber" in data:
                flight = Flight.query.filter_by(flightnumber=data["flightnumber"]).first()
                if flight:
                    aircraft = Aircraft.query.filter_by(aircraft=flight.aircraft).first()
                    if not aircraft:
                        return {'message': 'Ticket containing invalid aircraft'}, 400
                    else: 
                        seatcount = aircraft.seatcount
                else:
                    return {'message': 'Flight does not exist'}, 400

            #try

            # are there tickets left for flight? sum tickets for same flight must be smaller seatcount
            tickets  = Ticket.query.filter_by(flightnumber=data["flightnumber"])
            ticketsnumber = tickets.count()

            if ticketsnumber >= seatcount:
                return {'message': 'No more seats left for this flight'}, 404

            # TODO: creating an object could be done via the pre_load method in the schema
            ticket = Ticket(
                flightnumber=data['flightnumber'],
                passengername=data['passengername'],
                passportnumber=data['passportnumber'],
            )

            db.session.add(ticket)
            db.session.commit()

            # Create a notification for ticket booking using the ticketnumber for the just created ticket
            ticket = Ticket.query.filter_by(passportnumber=data["passportnumber"]).filter_by(flightnumber=data["flightnumber"]).filter(Ticket.status != "cancelled").first()
            
            notificationstring = "Your ticket booking " + ticket.number+ " is successful."
            logging.info(notificationstring)
            notification = Notification(
                title = "Booking Successful",
                message = notificationstring,
                ticketnumber = ticket.number
            )

            db.session.add(notification)
            db.session.commit()

            result = ticket_schema.dump(ticket).data

            # return 200 OK, 201 would be created 
            # return { "status": 'success', 'data': result }, 200
            # After the flight is created the URL to the GET request of this flight is given as a response
            return {"Location": '/v1/ticket/'+ticket.number}, 200

        except InvalidPassport as invEx:
            db.session.rollback()
            logging.error("Exception:" + str(invEx))
            return {'error' : 'Passport number is invalid ;-) ' + str(invEx)}, 400

        except Exception as e:
            db.session.rollback()
            logging.info("Exception:" + str(e))
            return {'message' : 'Exception on ticket creation: ' + str(e)}, 400

    @login_required
    def put(self):
         return {'message': "Not implemented"}, 204 # 204 = No content

    @login_required
    @roles_required('user')
    def  delete(self):
        return {'message': "Not implemented"}, 204 # 204 = No content

class TicketResource(Resource):

    @login_required
    def get(self, ticketnumber):
        if ticketnumber:
            
            # Input validation:
            # only match 7-digit ticketnumbers like T123456
            pattern = re.compile("^([A-Z0-9]{7})$")
            if pattern.match(ticketnumber):
                
                ticket = Ticket.query.filter_by(number=ticketnumber).first()
                if ticket is not None:
                
                    result = ticket_schema.dump(ticket)
                    response = jsonify(result)
                    response.status_code = 200
                    return response
                    #return {json.dumps(result)}, 200
                else:
                    return {'message': 'No ticket found with number ' + ticketnumber}, 400        
            else:
                return {'message': 'Please enter a valid 7-digit ticketnumber (only numbers and uppercase characters) !'}, 400
        else:
            return {'message': 'Missing ticketnumber in request'}, 400

    @login_required
    def post(self):
        return {'status': "Not implemented"}, 204 # 204 = No content

    @login_required
    def put(self):
        return {'status': "Not implemented"}, 204 # 204 = No content

    @login_required
    @roles_accepted('user','admin')
    def  delete(self, ticketnumber):
        logging.info('Current user is: '+ current_user.email, file=sys.stdout)
        
        try:
            if ticketnumber:
                Ticket.query.filter_by(number=ticketnumber).delete()
                db.session.commit()
                return {"status": "Successfully deleted ticket with number "+ticketnumber}, 200
            else:
                return{"status": "No ticket found with ticketnumber: " + ticketnumber}, 400
        except Exception as e:
            db.session.rollback()
            logging.info("Exception:" + str(e))
            return {'message' : 'Exception on flight deletion: ' + str(e)}, 400