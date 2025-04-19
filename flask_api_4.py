from flask import Flask, request, jsonify
from flask_restful import Resource, Api
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, JWTManager
from datetime import datetime

app = Flask(__name__)
api = Api(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres_nutzer:postgres_pw@host:port/db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
app.config['JWT_SECRET_KEY'] ='super_duper_secret'

app.config['CACHE_TYPE'] = 'SimpleCache'
app.config['CACHE_DEFAULT_TIMEOUT']=300     #globales Caching --> Aktualisierung des Cache alle 300 Sekunden

cache = Cache(app)

jwt = JWTManager(app)

@app.route("/login", methods=['POST'])
def login():
    username = request.json.get('username', None)
    password = request.json.get('password', None)
    if username != 'test' or password != 'test':
        return jsonify({'msg':'Bad username or password'}), 401
    access_token = create_access_token(identity = username)
    return jsonify(access_token=access_token) 


db = SQLAlchemy(app)

#Model definieren
class kunde(db.Model):
    kd_nr=db.Column(db.Integer, primary_key=True)
    vorname=db.Column(db.String(50))
    nachname=db.Column(db.String(50))
    strasse=db.Column(db.String(50))
    plz=db.Column(db.Integer)
    ort=db.Column(db.String(50))
    vorwahl=db.Column(db.String(50))
    telefon=db.Column(db.String(50))
    geburtsdatum=db.Column(db.Date)
    ledig=db.Column(db.Boolean)
    rabatt=db.Column(db.Float)
    letzter_zugriff=db.Column(db.DateTime)


class kunde_list(Resource):
    @cache.cached(timeout=60)      #routenspezifisches Caching --> Erneuerung des Cache alle 60 Sekunden
    @jwt_required()
    def get(self):    
        now = datetime.utcnow().isoformat()
        print(f"Uhrzeit der Generierung des Cache: {now}")
        current_user = get_jwt_identity()
        kunden=kunde.query.all() 
        return [{'kd_nr':kunde.kd_nr, 'vorname':kunde.vorname}for kunde in kunden]
    

api.add_resource(kunde_list, '/kunden')
if __name__== '__main__':
    app.run(debug=True)

