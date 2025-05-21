from flask import Blueprint

bank = Blueprint('bank', __name__)

from app.views.bank import routes