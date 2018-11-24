import sys

from flask import request, jsonify
from flask_restful import Resource
from flask_security import login_required, roles_required, roles_accepted
from flask_login import current_user
from model import db, Aircraft, Flight, AircraftSchema, FlightSchema, Ticket, TicketSchema, Seat, SeatSchema

tickets_schema = TicketSchema(many=True)
ticket_schema = TicketSchema()

class TicketsResource(Resource):
    
    # Get all tickets
    @login_required
    def get(self):
        tickets = Ticket.query.all()
        result = ticket_schema.dump(tickets)
        response = jsonify(result)
        response.status_code = 200
        return response
    
    @login_required
    def post(self):
        json_data = request.get_json(force=True)
        if not json_data:
               return {'message': 'No input data provided'}, 400
        
        # deserialize input: map json fields to schema fields
        # specifying partial=True to enable seatnumber being optional
        
        # TODO: the sample requests contain dashes in the JSON fieldnames which prevents simply mapping them 
        # to schema fields. This collides when I try to deserialize them (to renamed json fields)  with some fields beinf optional like seatnumber
        # this does not work:
        # data, errors = ticket_schema.load({"flightnumber":json_data["flight-number"],"passengername":json_data["passengername"],"passportnumber":json_data["pass-number"],"seatnumber":json_data["seat_number"]}, partial=True)
        # overload the serializer for each schema?
        data, errors = ticket_schema.load(json_data, partial=True)
        

        if errors:
            return {"status": "error", "data": errors}, 422
        
        # only one ticket per passport
        ticket = Ticket.query.filter_by(passportnumber=data["passportnumber"]).first()
        if ticket:
            return {'ticket': 'Passport-number already booked a seat'}, 400

        # check ticket-db if seatnumber is already taken (seatnumber is optional)
        seatnr=data["seatnumber"]
        if not seatnr == "None":
            # try to find tickets with requested seatnumber
            #ticket = Ticket.query.filter_by(seat.number=seatnr).first()
            ticket = Seat.query(Ticket).join(Seat, Ticket.id).filter(Seat.number==seatnr)
            if ticket:
                return {'ticket': 'Seatnumber already booked'}, 400
           
        # get seatcount from aircraft specified in ticket 
        flight = Flight.query.filter_by(flightnumber=data["flightnumber"]).first()
        if flight:
            aircraft = Aircraft.query.filter_by(aircraft=flight.aircraft).first()
            if not aircraft:
                return {'ticket': 'Ticket containing invalid aircraft'}, 400
            else: 
                seatcount = aircraft.seatcount
        else:
            return {'ticket': 'Flight does not exist'}, 400
        
        # sum existing tickets for same flight must be smaller than seatcount
        tickets  = Ticket.query.filter_by(flightnumber=data["flightnumber"])
        ticketsnumber = tickets.count()

        if ticketsnumber >= seatcount:
            return {'ticket': 'No more seats left for this flight'}, 400

        ticket = Ticket(
            flightnumber=data['flightnumber'],
            passengername=data['passengername'],
            passportnumber=data['passportnumber'],
        )

        db.session.add(ticket)
        db.session.commit()

        result = ticket_schema.dump(ticket).data

        # return 200 OK, 201 would be created 
        # return { "status": 'success', 'data': result }, 200
        # After the flight is created the URL to the GET request of this flight is given as a response
        return {"status": 'success', "location": '/v1/ticket/'+ticket.number}, 200

    @login_required
    def put(self):
         return {'status': "Not implemented"}, 204 # 204 = No content

    @login_required
    @roles_required('user')
    def  delete(self):
        return {'status': "Not implemented"}, 204 # 204 = No content

class TicketResource(Resource):

    @login_required
    def get(self, ticketnumber):
        if ticketnumber:
            #flights = Flight.query.all()
            ticket = Ticket.query.filter_by(number=ticketnumber).first()
            result = ticket_schema.dump(ticket)
            response = jsonify(result)
            response.status_code = 200
            return response
        #return {json.dumps(result)}, 200
        return {'error': 'Missing ticketnumber in request'}, 400

    @login_required
    def post(self):
        return {'status': "Not implemented"}, 204 # 204 = No content

    @login_required
    def put(self):
        return {'status': "Not implemented"}, 204 # 204 = No content

    @login_required
    @roles_accepted('user','admin')
    def  delete(self, ticketnumber):
        print('Current user is: '+ current_user.email, file=sys.stdout)
        
        try:
            if ticketnumber:
                Ticket.query.filter_by(number=ticketnumber).delete()
                db.session.commit()
                return {"status": "Successfully deleted ticket with number "+ticketnumber}, 200
            else:
                return{"status": "No ticket found with ticketnumber: " + ticketnumber}, 400
        except Exception as e:
            db.session.rollback()
            print("Exception:" + str(e))
            return {"Error": 'Exception on flight deletion: ' + str(e)}, 400