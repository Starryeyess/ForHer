from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func


class Period(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_date = db.Column(db.Date, nullable=False)
    # Duration is essential for highlighting the "End" on the calendar
    duration = db.Column(db.Integer, nullable=False, default=5) 
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))



class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    
    dob = db.Column(db.Date, nullable=True)
    avatar_url = db.Column(db.String(500), nullable=True) # For future photo upload
    
    
    avg_cycle_length = db.Column(db.Integer, default=28)
    avg_period_length = db.Column(db.Integer, default=5)
    luteal_phase_length = db.Column(db.Integer, default=14)
    
    
    tracking_mode = db.Column(db.String(50), default='Track Period') # 'Track', 'TTC', 'Pregnancy'
    
    
    contraception_method = db.Column(db.String(100), default='None')
    health_conditions = db.Column(db.String(500), default='') # Stored as comma-separated text
    
    
    periods = db.relationship('Period', backref='user', lazy=True)

class DailyLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Categories (Stored as comma-separated strings)
    physical = db.Column(db.String(500), default="")
    discharge = db.Column(db.String(100), default="")
    mood = db.Column(db.String(500), default="")
    digestion = db.Column(db.String(500), default="")
    flow = db.Column(db.String(100), default="") # Only for Menstrual Phase