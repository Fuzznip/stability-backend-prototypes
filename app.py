import os

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask import Flask, render_template
from dotenv import load_dotenv
from flask_swagger_ui import get_swaggerui_blueprint
from scripts.combine_swagger import combine_swagger_files

load_dotenv()

DATABASE_USERNAME = os.getenv("DATABASE_USERNAME")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_URL = os.getenv("DATABASE_URL")

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']=f"postgresql://{DATABASE_USERNAME}:{DATABASE_PASSWORD}@{DATABASE_URL}"
app_context = app.app_context()
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Ensure swagger.json is generated at app startup
project_root = os.path.dirname(os.path.abspath(__file__))
swagger_input_dir = os.path.join(project_root, "static/swagger")
swagger_output_file = os.path.join(project_root, "static/swagger.json")

# Ensure the static directory exists
if not os.path.exists(os.path.join(project_root, "static")):
    os.makedirs(os.path.join(project_root, "static"))

# Generate the combined swagger file
combine_swagger_files(swagger_input_dir, swagger_output_file)

# Configure Swagger UI
SWAGGER_URL = '/docs'  # URL for exposing Swagger UI
API_URL = '/static/swagger.json'  # Path to the Swagger JSON file

# Register Swagger UI blueprint
swaggerui_blueprint = get_swaggerui_blueprint(SWAGGER_URL, API_URL)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

# Needed to auto generate tables using SQLAlchemy
from models import models, stability_party_3

# make app aware of all endpoints
from endpoints import users, announcements, splits, applications, diary, ranks, raid_tier
from endpoints.events import item_whitelist, submit

# Initialize event handlers
from event_handlers import app_init

if __name__ == '__main__':
    app.run(debug=False)

