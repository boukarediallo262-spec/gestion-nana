import os

class Config:
    SECRET_KEY = "super_secret_key"

    SQLALCHEMY_DATABASE_URI = "sqlite:///database.db"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
