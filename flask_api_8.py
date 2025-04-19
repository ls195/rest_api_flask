from flask import Flask, request, jsonify
from typing import List
from flask_restful import Resource, Api
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import PrimaryKeyConstraint, func
from sqlalchemy import Integer, String, Column, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from flask_caching import Cache
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, JWTManager
from datetime import datetime, date, timedelta

app = Flask(__name__)
api = Api(app)


app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres_nutzer:postgres_pw@host:port/db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
app.config['JWT_SECRET_KEY'] ='super_duper_secret'

app.config['CACHE_TYPE'] = 'SimpleCache'
app.config['CACHE_DEFAULT_TIMEOUT']=300     #globales Caching --> Aktualisierung des Cache alle 300 Sekunden

cache = Cache(app)

jwt = JWTManager(app)

@app.route("/login", methods=['POST'])              ##JWT Initialisierung über /login --> zuerst muss man über Login den Token generieren
def login():
    username = request.json.get('username', None)
    password = request.json.get('password', None)
    if username != 'test' or password != 'test':
        return jsonify({'msg':'Bad username or password'}), 401
    access_token = create_access_token(identity = username)
    return jsonify(access_token=access_token) 

#Hier wird die Datenbank anhand der Model-Klassen definiert ---> ORM
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
    fk_kunde:Mapped[int]=mapped_column(ForeignKey("kunde.kd_nr"))                     
    fk_shop:Mapped[int]=mapped_column(ForeignKey("shop.shop_nr"))                   

class Bestellposition(db.Model):
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

class Kunde_list(Resource):        #Liste aller Kunden generieren
    @cache.cached(timeout=60)      #routenspezifisches Caching --> Erneuerung des Cache alle 60 Sekunden
#    @jwt_required()
    def get(self):                              #Service Initialisierung   
        now = datetime.utcnow().isoformat()
        print(f"Uhrzeit der Generierung des Cache: {now}")
#        current_user = get_jwt_identity()

        #eigentlicher Service startet hier
        kunden=Kunde.query.all() 
        return [{'kd_nr':kunde.kd_nr, 'vorname':kunde.vorname}for kunde in kunden]
    


class Kunde_add(Resource):              #Kunde hinzufügen
    #@cache.cached(timeout=60)            #Cache und JWT auskommentiert zum testen
    #@jwt_required()
    
    def post(self):
        data=request.get_json()     #hier wird die gesamte im URL-Body mitgeteilte JSON entgegengenommen
                        
        neue_kd_nr=db.session.query(func.max(Kunde.kd_nr)).scalar()+1    #neue KD-Nr wird generiert
        letzter_zugriff_aktuell=datetime.utcnow().isoformat()            #letzter Zugriff wird generiert
      
        kunde_neu=Kunde(
                kd_nr=neue_kd_nr,
                vorname=data['vorname'],
                nachname=data['nachname'],
                strasse=data['strasse'],
                plz=data['plz'],
                ort=data['ort'],
                vorwahl=data['vorwahl'],
                telefon=data['telefon'],
                geburtsdatum=data['geburtsdatum'],
                ledig=data['ledig'],
                rabatt=data['rabatt'],
                letzter_zugriff=letzter_zugriff_aktuell)
        db.session.add(kunde_neu)                                           #Insert-Statement wird der Session hinzugefügt
        db.session.commit()                                                 #Session wird commited
        print(f"Kunde -{neue_kd_nr}- angelegt")
        return {"message": "Alles erstellt."}, 201

