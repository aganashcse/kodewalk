#!/usr/bin/python
from __future__ import division
from flask import Flask, render_template, request, session, redirect, url_for
from pymongo import MongoClient
from bson.objectid import ObjectId
from flask_mail import Mail, Message
from random import randint
import subprocess
import flask_login
import pdb
import os
import time
import threading

from helpers.helper import Db_helper
from helpers.helper import File_helper
from helpers.helper import Code_processor

app = Flask(__name__)
app.config["MAIL_SERVER"]='smtp.gmail.com'  
app.config["MAIL_PORT"] = 465     
app.config["MAIL_USERNAME"] = 'flask.ganesh@gmail.com'
app.config['MAIL_PASSWORD'] = 'slmvveqoktmewnyf'
app.config['MAIL_USE_TLS'] = False  
app.config['MAIL_USE_SSL'] = True  

client = MongoClient('mongodb://localhost:27017/')
db = client.kodewalk
db_helper = Db_helper(db)
file_helper = File_helper(db)
code_processor = Code_processor()
login_manager = flask_login.LoginManager()
login_manager.init_app(app)
user = ''
mail = Mail(app)
otp = randint(000000,999999)
SCRIPT_TEMPLATE_FOLDER = os.path.dirname(os.path.abspath(__file__)) + '/script_templates/'
USER_SCRIPT_FOLDER = os.path.dirname(os.path.abspath(__file__)) + '/scripts/'
BLOCKED_SCRIPTS = ['import', 'eval', 'from', 'exec', 'open']

class User(flask_login.UserMixin):
    pass

@login_manager.user_loader
def user_loader(email):
    user = User()
    user.id = session['email']
    return user

@app.before_request
def before_request_callback():
    session['pass_rate'] = session.get("pass_rate", -1)
    session['error'] = session.get("error", "")
    session['blocked'] = session.get("blocked", False)
    session['sample_input_list'] = session.get('sample_input_list', "")
    session['sample_output'] = session.get('sample_output', "")
    session['user_output'] = session.get('user_output', "")
    session['curr_try'] = session.get('curr_try', 1)
    session['local_run'] = session.get('local_run', False)

@app.after_request
def after_request_func(response):
    try:
        script_file_obj.close()
    except:
        print("handling exception")
    return response

def remove_id_key(list_of_dict):
    for dct in list_of_dict:
        if '_id' in dct.keys():
            del list_of_dict[list_of_dict.index(dct)]['_id']

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    session['admin_try'] = True
    if request.method=='GET':
        return render_template('login.html', msg = 'Only Admin users are allowed to login here! Please use \'user login\' if you are not admin')
    session['email']=request.form['email']
    email_dict = {"email": session['email']}
    user = db.admin_users.find_one(email_dict)
    if not user:
        return render_template('login.html', msg = 'Email doesn\'t exists! Please contact us if you want to be admin user!')
    if user['passwd'] != request.form['passwd']:
        return render_template('login.html', msg = 'Password is incorrect!')
    user = User()
    user.id = session['email']
    flask_login.login_user(user)
    print("need to go admin")
    return redirect(url_for('admin_page'))

@app.route('/admin_page', methods=['GET', 'POST'])
@flask_login.login_required
def admin_page():
    return render_template('admin.html')

@app.route('/dashboard', methods=['GET', 'POST'])
@flask_login.login_required
def dashboard():
    session['pass_rate'] = -1
    session['error'] = ""
    session['blocked'] = False
    session['sample_input_list'] = ""
    session['sample_output'] = ""
    session['user_output'] = ""
    return render_template('dashboard.html')

@app.route('/python', methods=['GET', 'POST'])
@flask_login.login_required
def python():
    session['pass_rate'] = -1
    session['error'] = ""
    session['blocked'] = False
    session['sample_input_list'] = ""
    session['sample_output'] = ""
    session['user_output'] = ""
    tasks = list(db.tasks.find().sort('date',-1))
    return render_template('python.html', tasks_list=tasks)

