import unittest
import os, logging
import json
import app
from flask import Flask
from app import create_app, db
from base64 import b64encode

class AirlinewsTestCase(unittest.TestCase):
    
    def setUp(self):
        app = create_app()
        app.testing = True
        app.login_manager.init_app(app)
        self.app = app.test_client()

    def test_app_get(self):
        result = self.app.get('/', follow_redirects=True)
        self.assertEqual(result.status_code, 200)

    def test_aircraft_get(self):
        # Test API get all aircrafts (GET request)
        result = self.app.get('v1/flight/', follow_redirects=True)
        self.assertEqual(result.status_code, 200)
        self.assertIn(result, str("aircraft"))
        self.assertIn(result, str("seatcount"))

    def test_aircraft_creation(self):
        # Test API can create a flight (POST request)
        result = self.app.POST('v1/aircraft/', json={ "start":"STR", "end":"FRA", "departure":"2018-10-10T10:00:00Z", "flightnumber" : "SF2490", "aircraft":"Airbus A340"})
        json_data = json.loads(result.data)
        
        self.assertEqual(result.status_code, 201)
        self.assertIn(result, str("success"))
        self.assertIn(result, str("seatcount"))
        self.assertIn(result, str("aircraft"))

    # executed after each test
    def tearDown(self):
        pass  

# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()