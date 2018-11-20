from flask import request, jsonify
from flask_restful import Resource
from flask_security import login_required
from model import db, Aircraft, Flight, AircraftSchema, FlightSchema, Ticket, TicketSchema, Seat, SeatSchema

tickets_schema = TicketSchema(many=True)
ticket_schema = TicketSchema()

class TicketResource(Resource):
    
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
        
        # validate & deserialize input
        data, errors = ticket_schema.load(json_data)
        if errors:
            return {"status": "error", "data": errors}, 422
        
        ticket = Ticket.query.filter_by(id=data['number']).first()
        if ticket:
            return {'ticket': 'Ticket already exists'}, 400
        
        ticket = Aircraft(
            number=data['number'],
            flightnumber=data['flight-number'],
            passengername=data['name'],
            passportnumber=data['pass-number'],
            seatnumber=data['seat_number']
            )

        db.session.add(ticket)
        db.session.commit()

        result = ticket_schema.dump(ticket).data

        # return 200 OK, 201 would be 'created'
        return {'status': "success", 'data': result}, 200

    @login_required
    def put(self):
        return {}, 204

    @login_required
    def delete(self):
        return {}, 204