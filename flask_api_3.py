from flask import Flask, request, jsonify
from flask_restful import Resource, Api
from flask_sqlalchemy import SQLAlchemy

from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, JWTManager


app = Flask(__name__)
api = Api(app)

#PostgreSQL_Verbindung erstellen

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres_nutzer:postgres_pw@host:port/db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False

#JWT implementation:
#Wir bilden einen Login-Prozess nach: 1. muss die seite /login besucht werden, damit ein JWT erstellt wird
#2. können Seiten wie /kunden besucht werden, da ein JWT existiert. 
#3. vorher sollte das nicht möglich sein
app.config['JWT_SECRET_KEY'] ='supe_secret'
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
    @jwt_required()
    def get(self):    
        current_user = get_jwt_identity()
        kunden=kunde.query.all() 
        return[{'kd_nr':kunde.kd_nr, 'vorname':kunde.vorname}for kunde in kunden]

api.add_resource(kunde_list, '/kunden')
if __name__== '__main__':
    app.run(debug=True)

