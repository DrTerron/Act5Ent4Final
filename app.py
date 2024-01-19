import os
from flask import Flask
from route.es import es
from utils.database import db
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
#app.wsgi_app = ProxyFix(app.wsgi_app)

db_uri = 'sqlite:///{}/prods_datos.db'.format(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
#db = SQLAlchemy()
db.init_app(app)
with app.app_context():
    db.create_all()

app.register_blueprint(es)


