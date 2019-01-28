from flask import Blueprint
from app.views import env

index_blueprint = Blueprint('/', __name__)


@index_blueprint.route('/', methods=['GET'])
def index():
    template = env.get_template('index.html')
    return template.render(message='Index page')