@app.route('/task/<string:task_title>', methods=['GET', 'POST'])
@flask_login.login_required
def task(task_title):
    task_dict = db_helper.find_doc_from_db(query_dict = {"title":task_title}, collection= 'tasks')
    task_object_id = db_helper.get_id_of_doc_from_db(query_dict={"title":task_title}, collection= 'tasks')
    user_object_id = db_helper.get_id_of_doc_from_db(query_dict={"email":session['email']}, collection = "users")
    if file_helper.is_user_script_exists(user_folder=user_object_id, script_file_name=task_object_id, local_run=session['local_run']):
        if session['local_run']:
            processed_code = file_helper.read_user_script(user_folder=user_object_id, script_file_name=task_object_id, local_run=True)
        else:
            processed_code = file_helper.read_user_script(user_folder=user_object_id, script_file_name=task_object_id)
    else:
        processed_code = file_helper.read_template_script(script_file_name=task_object_id)
        print("Template script loaded! User doesn't have any")
        print("pass rate should be printed:",session['pass_rate'])
        print("code blocked", session['blocked'])
    user_tries_list = db_helper.get_user_tries_list(user_object_id=user_object_id, task_object_id=task_object_id, collection = "points")
    print("user_tries_list:{}".format(user_tries_list))
    return render_template('task.html', task=task_dict, script_template = processed_code.decode("utf-8"), script_blocked=session['blocked'],\
         pass_rate=session['pass_rate'], error=session['error'], blocked_scripts=', '.join(BLOCKED_SCRIPTS),\
             sample_input_list=session['sample_input_list'], sample_output=session['sample_output'], user_output=session['user_output'],\
                 user_tries_list=user_tries_list)

@app.route('/submit', methods=['GET', 'POST'])
@flask_login.login_required
def submit():
    code_lines = request.form['code']
    task_title = request.form['task_tit']
    code_lines = code_lines.replace('    ', '\t')
    task_object_id = db_helper.get_id_of_doc_from_db(query_dict={"title":request.form['task_tit']}, collection="tasks")
    user_object_id = db_helper.get_id_of_doc_from_db(query_dict={"email":session['email']}, collection = "users")
    if not os.path.exists(USER_SCRIPT_FOLDER+str(user_object_id)):
        os.mkdir(USER_SCRIPT_FOLDER+str(user_object_id))
    if str(request.form['test_run']) == 'true':
        session['curr_try']=file_helper.write_user_script(user_folder= user_object_id, script_file_name=task_object_id, content=code_lines.encode('utf-8'), local_run=True)
    else:
        session['curr_try']=file_helper.write_user_script(user_folder= user_object_id, script_file_name=task_object_id, content=code_lines.encode('utf-8'))
    #handling unicode character below
    if code_processor.precheck_code_errors(code = code_lines):
        session['blocked'] = True
        return redirect(url_for('task', task_title=task_title))
    else:
        session['blocked'] = False
    if str(request.form['test_run']) == 'true':
        sample_input_list, sample_output, user_output, pass_rate, error, total_count = execute_sample_logic(task_object_id)
        session['sample_input_list'] = sample_input_list
        session['sample_output'] = sample_output
        session['user_output'] = user_output
        session['local_run'] = True
    else:
        pass_rate, error, total_count = execute_logic(task_object_id)
        session['sample_input_list'] = ""
        session['sample_output'] = ""
        session['user_output'] = ""
        session['local_run'] = False
        db_helper.save_score_db(user_object_id=user_object_id, task_object_id=task_object_id, score=round((pass_rate/total_count*100), 2), curr_try= session['curr_try'])
    session['pass_rate'] = pass_rate/total_count*100
    print("pass_count:", pass_rate)
    print("total_cnt:", total_count)
    print("pass_rate:", session['pass_rate'])
    print("curr_try:", session['curr_try'])
    if error:
        session['error'] = code_processor.postcheck_code_errors(error=error, user_folder= user_object_id, script_file_name=task_object_id, local_run=session['local_run'])
    else:
        session['error'] = ""
    return redirect(url_for('task', task_title=task_title))

