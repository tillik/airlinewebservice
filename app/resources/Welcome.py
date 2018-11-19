from flask_restful import Resource
from flask_security import login_required

class Welcome(Resource):

    def get(self):
        return {"message": "Welcome to the flight booking service!"}