from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User model for authentication"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    notebooks = db.relationship('Notebook', backref='owner', lazy=True, cascade='all, delete-orphan')
    jobs = db.relationship('Job', backref='owner', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


class Notebook(db.Model):
    """Notebook model for storing notebook data"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, default='')  # Legacy field for backward compatibility
    language = db.Column(db.String(50), default='python')
    folder = db.Column(db.String(500), default='/')  # Folder path for organization
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    cells = db.relationship('Cell', backref='notebook', lazy=True, cascade='all, delete-orphan', order_by='Cell.position')
    
    def __repr__(self):
        return f'<Notebook {self.name}>'


class Cell(db.Model):
    """Cell model for notebook cells"""
    id = db.Column(db.Integer, primary_key=True)
    notebook_id = db.Column(db.Integer, db.ForeignKey('notebook.id'), nullable=False)
    cell_type = db.Column(db.String(20), default='code')  # 'code', 'sql', or 'markdown'
    content = db.Column(db.Text, default='')
    position = db.Column(db.Integer, nullable=False)  # Order of cells in notebook
    output = db.Column(db.Text)  # Cached output from last execution
    error = db.Column(db.Text)  # Cached error from last execution
    execution_count = db.Column(db.Integer)  # Execution counter
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Cell {self.id} in Notebook {self.notebook_id}>'


class Job(db.Model):
    """Job model for scheduled tasks"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    notebook_id = db.Column(db.Integer, db.ForeignKey('notebook.id'), nullable=True)
    schedule = db.Column(db.String(100))  # Cron expression
    status = db.Column(db.String(50), default='inactive')  # active, inactive, running
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_run = db.Column(db.DateTime)
    next_run = db.Column(db.DateTime)
    
    notebook = db.relationship('Notebook', backref='jobs')
    executions = db.relationship('JobExecution', backref='job', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Job {self.name}>'


class JobExecution(db.Model):
    """Job execution history"""
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    status = db.Column(db.String(50), default='pending')  # pending, running, success, failed
    output = db.Column(db.Text)
    error = db.Column(db.Text)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<JobExecution {self.id} for Job {self.job_id}>'


class Catalog(db.Model):
    """Catalog for SQL data organization"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    schemas = db.relationship('Schema', backref='catalog', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Catalog {self.name}>'


class Schema(db.Model):
    """Schema (layer) within a catalog - e.g., bronze, silver, gold"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    catalog_id = db.Column(db.Integer, db.ForeignKey('catalog.id'), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    tables = db.relationship('Table', backref='schema', lazy=True, cascade='all, delete-orphan')
    
    __table_args__ = (db.UniqueConstraint('catalog_id', 'name', name='_catalog_schema_uc'),)
    
    def __repr__(self):
        return f'<Schema {self.name} in Catalog {self.catalog_id}>'


class Table(db.Model):
    """Table within a schema"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    schema_id = db.Column(db.Integer, db.ForeignKey('schema.id'), nullable=False)
    data = db.Column(db.Text)  # JSON serialized data
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('schema_id', 'name', name='_schema_table_uc'),)
    
    def __repr__(self):
        return f'<Table {self.name} in Schema {self.schema_id}>'
