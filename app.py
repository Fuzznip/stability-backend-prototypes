import os

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask import Flask
from dotenv import load_dotenv

load_dotenv()

DATABASE_USERNAME = os.getenv("DATABASE_USERNAME")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_URL = os.getenv("DATABASE_URL")

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']=f"postgresql://{DATABASE_USERNAME}:{DATABASE_PASSWORD}@{DATABASE_URL}"
db = SQLAlchemy(app)
migrate = Migrate(app, db)


# Needed to auto generate tables using SQLAlchemy
from models import *

# make app aware of all endpoints
from endpoints import leaderboard, users, announcements, webhooks

if __name__ == '__main__':
    from waitress import serve
    serve(app, host="0.0.0.0", port=5000)
