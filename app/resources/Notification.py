import sys, re, logging

from flask import request, json,jsonify, session
from flask_restful import Resource
from flask_security import login_required, roles_required, roles_accepted
from flask_login import current_user
from model import db, Ticket, TicketSchema, Notification, NotificationSchema
from sqlalchemy import exc
from marshmallow import fields, pprint


notifications_schema = NotificationSchema(many=True)
notification_schema = NotificationSchema()

class NotificationResource(Resource):

     # Create new flight
    @login_required
    @roles_accepted('admin', 'customer')
    def post(self, ticketnumber):


        if ticketnumber:
            logging.info("POST - notifications: Received ticketnmber [" + ticketnumber +"]" )

            # only match 7-digit ticketnumbers like T123456
            pattern = re.compile("^([A-Z0-9]{7})$")

            if pattern.match(ticketnumber):

                # get all notifications for ticketnumber ordered by their timestamp
                notifications = Notification.query.filter_by(ticketnumber=ticketnumber).order_by("timestamp").all()

                if notifications:
                    #dump notifications for a specific ticket    
                    return notifications_schema.dump(notifications, many=True).data
                else:
                    return {"status": "No notifications found for ticketnumber " + ticketnumber}, 200
            else:
                return {"Error": "Please specifiy a 7digit-ticketnumber containing only alphanumerical characters!"}, 404    

        else:
            return {"Error": "No ticketnumber specified !"}, 404