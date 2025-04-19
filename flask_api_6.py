from flask import Flask, request, jsonify
from typing import List
from flask_restful import Resource, Api
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import PrimaryKeyConstraint
from sqlalchemy import Integer, String, Column, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from flask_caching import Cache
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, JWTManager
from datetime import datetime, date

app = Flask(__name__)
api = Api(app)


app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres_user:postgres_pw@192.168.178.52:5432/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
app.config['JWT_SECRET_KEY'] ='super_duper_secret'

app.config['CACHE_TYPE'] = 'SimpleCache'
app.config['CACHE_DEFAULT_TIMEOUT']=300     #globales Caching --> Aktualisierung des Cache alle 300 Sekunden

cache = Cache(app)

jwt = JWTManager(app)

@app.route("/login", methods=['POST'])              ##JWT Initialisierung über /login
def login():
    username = request.json.get('username', None)
    password = request.json.get('password', None)
    if username != 'test' or password != 'test':
        return jsonify({'msg':'Bad username or password'}), 401
    access_token = create_access_token(identity = username)
    return jsonify(access_token=access_token) 

#Hier wird die Datenbank anhand der Model-Klassen definiert
db = SQLAlchemy(app)

#Model definieren
class Kunde(db.Model):
    __tablename__ = 'kunde'
    kd_nr:Mapped[int]=mapped_column(primary_key = True)
    vorname:Mapped[str]
    nachname:Mapped[str]
    strasse:Mapped[str]
    plz:Mapped[int]
    ort:Mapped[str]
    vorwahl:Mapped[str]
    telefon:Mapped[str]
    geburtsdatum:Mapped[date]
    ledig:Mapped[int]
    rabatt:Mapped[float]
    letzter_zugriff:Mapped[datetime]
    k_a:Mapped[List["Auftrag"]]=relationship()

class Auftrag(db.Model):
    __tablename__ = 'auftrag'
    auft_nr:Mapped[int]=mapped_column(primary_key = True)
    bestelldat:Mapped[date]
    lieferdat:Mapped[date]
    zahlungsziel:Mapped[date]
    zahlungseingang:Mapped[date]
    mahnung:Mapped[int]
    fk_k_a:Mapped[int]=mapped_column(ForeignKey("kunde.kd_nr"))                   #Foreign key auf kunde.kd_nr  
    fk_s_a:Mapped[int]=mapped_column(ForeignKey("shop.shop_nr"))                   #Foreign key auf shop.shop_nr
    


class bestellposition(db.Model):
    __tableame__='bestellposition'
    fk_auftrag:Mapped[int]=mapped_column(ForeignKey("auftrag.auft_nr"))
    position:Mapped[int]
    fk_artikel:Mapped[int]=mapped_column(ForeignKey("artikel.art_nr"))
    anzahl:Mapped[int]

    __table_args__=(
            PrimaryKeyConstraint('fk_auftrag', 'fk_artikel'),
            )

class Artikel(db.Model):
    __tablename__='artikel'
    art_nr:Mapped[int]=mapped_column(primary_key=True)
    artikelbezeichnung:Mapped[str]
    einzelpreis:Mapped[float]
    gewicht:Mapped[float]
    fk_hersteller:Mapped[float]=mapped_column(ForeignKey("hersteller.herst_nr"))
    

class Hersteller(db.Model):
    __tablename__='hersteller'
    herst_nr:Mapped[int]=mapped_column(primary_key=True)
    herstellerbezeichnung:Mapped[str]

class Stadt(db.Model):
    __tablename__='stadt'
    stadt_nr:Mapped[int]=mapped_column(primary_key=True)
    stadt:Mapped[str]
    lat:Mapped[float]
    lot:Mapped[float]

class Shop(db.Model):
    __tablename__='shop'
    shop_nr:Mapped[int]=mapped_column(primary_key=True)
    fk_shoptyp:Mapped[int]
    strasse:Mapped[str]
    plz:Mapped[str]
    fk_stadt:Mapped[int]=mapped_column(ForeignKey("stadt.stadt_nr"))
    s_a:Mapped[List["Auftrag"]]=relationship()                                         

#Initialisierung des Services

class kunde_list(Resource):
    @cache.cached(timeout=60)      #routenspezifisches Caching --> Erneuerung des Cache alle 60 Sekunden
    @jwt_required()
    def get(self):                              #Service Initialisierung   
        now = datetime.utcnow().isoformat()
        print(f"Uhrzeit der Generierung des Cache: {now}")
        current_user = get_jwt_identity()

        #eigentlicher Service startet hier
        kunden=Kunde.query.all() 
        return [{'kd_nr':kunde.kd_nr, 'vorname':kunde.vorname}for kunde in kunden]
    



class service_a(Resource):
    #@cache.cached(timeout=60)
    @jwt_required()
    def post(self):
        data=request.get_json()
        #kd_nr = autoincrement
        kunde_neu = Kunde(
                kd_nr=data.get('kd_nr'),
                vorname = data.get('vorname'),
                nachname = data.get('nachname'),
                plz = data.get('plz'),
                ort= data.get('ort'),
                vorwahl=data.get('vorwahl'),
                telefon=data.get('telefon'),
                geburtsdatum=datetime.strptime(data.get('geburtsdatum'), '%Y-%m-%d'),
                ledig = data.get('ledig'),
                rabatt = data.get('rabatt'),
                letzter_zugriff = datetime.strptime(data.get('letzter_zugriff'), '%Y-%m-%d %H:%M:%S'),
                )
        db.session.add(kunde_neu)
        db.session.commit()
        
        return {"message": "Kunde wurde erstellt."}, 201


api.add_resource(kunde_list, '/kunden')         #gibt auskunft über alle Kunden {"kd_nr": XYZ, "vorname": "Maximilian"}
api.add_resource(service_a, '/service_a')

if __name__== '__main__':
    app.run(debug=True)

