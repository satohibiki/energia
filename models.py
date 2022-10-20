from email.policy import default
from flask_login import UserMixin
from __init__ import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))
    height = db.Column(db.Integer, default=170)
    weight = db.Column(db.Integer, default=60)
    total_energia = db.Column(db.Integer, default=0)
    ave_energia = db.Column(db.Integer, default=0)
    last_up_date = db.Column(db.DateTime)
    histories = db.relationship('History', backref='user', lazy=True)
    last_up_date = db.Column(db.DateTime)

class History(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    users_id = db.Column(db.String, db.ForeignKey('user.id'), nullable=False)
    energia = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime)
