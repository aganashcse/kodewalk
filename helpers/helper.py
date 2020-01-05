import os
from pathlib import Path
class Db_helper:
    def __init__(self, db):
        self.db = db

    def is_collection_exists_in_db(self, collection):
        print("collections available in db:{}".format(self.db.list_collection_names()))
        if collection in self.db.list_collection_names():
            return True
        return False

    def get_id_of_doc_from_db(self, query_dict, collection):
        if self.is_collection_exists_in_db(collection):
            print("getting id of query:{} in collection:{}".format(query_dict, collection))
        else:
            print("No Data Found!!")
        return list(self.db[collection].find(query_dict))[0].get('_id')
    
    def find_doc_from_db(self, query_dict, collection):
        if self.is_collection_exists_in_db(collection):
            print("reading doc of query:{} in collection:{}".format(query_dict, collection))
        else:
            print("No Data Found!!")
        try:
            return list(self.db[collection].find(query_dict))[0]
        except IndexError:
            return {}

    def get_user_tries_list(self, user_object_id, task_object_id, collection):
        user_points_dict = self.find_doc_from_db(query_dict={"user_object_id": str(user_object_id)}, collection=collection)
        try:
            return user_points_dict[str(task_object_id)]
        except KeyError:
            return []

    def get_max_score(self, user_object_id, task_object_id):
        user_points_dict = self.find_doc_from_db(query_dict={"user_object_id": str(user_object_id)}, collection='points')
        return user_points_dict[str(task_object_id)][-2]['score']

    def save_score_db(self, user_object_id, task_object_id, score, curr_try):
        if curr_try!=1:
            last_max_score = self.get_max_score(user_object_id, task_object_id)
            if score>last_max_score:
                self.db.points.update({"user_object_id": str(user_object_id), str(task_object_id): {'$elemMatch': {'try':\
                    {'$eq': curr_try}}}}, {'$set' : {str(task_object_id)+".$.score":score}})
                print("Score saved in db!!! as score:{} & last_max_score:{}".format(score, last_max_score))
            else:
                #need to delete last entry in the db with default score 0
                self.db.points.update({"user_object_id": str(user_object_id), str(task_object_id): {'$elemMatch': {'try':\
                    {'$eq': curr_try}}}}, {'$pop' : {str(task_object_id):1}})
                print("not a better score and so didn't saved in db! score:{} & last_max_score:{}".format(score, last_max_score))
        else:
            self.db.points.update({"user_object_id": str(user_object_id), str(task_object_id): {'$elemMatch': {'try':\
                    {'$eq': curr_try}}}}, {'$set' : {str(task_object_id)+".$.score":score}})
            print("1st Score saved in db!!! as score:{}".format(score))
        if curr_try>5:
            self.db.points.update({"user_object_id": str(user_object_id), str(task_object_id): {'$elemMatch': {'try':\
                {'$eq': curr_try}}}}, {'$pop' : {str(task_object_id):-1}})
            print("user tried more than 5 submissions!, removing 1st submission")

