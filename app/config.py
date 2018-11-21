import os

# config for postgresql for migrate.py

basedir = os.path.abspath(os.path.dirname(__file__))
SQLALCHEMY_ECHO = False
SQLALCHEMY_TRACK_MODIFICATIONS = False
# read from env vars: 
#SQLALCHEMY_DATABASE_URI = "postgresql://tobi:<see keepass>@localhost/airlinewebservice"
database_uri = 'postgresql+psycopg2://{dbuser}:{dbpass}@{dbhost}/{dbname}'.format(
    dbuser=os.environ['DBUSER'],
    dbpass=os.environ['DBPASS'],
    dbhost=os.environ['DBHOST'],
    dbname=os.environ['DBNAME']
)
SQLALCHEMY_DATABASE_URI=database_uri