from flask import Flask, render_template, request, session, redirect, url_for
from pymongo import MongoClient
import subprocess
import flask_login
import os

app = Flask(__name__)
client = MongoClient('mongodb://localhost:27017/')
db = client.codewalk
login_manager = flask_login.LoginManager()
login_manager.init_app(app)
user = ''
SCRIPT_TEMPLATE_FOLDER = os.path.dirname(os.path.abspath(__file__)) + '/script_templates/'
SCRIPTS_MAIN_FOLDER = os.path.dirname(os.path.abspath(__file__)) + '/script_templates/'
USER_SCRIPT_FOLDER = os.path.dirname(os.path.abspath(__file__)) + '/scripts/'
USER_SCRIPT_MAIN_FOLDER = os.path.dirname(os.path.abspath(__file__)) + '/scripts/'

class User(flask_login.UserMixin):
    pass

@login_manager.user_loader
def user_loader(email):
    user = User()
    user.id = session['email']
    return user

@app.after_request
def after_request_func(response):
    try:
        script_file_obj.close()
    except:
        print("handling exception")
    return response

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    return render_template('dashboard.html')

@app.route('/python', methods=['GET', 'POST'])
def python():
    tasks = list(db.tasks.find().sort('date',-1))
    return render_template('python.html', tasks_list=tasks)

@app.route('/task/<string:task_title>', methods=['GET', 'POST'])
def task(task_title):
    task = list(db.tasks.find({"title":task_title}))[0]
    script_template_file = open(SCRIPT_TEMPLATE_FOLDER + str(task['_id']) + '.py', 'r')
    processed_template = "".join(script_template_file.readlines())
    object_id = list(db.tasks.find({"title":task_title}))[0].get('_id')
    if os.path.isfile(USER_SCRIPT_FOLDER+session['email']+"/"+str(object_id)+".py"):
        script_file = open(USER_SCRIPT_FOLDER+session['email']+"/"+str(object_id)+".py", 'r')
        processed_template = "".join(script_file.readlines())
    return render_template('task.html', task=task, script_template = processed_template)

@app.route('/submit', methods=['GET', 'POST'])
def submit():
    code_lines = request.form['code']
    task_title = request.form['task_tit']
    object_id = list(db.tasks.find({"title":request.form['task_tit']}))[0].get('_id')
    if not os.path.exists(USER_SCRIPT_FOLDER+session['email']):
        os.mkdir(USER_SCRIPT_FOLDER+session['email'])
    user_script_file = USER_SCRIPT_FOLDER+session['email']+"/"+str(object_id)+".py"
    script_file_obj = open(user_script_file, 'w+')
    script_file_obj.write(code_lines)
    script_file_obj = open(user_script_file, 'r')
    result = execute_logic(object_id)
    print("result:", result)
    return redirect(url_for('task', task_title=task_title))

def execute_logic(object_id):
    user_script_file = USER_SCRIPT_FOLDER+session['email']+"/"+str(object_id)+".py"
    script_file_obj = open(user_script_file, 'r')
    user_logic = "".join(script_file_obj.readlines())
    print("user_logic:",user_logic)
    script_main_file = SCRIPTS_MAIN_FOLDER+"/"+str(object_id)+"_main.py"
    script_main_obj = open(script_main_file, 'r')
    script_main_logic = "".join(script_main_obj.readlines())
    print("script_main:",script_main_logic)
    if(subprocess.call("python "+script_main_file+" 2 5") == 7):
        print('hel')
    else:
        print('nnnn')
    #result2 = subprocess.call("python "+script_main_file+" 2 5")
    #print("f:",result2)
    #print("typ2:",type(result2))
    return user_logic

@app.route('/login', methods=['GET', 'POST'])
def login():
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
            db.users._insert(session['user_info'])
            return render_template('login.html', msg = 'Registered Successfully! Please login')
        else:
            return render_template('register.html', msg = 'Password Doesn\'t matching!!!')

@app.route('/logout', methods=['GET', 'POST'])
@flask_login.login_required
def logout():
    flask_login.logout_user()
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.secret_key="afdoijaw23409aoj()_)(&%#$%)"
    app.run(debug=True, use_reloader=False)