from flask import Flask, render_template, request, redirect
from pymongo import MongoClient
import pymongo
from datetime import datetime

app = Flask(__name__)

try:
    client = MongoClient('mongodb://tushardbuser:tushardbpass@ds045021.mongolab.com:45021/tushardb')
    # noinspection PyUnresolvedReferences
    print("Connected successfully!!!")
    db = client.tushardb
    collection = db.projects
    collection_user = db.users

except pymongo.errors.ConnectionFailure:
    print("Could not connect to MongoDB:")


@app.route('/')
def login():
    return render_template('Login.html', title='MultiTenant-Tenant SaaS')

@app.route('/login', methods=['POST'])
def user_login():
    user = request.form['user']
    pwd = request.form['pass']
    doc = collection_user.find_one({'userid': user})
    if pwd == doc['password']:
        print(doc['password']+" ==> Correct Password")
        return redirect("/"+user)
    else:
        print(pwd + " ==> Wrong Password")
        return redirect("/")

@app.route('/signup', methods=['POST'])
def user_signup():
    user = request.form['username']
    first = request.form['firstName']
    last = request.form['lastName']
    pwd = request.form['password']
    tenant = request.form['projectType']

    story = ["Story ID", "Story Title",  "Story Description", "Total Hours", "Remaining Hours", "Assigned To"]
    tasks = ["Task ID", "Task Name",  "Task Description", "Start Date", "Finish Date",  "Assigned To"]
    cards = ["Card Id", "Card Name",  "Card Description", "Assigned To", "Card Type"]

    if tenant == "Kanban":
        collection_user.insert({'userid': user, 'firstName': first, 'lastName': last, 'password': pwd, 'tenantType': tenant, 'fields': cards})
    elif tenant == "Scrum":
        collection_user.insert({'userid': user, 'firstName': first, 'lastName': last, 'password': pwd, 'tenantType': tenant, 'fields': story})
    else:
        collection_user.insert({'userid': user, 'firstName': first, 'lastName': last, 'password': pwd, 'tenantType': tenant, 'fields': tasks})
    return redirect('/'+user+'/project/'+tenant)

@app.route('/<user>/project/<tenant>', methods=['GET', 'POST'])
def create_project(user, tenant):
    if request.method == "GET":
        return render_template('Project.html', tenant=tenant, user=user)
    elif request.method == "POST":
        proj = request.form['projectName']
        start = request.form['startDate']
        end = request.form['endDate']
        owner = request.form['assignedTo']

        if tenant == 'Kanban':
            collection.insert({'userid': user, 'projectName': proj, 'startDate': start, 'endDate': end, 'assignedTo': owner, 'cards': []})
        elif tenant == 'Waterfall':
             collection.insert({'userid': user, 'projectName': proj, 'startDate': start, 'endDate': end, 'assignedTo': owner, 'tasks': []})
        else:
             collection.insert({'userid': user, 'projectName': proj, 'startDate': start, 'endDate': end, 'assignedTo': owner, 'burndown': request.form['burndown'], 'story': []})
        return redirect('/'+user)

@app.route('/<user>', methods=['GET'])
def dashboard(user):
    doc = collection.find_one({'userid': user})
    return render_template('Dashboard.html', doc=doc)

@app.route('/<user>/edit/<proj>/<id>', methods=['GET'])
def edit(user, proj, id):
    if proj == 'tasks':
        doc = collection.find_one({'userid': user, 'tasks': {"$elemMatch": {'taskId': id}}}, {'_id': 0, 'userid': 1, 'projectName': 1, 'tasks.$': 1})
        return render_template('Details.html', title='Edit Task', doc=doc)
    elif proj == 'cards':
        doc = collection.find_one({'userid': user, 'cards': {"$elemMatch": {'cardId': id}}}, {'_id': 0, 'userid': 1, 'projectName': 1, 'cards.$': 1})
        return render_template('Details.html', title='Edit Card', doc=doc)
    else:
        doc = collection.find_one({'userid': user, 'story': {"$elemMatch": {'storyId': id}}}, {'_id': 0, 'userid': 1, 'projectName': 1, 'story.$': 1})
        return render_template('Details.html', title='Edit Story', doc=doc)


