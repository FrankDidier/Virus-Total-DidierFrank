# project/server/main/views.py

from celery import group
from flask import render_template, Blueprint, request, redirect,url_for
from project.server.extensions import db
from project.server.main.models import Task, Job
from project.server.tasks import fetch_file_info


main_blueprint = Blueprint("main", __name__,)


@main_blueprint.route("/", methods=["GET"])
def home():
    return render_template("main/home.html")

@main_blueprint.route('/upload', methods=['POST'])
def upload_file():
    uploaded_file = request.files['file']
    if uploaded_file.filename != '':
        job= Job()
        db.session.add(job)
        db.session.commit()
        #todo guad and handle exceptions
        data = uploaded_file.readlines()
        tasks = []
        for line in data:
            # query database to find any completed task from less than one day ago 
            # if present then created that task with the job id and results from the previous completed job
            # get_task = Task.query.filter_by(hash=hash).first()
            tasks.append(line.decode().strip()) #save list of hashes in array to use later
            task = Task(hash=line.decode().strip(), job_id=job.id)
            db.session.merge(task)
            db.session.commit()
        
        g = group(fetch_file_info.s(hash,job.id) for hash 
        in tasks) # create group
        result = g() # you may need to call g.apply_sync(), but this executes all tasks in group
        return redirect(url_for(".results",id=job.id))
    return redirect(url_for(".home"))


@main_blueprint.route("/results/<id>", methods=["GET"])
def results(id):
    job = Job.query.filter_by(id=id).first()
    if job:
        results = job.tasks
        return render_template("main/results.html" , results=results)
    else:
        return redirect(url_for(".home"))

