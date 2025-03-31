from app import app, db
from helper.helpers import ModelEncoder
from flask import request
from models.models import DiaryTasks
import json

@app.route("/diary", methods=['GET'])
def get_diary_tasks():
    content = request.args.get('content')
    if content is not None:
        tasks = DiaryTasks.query.filter(DiaryTasks.diary_shorthand.contains(content)).all()
    else:
        tasks = DiaryTasks.query.all()
    data = [task.serialize() for task in tasks]
    return json.dumps(data, cls=ModelEncoder)

@app.route("/diary/shorthands", methods=['GET'])
def get_diary_shorthands():
    tasks = DiaryTasks.query.all()
    # unique shorthands
    data = set()
    for task in tasks:
        data.add(task.diary_shorthand)
    data = list(data)
    return json.dumps(data, cls=ModelEncoder)

@app.route("/diary/categories", methods=['GET'])
def get_diary_categories():
    tasks = DiaryTasks.query.all()
    # Remove tasks with duplicate shorthands
    unique_tasks = {task.diary_shorthand: task for task in tasks}.values()
    data = []
    for task in unique_tasks:
        data.append({'diary_name': task.diary_name, 'shorthand': task.diary_shorthand, 'scale': task.scale})
        
    return json.dumps(data, cls=ModelEncoder)

@app.route("/diary", methods=['POST'])
def create_diary_task():
    data = DiaryTasks(**request.get_json())
    if data is None:
        return "No JSON received", 400
    task = DiaryTasks.query.filter_by(diary_name=data.diary_name).first()
    if task is not None:
        return "Task already exists", 400
    db.session.add(data)
    db.session.commit()
    return json.dumps(data.serialize(), cls=ModelEncoder)

@app.route("/diary/<id>", methods=['GET'])
def get_diary_task(id):
    task = DiaryTasks.query.filter_by(id=id).first()
    if task is None:
        return "Could not find Task", 404
    return json.dumps(task.serialize(), cls=ModelEncoder)

@app.route("/diary/<id>", methods=['PUT'])
def update_diary_task(id):
    data = DiaryTasks(**request.get_json())
    if data is None:
        return "No JSON received", 400
    task = DiaryTasks.query.filter_by(id=id).first()
    if task is None:
        return "Could not find Task", 404
    task.diary_name = data.diary_name
    task.diary_shorthand = data.diary_shorthand
    db.session.commit()
    return json.dumps(task.serialize(), cls=ModelEncoder)

@app.route("/diary/<id>", methods=['DELETE'])
def delete_diary_task(id):
    task = DiaryTasks.query.filter_by(id=id).first()
    if task is None:
        return "Could not find Task", 404
    db.session.delete(task)
    db.session.commit()
    return "Task deleted", 200
