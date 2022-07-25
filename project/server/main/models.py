from sqlalchemy.dialects.postgresql import JSON
from flask_hashids import HashidMixin, Hashids
from project.server.extensions import db
from datetime import datetime

# hashids = Hashids()

class Job(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  tasks = db.relationship('Task', backref='job')
  created_at = db.Column(db.DateTime, default=datetime.now)
   
class Task(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  hash = db.Column(db.String(80), nullable=False)
  job_id = db.Column(db.Integer, db.ForeignKey("job.id"), nullable=False)
  results = db.Column(JSON, nullable=True)
  created_at = db.Column(db.DateTime, default=datetime.now)

  def __init__(self, hash, job_id, results={}):
        self.hash = hash
        self.job_id = job_id
        self.results = results


