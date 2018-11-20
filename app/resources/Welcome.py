from flask_restful import Resource
from flask_security import login_required

class Welcome(Resource):

    # Get a welcome message when logged in
    @login_required
    def get(self):
        return {"message": "Welcome to the flight booking service!"}