from flask_restful import Resource
from flask_security import login_required
from flask_login import current_user

class Welcome(Resource):

    # Get a welcome message when logged in
    @login_required
    def get(self):
        return {"message": "Welcome, "+ current_user.email+" to the airline-webservice!"}