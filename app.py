import os

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask import Flask, render_template
from dotenv import load_dotenv
from flask_swagger_ui import get_swaggerui_blueprint

load_dotenv()

DATABASE_USERNAME = os.getenv("DATABASE_USERNAME")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_URL = os.getenv("DATABASE_URL")

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']=f"postgresql://{DATABASE_USERNAME}:{DATABASE_PASSWORD}@{DATABASE_URL}"
app_context = app.app_context()
db = SQLAlchemy(app)
migrate = Migrate(app, db)

SWAGGER_URL = '/docs'  # URL for exposing Swagger UI
API_URL = '/static/swagger.json'  # Path to the Swagger JSON file

# Register Swagger UI blueprint
swaggerui_blueprint = get_swaggerui_blueprint(SWAGGER_URL, API_URL)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

# Needed to auto generate tables using SQLAlchemy
from models import *

# make app aware of all endpoints
from endpoints import users, announcements, splits, applications

if __name__ == '__main__':
    app.run(debug=False)

