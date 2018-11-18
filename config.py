import os

# config for postgresql for migrate.py

basedir = os.path.abspath(os.path.dirname(__file__))
SQLALCHEMY_ECHO = False
SQLALCHEMY_TRACK_MODIFICATIONS = True
SQLALCHEMY_DATABASE_URI = "postgresql://tobi:13Fl@sk57@localhost/airlinewebservice"