class Service_A(Resource):          
    #Aus irgendeinem Shop geht eine Bestellung ein. 
    #    1. Überprüfung, ob der Kunde bereits existiert. 
    #    2. ggf. Kunden anlegen. Auf jeden Fall: Auftrag und Bestellungen anpassen
    def post(self):

        data=request.get_json()                 #daten aus JSON-Body auslesen
        
        neue_kd_nr=db.session.query(func.max(Kunde.kd_nr)).scalar()+1               #neue kd_nr -> 1 höher als die aktuell höchste
        neue_auft_nr=db.session.query(func.max(Auftrag.auft_nr)).scalar()+1         #neue auft_nr -> 1 höher als die aktuell höchste
        aktuelle_zeit=datetime.utcnow().isoformat()                                 #aktuelle_zeit
        aktuelles_datum=date.today()                                                #aktuelles_datum
       
        kunde_data=data.get("kunde")                                                #data wird objekt-bezogen ausgelesen 
        auftrag_data=data.get("auftrag")
        bestellpositionen_data=data.get("bestellpositionen")
        
        #Folgendes ist für die Prüfung, ob ein Kunde mit gleichem vor-, nachnamen sowie geburtsdatum existiert.
        kunde_exist=db.session.query(Kunde).filter((Kunde.vorname==kunde_data['vorname']) & (Kunde.nachname==kunde_data['nachname']) & (Kunde.geburtsdatum==kunde_data['geburtsdatum']))  #Statement zur Überprüfung, ob vorname existiert
        k_exist=db.session.query(kunde_exist.exists()).scalar() #hier werden drei unterabfragen abgrafragt. Sollte in allen reihen etwas gefunden wrden, so wird mittels scalar() als True zurückgegeben
        kd_nr_aktu=db.session.query(Kunde.kd_nr).filter((Kunde.vorname==kunde_data['vorname']) & (Kunde.nachname==kunde_data['nachname']) &(Kunde.geburtsdatum==kunde_data['geburtsdatum'])).scalar()
        #aktuelle KD-NR des existierenden Kunden mit vorname, nachname und geburtsdatum
        if k_exist:         #==True
            print(f"Kunde with {kunde_data['vorname']}, {kunde_data['nachname']}, born in {kunde_data['geburtsdatum']} DOES already EXIST with kd_nr: {kd_nr_aktu}.")
            auftrag_neu=Auftrag(
                auft_nr=neue_auft_nr,
                bestelldat=aktuelles_datum,
                lieferdat=aktuelles_datum+timedelta(days=1),
                zahlungsziel=aktuelles_datum+timedelta(days=21),
                zahlungseingang=aktuelles_datum,
                mahnung=0,
                fk_kunde=kd_nr_aktu,
                fk_shop=auftrag_data['fk_shop']                      
                )
            db.session.add(auftrag_neu)
            print(f"New Auftrag with auft_nr. {neue_auft_nr} was created") 
            
            for best_position in bestellpositionen_data:
                bestellposition_neu = Bestellposition(
                fk_auftrag=neue_auft_nr,
                fk_artikel=best_position['fk_artikel'],
                position=best_position['position'],
                anzahl=best_position['anzahl']
                )
                db.session.add(bestellposition_neu)
            

            db.session.commit()
            print(f"New Bestellpositionen were created.")
            
            return {"message": "Alles erstellt außer Kunde."}, 201
 

        else:
            print(f"Kunde with {kunde_data['vorname']}, {kunde_data['nachname']}, born in {kunde_data['geburtsdatum']} DOES NOT EXIST.")
            kunde_neu=Kunde(
                kd_nr=neue_kd_nr,
                vorname=kunde_data['vorname'],
                nachname=kunde_data['nachname'],
                strasse=kunde_data['strasse'],
                plz=kunde_data['plz'],
                ort=kunde_data['ort'],
                vorwahl=kunde_data['vorwahl'],
                telefon=kunde_data['telefon'],
                geburtsdatum=kunde_data['geburtsdatum'],
                ledig=kunde_data['ledig'],
                rabatt=kunde_data['rabatt'],
                letzter_zugriff=aktuelle_zeit)
            db.session.add(kunde_neu)
            print(f"Kunde with kd_nr: {neue_kd_nr} was created.")
            
            auftrag_neu=Auftrag(
                auft_nr=neue_auft_nr,
                bestelldat=aktuelles_datum,
                lieferdat=aktuelles_datum+timedelta(days=1),
                zahlungsziel=aktuelles_datum+timedelta(days=21),
                zahlungseingang=aktuelles_datum,
                mahnung=0,
                fk_kunde=neue_kd_nr,
                fk_shop=auftrag_data['fk_shop']                      
                )
            db.session.add(auftrag_neu)
            print(f"New Auftrag with auft_nr. {neue_auft_nr} was created.")
            for best_position in bestellpositionen_data:
                bestellposition_neu = Bestellposition(
                fk_auftrag=neue_auft_nr,
                fk_artikel=best_position['fk_artikel'],
                position=best_position['position'],
                anzahl=best_position['anzahl']
                )
                db.session.add(bestellposition_neu)
            print(f"Bestellpositionen were created.") 
        

            db.session.commit()
            return {"message": "Alles erstellt mit Kunde."}, 201

   
class Get_max_kd_nr(Resource):
    def get(self):
        max_kd_nr = db.session.query(db.func.max(Kunde.kd_nr)).scalar()
        return {"kd_nr_max":max_kd_nr or 0}, 200



api.add_resource(Kunde_list, '/api/kunden/list')                 #gibt auskunft über alle Kunden {"kd_nr": XYZ, "vorname": "Maximilian"}
api.add_resource(Get_max_kd_nr, '/api/kunden/get_max_kd_nr')
api.add_resource(Kunde_add, '/api/kunden/add')
api.add_resource(Service_A, '/api/service/A')                    #eigentliche Service-Abfrage

if __name__== '__main__':
    app.run(debug=True)

