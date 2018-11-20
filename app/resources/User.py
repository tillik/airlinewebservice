from flask import request, jsonify, url_for, abort, make_response
from flask_restful import Resource
from flask_security import login_required
from model import db, User, UserSchema
import sys

users_schema = UserSchema(many=True)
user_schema = UserSchema()

class UserResource(Resource):
   
   # Get all users
    @login_required
    def get(self):
        users = User.query.all()
        result = user_schema.dump(users)
        response = jsonify(result)
        response.status_code = 200
        return response

    def post(self):
        #username = request.json.get('username')
        json_data = request.get_json(force=True)
        
        email=json_data['email']
        print('Received email: ' + email, file=sys.stdout)
        
        # password = request.json.get('password')
        password=json_data['password']
        print('Received password: ' + password, file=sys.stdout)
        
        roles=json_data['roles']
        #print('Received roles: ' + str(roles), file=sys.stdout)
        
        if email is None or password is None or roles is None:
            print('Email or password or role empty in request', file=sys.stdout)
            #return abort (400) # missing arguments
            return make_response(jsonify(error="email or passwort empty in request"), 400)
       
        if User.query.filter_by(email = email).first() is not None:
            print('Email already exists in db: [' + email + ']', file=sys.stdout)
            #return abort(400) # existing user
            return make_response(jsonify(error="email already in database"), 400)
        
        user = User(email = email, roles=[roles])
        user.hash_password(password)
        db.session.add(user)
        db.session.commit()
        
        return jsonify(email=user.email)
    