def execute_sample_logic(task_object_id):
    user_object_id = db_helper.get_id_of_doc_from_db(query_dict={"email":session['email']}, collection = "users")
    user_script_file = USER_SCRIPT_FOLDER+str(user_object_id)+"/"+str(task_object_id)+".py"
    test_ip_op_dict = list(db.tasks.find({"_id":task_object_id}))[0]
    pass_count = 0
    total_count = 1
    process = subprocess.Popen("python "+user_script_file, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    test_input = '\n'.join(test_ip_op_dict['test_ip_op']['test1']['input'])
    print('test_ip_sample:', str(test_input))
    test_output = test_ip_op_dict['test_ip_op']['test1']['output']
    print('test_op_sample:',str(test_output))
    process.stdin.write(test_input)
    try:
        output, error = process.communicate()
    except Exception as e:
        print("Process takes longer time than usual\nException:",e)
        process.kill()
    if str(test_output) == output.strip():
        pass_count+=1
    print("sample_script_output:", output.strip())
    print("sample_script_error:", error)
    return test_ip_op_dict['test_ip_op']['test1']['input'], str(test_output), output.strip(), pass_count, error, total_count

def execute_logic(task_object_id):
    user_object_id = db_helper.get_id_of_doc_from_db(query_dict={"email":session['email']}, collection = "users")
    user_script_file = USER_SCRIPT_FOLDER+str(user_object_id)+"/"+str(task_object_id)+"_submission.py"
    test_ip_op_dict = list(db.tasks.find({"_id":task_object_id}))[0]
    pass_count = 0
    total_count = len(test_ip_op_dict['test_ip_op'].values())
    for test_ip_op in test_ip_op_dict['test_ip_op'].values():
        process = subprocess.Popen("python "+user_script_file, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        test_input = '\n'.join(test_ip_op['input'])
        print('test_ip:', test_input)
        test_output = test_ip_op['output']
        print('test_op:',str(test_output))
        process.stdin.write(test_input)
        try:
            output, error = process.communicate()
        except subprocess.TimeoutExpired:
            print("Process takes longer time than usual")
            process.kill()
        if str(test_output) == output.strip():
            pass_count+=1
        print("script_output:", output.strip())
        print("script_error:", error)
    return pass_count, error, total_count

@app.route('/login', methods=['GET', 'POST'])
def login():
    session['admin_try'] = False
    if request.method=='GET':
        return render_template('login.html')
    session['email']=request.form['email']
    email_dict = {"email": session['email']}
    user = db.users.find_one(email_dict)
    if not user:
        return render_template('login.html', msg = 'Email doesn\'t exists! Please register if new user!')
    if user['passwd'] != request.form['passwd']:
        return render_template('login.html', msg = 'Password is incorrect!')
    user = User()
    user.id = session['email']
    flask_login.login_user(user)
    return redirect(url_for('dashboard'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method=='GET':
        return render_template('register.html')
    else:
        session['email'] = request.form['email']
        session['user_info'] = {'email': str(session['email']), 'passwd': str(request.form['passwd']), 'uname': str(request.form['uname'])}
        re_passwd=request.form['re_passwd']
        if session['user_info']['passwd']==re_passwd:
            email_dict = {"email": session['email']}
            #handling if user(s) already exists
            for _ in db.users.find(email_dict):
                return render_template('register.html', msg = 'Email already used!!!')
            msg = Message('kodeWalk Account Verification', sender = app.config["MAIL_USERNAME"], recipients = [session['email']])  
            msg.body = "Welcome to KodeWalk - a code learning platform!\nPlease use "+str(otp)+" as otp for KodeWalk account verification"  
            mail.send(msg)
            return redirect(url_for('validate'))
        else:
            return render_template('register.html', msg = 'Password Doesn\'t matching!!!')

@app.route('/validate',methods=['GET', "POST"])
def validate():
    if request.method == 'GET':
        return render_template('validate_email.html')
    user_otp = request.form['otp']
    print("otps:{},{}".format(user_otp, otp))
    if otp == int(user_otp):
        db.users._insert(session['user_info'])
        print("redirecting to login.html")
        return render_template('login.html', msg = 'Registered Successfully! Please login')
    return render_template('validate_email.html', msg = 'OTP doesnot Matching!!!')

@app.route('/logout', methods=['GET', 'POST'])
@flask_login.login_required
def logout():
    session['admin_try'] = False
    flask_login.logout_user()
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.secret_key="afdoijaw23409aoj()_)(&%#$%)"
    app.run(debug=True, use_reloader=False, port=80, host='0.0.0.0')