@app.route('/<user>/update/<proj>', methods=['POST'])
def update(user, proj):
    if proj == "cards":
        collection.update({'userid': user, 'cards.cardId': request.form['cardId']},
                        {'$set': {'cards.$': {'cardId': request.form['cardId'], 'cardName': request.form['cardName'], 'cardDescription': request.form['cardDescription'],
                                            'assignedTo': request.form['assignedTo'], 'cardType': request.form['selectCard']}}})
    elif proj == "tasks":
        collection.update({'userid': user, 'tasks.taskId': request.form['taskId']},
                        {'$set': {'tasks.$': {'taskId': request.form['taskId'], 'taskName': request.form['taskName'], 'taskDescription': request.form['taskDescription'],
                                            'startDate': request.form['startDate'], 'finishDate': request.form['finishDate'], 'assignedTo': request.form['assignedTo'], 'taskType': request.form['selectTask']}}})
    else:
        collection.update({'userid': user, 'story.storyId': request.form['storyId']},
                        {'$set': {'story.$': {'storyId': request.form['storyId'], 'storyTitle': request.form['storyTitle'], 'storyDescription': request.form['storyDescription'],
                                            'totalHours': request.form['totalHours'], 'remainingHours': request.form['remainingHours'], 'assignedTo': request.form['assignedTo']}}})
    return redirect("/"+user)


@app.route('/<user>/delete/<proj>/<id>', methods=['GET'])
def delete(user, proj, id):
    if proj == "cards":
        collection.update({'userid': user, 'cards.cardId': id}, {'$pull': {'cards': {'cardId': id}}})
    elif proj == "tasks":
        collection.update({'userid': user, 'tasks.taskId': id}, {'$pull': {'tasks': {'taskId': id}}})
    else:
        collection.update({'userid': user, 'story.storyId': id}, {'$pull': {'story': {'storyId': id}}})
    return redirect("/"+user)

@app.route('/<user>/add/<proj>', methods=['GET', 'POST'])
def add(user, proj):
    if request.method == 'GET':
        doc = collection.find_one({'userid': user})
        return render_template('Add.html', doc=doc, proj=proj)
    elif request.method == 'POST':
        if proj == "cards":
            collection.update({'userid': user},
                        {'$push': {'cards': {'cardId': request.form['cardId'], 'cardName': request.form['cardName'], 'cardDescription': request.form['cardDescription'],
                                            'assignedTo': request.form['assignedTo'], 'cardType': request.form['selectCard']}}})
        elif proj == "tasks":
            collection.update({'userid': user},
                        {'$push': {'tasks': {'taskId': request.form['taskId'], 'taskName': request.form['taskName'], 'taskDescription': request.form['taskDescription'],
                                            'startDate': request.form['startDate'], 'finishDate': request.form['finishDate'], 'assignedTo': request.form['assignedTo'], 'taskType': request.form['selectTask']}}})
        else:
            collection.update({'userid': user},
                        {'$push': {'story': {'storyId': request.form['storyId'], 'storyTitle': request.form['storyTitle'], 'storyDescription': request.form['storyDescription'],
                                            'totalHours': request.form['totalHours'], 'remainingHours': request.form['remainingHours'], 'assignedTo': request.form['assignedTo']}}})
    return redirect("/"+user)