class File_helper:
    CURRENT_PATH = Path(os.path.dirname(os.path.abspath(__file__)))
    USER_SCRIPT_FOLDER = str(CURRENT_PATH.parent) + '/scripts/'
    SCRIPT_TEMPLATE_FOLDER = str(CURRENT_PATH.parent)+'/script_templates/'

    def __init__(self, db):
        self.db = db
        self.db_helper = Db_helper(db)

    def is_user_script_exists(self, user_folder, script_file_name, local_run=False):
        if local_run:
            user_script_file=File_helper.USER_SCRIPT_FOLDER+str(user_folder)+"/"+str(script_file_name)+".py"
        else:
            last_try = self.get_last_try(user_folder, script_file_name)
            user_script_file=File_helper.USER_SCRIPT_FOLDER+str(user_folder)+"/"+str(script_file_name)+"_submission.py"
            print("last try is: ", last_try)
        if os.path.isfile(user_script_file):
            print("user script file already exists!")
            return True
        return False
    
    def read_user_script(self, user_folder, script_file_name, local_run=False):
        if local_run:
            user_script_file = open(File_helper.USER_SCRIPT_FOLDER+str(user_folder)+"/"+str(script_file_name)+".py", 'r')
            print("Reading file:{}".format(File_helper.USER_SCRIPT_FOLDER+str(user_folder)+"/"+str(script_file_name)+".py"))
        else:
            print("Reading file:{}".format(File_helper.USER_SCRIPT_FOLDER+str(user_folder)+"/"+str(script_file_name)+"_submission.py"))
            user_script_file = open(File_helper.USER_SCRIPT_FOLDER+str(user_folder)+"/"+str(script_file_name)+"_submission.py", 'r')
        return "".join(user_script_file.readlines())

    def read_template_script(self, script_file_name):
        file_obj = open(File_helper.SCRIPT_TEMPLATE_FOLDER+str(script_file_name)+".py", 'r')
        print("Reading file:{}".format(File_helper.SCRIPT_TEMPLATE_FOLDER+str(script_file_name)+".py"))
        return "".join(file_obj.readlines())

    def write_user_script(self, user_folder, script_file_name, content, local_run=False):
        if not local_run:
            current_try = self.get_last_try(user_folder, script_file_name, db_write=True)+1
            user_script_file = File_helper.USER_SCRIPT_FOLDER+str(user_folder)+"/"+str(script_file_name)+"_submission.py"
        else:
            current_try = 0
            user_script_file = File_helper.USER_SCRIPT_FOLDER+str(user_folder)+"/"+str(script_file_name)+".py"   
        script_file_obj = open(user_script_file, 'w+')
        print("writing content of '{}' in file '{}".format(content, user_script_file))
        script_file_obj.write(content)
        return current_try

    def get_last_try(self, user_folder, script_file_name, db_write=False):
        if self.is_new_user(user_folder):
            if self.is_new_logic(user_folder, script_file_name):
                last_try = 0
                points_dict={"user_object_id": str(user_folder),\
                    str(script_file_name): [{'try': 1, 'file':str(script_file_name)+"_"+str(1)+".py", 'score':0}]}
                print("default points_dict:{}".format(points_dict))
                if db_write:
                    self.db.points.insert(points_dict)
        else:
            if self.is_new_logic(user_folder, script_file_name):
                last_try = 0
                print("Old user but new logic!")
                if db_write:
                    self.db.points.update({"user_object_id": str(user_folder)}, \
                        {'$set' : {str(script_file_name): [{'try': 1, 'file':str(script_file_name)+"_"+str(1)+".py", 'score':0}]}})
            else:
                user_points_dict = list(self.db.points.find({"user_object_id":str(user_folder)}))[0]
                last_try_dict = user_points_dict[str(script_file_name)][-1]
                print("last try dict:{}".format(last_try_dict))
                last_try = last_try_dict["try"]
                curr_try = last_try+1
                if db_write:
                    self.db.points.update({"user_object_id": str(user_folder)}, \
                        {'$push' : {str(script_file_name): {'try': curr_try, 'file':str(script_file_name)+"_"+str(curr_try)+".py", 'score':0}}})
        return last_try

    def is_new_user(self, user_object_id):
        if len(list(self.db.points.find({"user_object_id":str(user_object_id)})))==0:
            return True
        return False
    
    def is_new_logic(self, user_object_id, script_object_id):
        try:
            user_points_dict = list(self.db.points.find({"user_object_id":str(user_object_id)}))[0]
            if str(script_object_id) in list(user_points_dict.keys()):
                print("Old user and old logic")
                return False
            print("Old user but new logic")
            return True
        except IndexError:
            print("This is very new task for user!")
            return True
        

class Code_processor:
    BLOCKED_SCRIPTS = ['import', 'eval', 'from', 'exec', 'open']

    def precheck_code_errors(self, code):
        #This method helps to block the execution incase of unicode or blocked scripts
        try:
            print("user_code b4 processing:",str(code))
        except:
            Blocked = True
            print("unicode entered! Blocked:", Blocked)
            return Blocked
        if  [True for item in Code_processor.BLOCKED_SCRIPTS if item in str(code)]:
            Blocked = True
            print("blocked scripts entered! Blocked:", Blocked)
            return Blocked
        else:
            Blocked = False

    def postcheck_code_errors(self, error, user_folder, script_file_name, local_run):
        if local_run:
            user_script_file = File_helper.USER_SCRIPT_FOLDER+str(user_folder)+"/"+str(script_file_name)+".py"
        else:
            user_script_file = File_helper.USER_SCRIPT_FOLDER+str(user_folder)+"/"+str(script_file_name)+"_submission.py"
        return error.replace(user_script_file, "your script file")
