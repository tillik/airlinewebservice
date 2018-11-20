import os

# config for postgresql for migrate.py

basedir = os.path.abspath(os.path.dirname(__file__))
SQLALCHEMY_ECHO = False
SQLALCHEMY_TRACK_MODIFICATIONS = False
# read from env vars: 
# SQLALCHEMY_DATABASE_URI = "postgresql://tobi:13Fl@sk57@localhost/airlinewebservice"
SQLALCHEMY_DATABASE_URI=database_uri