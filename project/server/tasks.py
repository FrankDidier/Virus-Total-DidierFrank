import os
import time
from datetime import datetime, timedelta
import json

from celery import Celery

from flask import Flask
from celery import Celery

import virustotal3.core
from project.server.main.models import Task
from project.server.extensions import db,make_celery


# This is required since flask and celery run in different containers
app = Flask(__name__) 
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("POSTGRES_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

API_KEY = os.environ['VT_API']
fileinfo = virustotal3.core.Files(API_KEY)

app.config.update(CELERY_CONFIG={
    'broker_url': os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379"),
    'result_backend': os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379"),
})
celery = make_celery(app)



@celery.task(name="fetch_file_info",bind=True)
def fetch_file_info(self,hash,job_id):
    task = Task.query.filter_by(hash=hash,job_id=job_id).first()

    # check if hash has been saved before and is less than one day 
    existing_task = Task.query.filter(Task.results["data"].astext != "", Task.hash==hash, Task.created_at > datetime.now() - timedelta(days=1)).first()
    
    #Use existing data instead of api call
    if existing_task:
        task.results = existing_task.results
        db.session.commit()
        return task.results

    #use api call if no data exist in database
    try:
        results = fileinfo.info_file(hash)
        task.results = results
        db.session.commit()
        return results
    except virustotal3.errors.VirusTotalApiError as err:
        error_details = json.loads(err.message)
        if(error_details["error"]["code"] == "NotFoundError"):
            results = {"status": "error", "error_message":"File not found "}
        elif(error_details["error"]["code"] == "QuotaExceededError"):
            results = {"status": "error", "error_message":"API Quota exceeded will retry after 24 hours"}
            task.results = results
            db.session.commit()
            tomorrow = datetime.utcnow() + timedelta(days=1)
            raise self.retry(exc=err, countdown=tomorrow)
            return results
        else:
             results = {"status": "error", "error_message":"{}".format(error_details.message)}  
        task.results = results
        db.session.commit()
        return results
    except Exception as err:
        results = {"status": "error", "error_message": "{}".format(err)}
        task.results = results
        db.session.commit()
        return results
