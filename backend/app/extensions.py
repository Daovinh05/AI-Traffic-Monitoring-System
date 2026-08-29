"""Flask extensions owned by the modular backend."""

from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_session import Session


bcrypt = Bcrypt()
cors = CORS()
session = Session()


def init_extensions(app) -> None:
    bcrypt.init_app(app)
    cors.init_app(app)
    session.init_app(app)
