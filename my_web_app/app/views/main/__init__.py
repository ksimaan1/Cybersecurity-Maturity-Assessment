from flask import Blueprint

main = Blueprint('main', __name__)

from app.views.main import routes