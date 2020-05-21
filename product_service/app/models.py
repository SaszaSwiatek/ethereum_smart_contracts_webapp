from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine,or_


db = SQLAlchemy()


def init_app(app):
    db.app = app
    db.init_app(app)
    return db


def create_tables(app):
    engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
    db.metadata.create_all(engine)
    return engine


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    image = db.Column(db.String(255), unique=False, nullable=True)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, onupdate=datetime.utcnow)

    def to_json(self):
        return {
            'id' : self.id,
            'name': self.name,
            'slug': self.slug,
            'price': self.price,
            'image': self.image
        }


class Contract(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    contractor_user_id = db.Column(db.Integer, nullable=False)#db.CheckConstraint('contractor_user_id<>user_id'),
    contract_template_id = db.Column(db.Integer, nullable=False, default=1)
    title = db.Column(db.String(255), nullable=False)
    value = db.Column(db.Integer, nullable=False)
    duedate = db.Column(db.DateTime, nullable=False)#db.CheckConstraint('duedate>sysdate')
    content = db.Column(db.String(255), nullable=False)
    contractor_approval = db.Column(db.Boolean, default=False)
    contractor_approval_timestamp = db.Column(db.DateTime)
    is_deployed = db.Column(db.Boolean, default=False)
    deployment_timestamp = db.Column(db.DateTime)
    transaction_hash = db.Column(db.String(255))
    is_finalized = db.Column(db.Boolean, default=False)
    finalization_timestamp = db.Column(db.DateTime)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, onupdate=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False)
    deleted_timestamp = db.Column(db.DateTime)

    def to_json(self):
        return {
            'id' : self.id,
            'user_id' : self.user_id,
            'contractor_user_id': self.contractor_user_id,
            'contract_template_id': self.contract_template_id,
            'title': self.title,
            'value' : self.value,
            'duedate' : self.duedate.timestamp(),
            'content': self.content,
            'contractor_approval': self.contractor_approval,
            'contractor_approval_timestamp' : self.contractor_approval_timestamp.timestamp() if self.contractor_approval_timestamp is not None else self.contractor_approval_timestamp,
            'date_added' : self.date_added.timestamp(),
            'date_updated' : self.date_updated.timestamp() if self.date_updated is not None else self.date_updated,
            'is_deployed': self.is_deployed,
            'deployment_timestamp' : self.deployment_timestamp.timestamp() if self.deployment_timestamp is not None else self.deployment_timestamp,
            'is_finalized' : self.is_finalized,
            'finalization_timestamp' : self.finalization_timestamp.timestamp() if self.finalization_timestamp is not None else self.finalization_timestamp,
            'transaction_hash' : self.transaction_hash,
            'is_deleted': self.is_deleted,
        }




class Attachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), unique=False, nullable=False)
    name = db.Column(db.String(255), unique=False, nullable=False)
    type_id = db.Column(db.Integer,default=1)
    contract_id = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(999), unique=False, nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, onupdate=datetime.utcnow)

    def to_json(self):
        return {
            'id' : self.id,
            'filename' : self.filename,
            'name': self.name,
            'description': self.description,
            'contract_id' : self.contract_id,
        }

class Attachment_type(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=False, nullable=False)
    description = db.Column(db.String(999), unique=False, nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, onupdate=datetime.utcnow)

    def to_json(self):
        return {
            'id' : self.id,
            'name' : self.name,
            'description': self.description,
        }

class Contract_template(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=False, nullable=False)
    code = db.Column(db.UnicodeText(99999) , unique=False, nullable=False)
    arguments = db.Column(db.UnicodeText(9999), unique=False, nullable=False)
    content = db.Column(db.String(255), unique=False, nullable=False)
    description = db.Column(db.String(999), unique=False, nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, onupdate=datetime.utcnow)

    def to_json(self):
        return {
            'id' : self.id,
            'code' : self.code,
            'arguments': self.arguments,
            'content': self.content,
            'description': self.description
        }