@app.route('/<user>/status', methods=['GET'])
def project_status(user):
    doc = collection.find_one({'userid': user})
    tenant = collection_user.find_one({'userid':user})
    if tenant['tenantType'] == 'kanban':
        a = [count_cardType(user, 'To Do'), count_cardType(user, 'In Progress'), count_cardType(user, 'In Review'), count_cardType(user, 'Done')]
        return render_template('Status.html', a=a, doc=doc)
    elif tenant['tenantType'] == 'waterfall':
        a = [count_taskType(user, 'Requested'), count_taskType(user, 'In Progress'), count_taskType(user, 'Completed')]
        return render_template('Status.html', a=a, doc=doc)
    else:
        days = count_weeks(doc['startDate'], doc['endDate'])
        weeks = int(days / 7)
        hours = count_hours(user)

        burn_down = int(doc['burndown']) * 5
        actual = []
        r_hours = hours[1]
        while r_hours > 0:
            actual.append(r_hours)
            r_hours -= burn_down
        initial = []
        t_hours = hours[0]
        while t_hours > 0:
            initial.append(t_hours)
            t_hours -= burn_down
        i = 0
        j = 1
        dataArray = []

        for item in actual:
            dataArray.append([i, item, initial[i]])
            i += 1
        if initial.__len__() > actual.__len__():
            for item in initial:
                if j > actual.__len__():
                   dataArray.append([j, 0, item])
                else:
                    pass
                j += 1
            dataArray.append([j, 0, 0])

        elif initial.__len__() < actual.__len__():
            for item in initial:
                if j > initial.__len__():
                    dataArray.append([j, item, 0])
                else:
                    pass
                j += 1
            dataArray.append([j, 0, 0])
        elif initial.__len__() == actual.__len__():
            dataArray.append([i, 0, 0])

        # Second Method
        # t = hours[0]
        # r = hours[1]
        # r1 = int(r/weeks)
        # t1 = int(t/weeks)
        # actual = []
        # initial = []
        # while r > 0:
        #     actual.append(r)
        #     r -= r1
        # while t > 0:
        #     initial.append(t)
        #     t -= t1
        # i = 0
        # j = 1
        # dataArray = []
        #
        # for item in actual:
        #     dataArray.append([i, item, initial[i]])
        #     i += 1
        #
        #
        # if initial.__len__() > actual.__len__():
        #     for item in initial:
        #         if j > actual.__len__():
        #            dataArray.append([j, 0, item])
        #         else:
        #             pass
        #         j += 1
        #     dataArray.append([j, 0, 0])
        #
        # elif initial.__len__() < actual.__len__():
        #     for item in initial:
        #         if j > initial.__len__():
        #             dataArray.append([j, item, 0])
        #         else:
        #             pass
        #         j += 1
        #     dataArray.append([j, 0, 0])
        # dataArray.append([i, 0, 0])

        return render_template('Status.html', doc=doc, dataArray=dataArray)

def count_weeks(sd, ed):
    date_format = "%Y-%m-%d"
    a = datetime.strptime(sd, date_format)
    b = datetime.strptime(ed, date_format)
    delta = b - a
    return delta.days

def count_hours(user):
    doc = collection.find_one({'userid': user}, {'_id': 0, 'story.remainingHours': 1, 'story.totalHours': 1})
    total_hours = 0
    remaining_hours = 0
    for item in doc['story']:
        remaining_hours += int(item['remainingHours'])
        total_hours += int(item['totalHours'])
    hours = [total_hours, remaining_hours]
    return hours

def count_cardType(user, type):
    doc = collection.aggregate([{'$match': {'userid': user}}, {'$unwind': '$cards'},
                               {'$match': {'cards.cardType': type}}, {"$group": {"_id": "$_id", "count": {"$sum": 1}}}])
    if doc['result']:
        for result in doc['result']:
            return result['count']
    else:
        return 0

def count_taskType(user, type):
    doc = collection.aggregate([{'$match': {'userid': user}}, {'$unwind': '$tasks'},
                               {'$match': {'tasks.taskType': type}}, {"$group": {"_id": "$_id", "count": {"$sum": 1}}}])
    if doc['result']:
        for result in doc['result']:
            return result['count']
    else:
        return 0

if __name__ == '__main__':
    app.run()
