from flask import Flask
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from model import db

# small script to manually migrate the db

def create_app(config_filename):
    app = Flask(__name__)
    app.config.from_object(config_filename)
    db.init_app(app)
    return app
    
if __name__ == '__main__':
    app = create_app("config")
    migrate = Migrate(app, db)
    manager = Manager(app)
    manager.add_command('db', MigrateCommand)
    manager.run()