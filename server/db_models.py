from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timedelta
from app import db


class User(db.Model):
    __tablename__ = 'Users'
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(db.String(10), index=True, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(db.String(64), nullable=False)
    email: Mapped[str] = mapped_column(db.String(64), unique=True, nullable=False)
    hash: Mapped[str] = mapped_column(db.String(64), nullable=False)
    salt: Mapped[str] = mapped_column(db.String(16), nullable=False)


class Device(db.Model):
    __tablename__ = 'Devices'
    id: Mapped[str] = mapped_column(db.String(6), primary_key=True, index=True)
    owner: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('Users.id'), nullable=False, index=True)
    nickname: Mapped[str] = mapped_column(db.String(32), nullable=True)
    bat_chrg_flag: Mapped[bool] = mapped_column(db.Boolean, nullable=True)
    bat_stby_flag: Mapped[bool] = mapped_column(db.Boolean, nullable=True)
    cmd: Mapped[int] = mapped_column(db.Integer, nullable=False, default=0)
    cmd_exp: Mapped[datetime] = mapped_column(db.DateTime, nullable=False, default=lambda: datetime.utcnow())
    btn1_action: Mapped[str] = mapped_column(db.String(64), nullable=False, default='')
    btn2_action: Mapped[str] = mapped_column(db.String(64), nullable=False, default='')
    last_ping: Mapped[datetime] = mapped_column(db.DateTime, nullable=False, default=lambda: datetime.fromtimestamp(0))
    

class Pair(db.Model):
    __tablename__ = 'Pairs'
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    user: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('Users.id'), nullable=False, index=True)
    device: Mapped[str] = mapped_column(db.String(6), db.ForeignKey('Devices.id'), nullable=False, index=True)
    created: Mapped[datetime] = mapped_column(db.DateTime, nullable=False, default=datetime.utcnow)
    approved: Mapped[bool] = mapped_column(db.Boolean, nullable=False, default=False)


class AuthKey(db.Model):
    __tablename__ = 'AuthKeys'
    key: Mapped[str] = mapped_column(db.String(64), nullable=False, index=True, primary_key=True, unique=True)
    user: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('Users.id'))
    device: Mapped[str] = mapped_column(db.String(6), db.ForeignKey('Devices.id'), nullable=True, index=True)
    is_user_key: Mapped[bool] = mapped_column(db.Boolean, nullable=False, default=False)
    created: Mapped[datetime] = mapped_column(db.DateTime, nullable=False, default=datetime.utcnow)
