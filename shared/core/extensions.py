"""Shared Flask extensions initialized for reuse across services."""

from flask_jwt_extended import JWTManager
from flask_pymongo import PyMongo

mongo = PyMongo()
jwt = JWTManager()
