from flask import Flask
from flask_restful import Resource, Api
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
api = Api(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres_nutzer:postgres_pw@host:port/db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False

db = SQLAlchemy(app)

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
    def get(self):
        kunden=kunde.query.all() 
        return[{'kd_nr':kunde.kd_nr, 'vorname':kunde.vorname}for kunde in kunden]

api.add_resource(kunde_list, '/kunden')
if __name__== '__main__':
    app.run(debug=True)

