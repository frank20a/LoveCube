from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timedelta
from app import db


class Users(db.Model):
    __tablename__ = 'Users'
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(db.String(10), index=True, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(db.String(64), nullable=False)
    email: Mapped[str] = mapped_column(db.String(64), unique=True, nullable=False)
    hash: Mapped[str] = mapped_column(db.String(64), nullable=False)
    salt: Mapped[str] = mapped_column(db.String(16), nullable=False)


class Devices(db.Model):
    __tablename__ = 'Devices'
    id: Mapped[str] = mapped_column(db.String(6), primary_key=True, index=True)
    owner: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('Users.id'), nullable=False, index=True)
    bat_chrg_flag: Mapped[bool] = mapped_column(db.Boolean)
    bat_stby_flag: Mapped[bool] = mapped_column(db.Boolean)
    cmd: Mapped[int] = mapped_column(db.Integer, default=0)
    cmd_exp: Mapped[datetime] = mapped_column(db.DateTime, nullable=False, default=lambda: datetime.utcnow() + timedelta(minutes=5))
    btn1_action: Mapped[str] = mapped_column(db.String(64), default='')
    btn1_action: Mapped[str] = mapped_column(db.String(64), default='')
    

class Pairs(db.Model):
    __tablename__ = 'Pairs'
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    user: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('Users.id'), nullable=False, index=True)
    device: Mapped[str] = mapped_column(db.String(6), db.ForeignKey('Devices.id'), nullable=False, index=True)
    date: Mapped[datetime] = mapped_column(db.DateTime, nullable=False, default=datetime.utcnow)
    approved: Mapped[bool] = mapped_column(db.Boolean, nullable=False, default=False)


class AuthKeys(db.Model):
    __tablename__ = 'AuthKeys'
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    user: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('Users.id'), nullable=False, index=True)
    device: Mapped[str] = mapped_column(db.String(6), db.ForeignKey('Devices.id'), nullable=False, index=True)
    key: Mapped[str] = mapped_column(db.String(64), nullable=False)
    expiry: Mapped[datetime] = mapped_column(db.DateTime)
