from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(30), nullable=False, default='therapist')
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    patients = db.relationship('Patient', backref='user', lazy='dynamic')
    games = db.relationship('Game', backref='creator', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_therapist(self):
        return self.role in ('therapist', 'admin')


class Patient(db.Model):
    __tablename__ = 'patients'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer)
    diagnosis = db.Column(db.Text)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    sessions = db.relationship('GameSession', backref='patient', lazy='dynamic')
    sensitivity = db.relationship('PatientSensitivity', backref='patient', uselist=False)


class Game(db.Model):
    __tablename__ = 'games'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    game_type = db.Column(db.String(50), nullable=False)
    thumbnail_url = db.Column(db.Text)
    config = db.Column(db.JSON, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class GameSession(db.Model):
    __tablename__ = 'game_sessions'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id', ondelete='CASCADE'))
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    started_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    ended_at = db.Column(db.DateTime(timezone=True))
    score = db.Column(db.Integer, default=0)
    metadata_ = db.Column('metadata', db.JSON)

    events = db.relationship('FingerEvent', backref='session', lazy='dynamic')
    game = db.relationship('Game')
    therapist = db.relationship('User')


class FingerEvent(db.Model):
    __tablename__ = 'finger_events'

    id = db.Column(db.BigInteger, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('game_sessions.id', ondelete='CASCADE'))
    timestamp = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    finger_index = db.Column(db.Integer, nullable=False)
    state = db.Column(db.Integer, nullable=False)
    landmark_x = db.Column(db.Float)
    landmark_y = db.Column(db.Float)
    landmark_z = db.Column(db.Float)
    confidence = db.Column(db.Float)


class SensitivityPreset(db.Model):
    __tablename__ = 'sensitivity_presets'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    difficulty_level = db.Column(db.String(50))
    sensitivities = db.Column(db.JSON, nullable=False)
    is_default = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class PatientSensitivity(db.Model):
    __tablename__ = 'patient_sensitivity'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id', ondelete='CASCADE'), unique=True)
    sensitivities = db.Column(db.JSON, nullable=False)
    based_on_preset = db.Column(db.Integer, db.ForeignKey('sensitivity_presets.id'))
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'))

    preset = db.relationship('SensitivityPreset')


class PlayerGameConfig(db.Model):
    __tablename__ = 'player_game_config'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id', ondelete='CASCADE'))
    game_id = db.Column(db.Integer, db.ForeignKey('games.id', ondelete='CASCADE'))
    sensitivities = db.Column(db.JSON, nullable=False, default=[50, 50, 50, 50, 50])
    finger_map = db.Column(db.JSON, nullable=False, default={"0": "jump", "1": "right", "2": "left", "3": "none", "4": "none"})
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (db.UniqueConstraint('patient_id', 'game_id'),)


class Sprite(db.Model):
    __tablename__ = 'sprites'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(30), nullable=False)  # player, platform, coin, enemy, background, other
    type = db.Column(db.String(20), nullable=False)       # pixelmap | image
    width = db.Column(db.Integer, nullable=False)
    height = db.Column(db.Integer, nullable=False)
    data = db.Column(db.JSON)           # pixelmap: { palette: [...], frames: [{ grid: [...] }] }
    image_url = db.Column(db.Text)      # image: URL to PNG/SVG
    frame_count = db.Column(db.Integer, default=1)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    creator = db.relationship('User')


class SensitivityHistory(db.Model):
    __tablename__ = 'sensitivity_history'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id', ondelete='CASCADE'))
    old_sensitivities = db.Column(db.JSON)
    new_sensitivities = db.Column(db.JSON, nullable=False)
    reason = db.Column(db.Text)
    changed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    changed_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
