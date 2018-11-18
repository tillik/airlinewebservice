from flask_restful import Resource


class Welcome(Resource):
    def get(self):
        return {"message": "Welcome to the flight booking service!"}