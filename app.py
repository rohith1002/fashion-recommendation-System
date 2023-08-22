from enum import unique
from flask import Flask, flash, redirect,request, send_from_directory,url_for,render_template
from flask_sqlalchemy import SQLAlchemy
import os
import werkzeug
from werkzeug.security import generate_password_hash, check_password_hash
import numpy as np
import pickle
from keras.models import load_model
from tensorflow.keras.preprocessing.image import load_img
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.preprocessing.image import array_to_img
from numpy import asarray
import cv2
from tensorflow.keras.applications.resnet50 import preprocess_input
from tensorflow.keras.preprocessing import image
from tensorflow.keras.preprocessing.image import ImageDataGenerator,load_img
import tensorflow as tf
from flask_login import UserMixin
from flask_login import LoginManager,login_user,login_required,logout_user,current_user
from flask.json import jsonify
import wardrobe,recommender
from PIL import Image, ImageOps
import numpy as np
import re
import time
# fashion_model=tf.keras.models.load_model('models/fashion-010.model')
# color_model=tf.keras.models.load_model('models/fashion-colors-020.model')
color_model_2=load_model('models/keras_model.h5')
type_model_2=load_model('models/type_model.h5')


app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(12)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)
 
temp=None
next= -1
res=[[]]
colors_array=['black', 'blue', 'brown', 'green', 'grey', 'khaki', 'marron', 'orange', 'pink', 'red', 'white', 'yellow']
#type_array=['longsleeve','outwear','pants','shirt','shoes','t-shirt']
type_array=['shirt','shoes','pants','t-shirt']

def matching(arr,target):
    for i in range(len(arr)):
        if arr[i] == 1:
            return target[i]
def matching_2(arr,target):
    return 


class User(UserMixin,db.Model):
    __tablename__ = 'user'
    id=db.Column(db.Integer,primary_key=True)
    uname=db.Column(db.String(100),unique=True)
    password=db.Column(db.String(100),unique=True)
    def __repr__(self) -> str:
        return '<Name %r>' %self.id
    def to_json(self):        
        return {"name": self.uname,
                "ID": self.id}

    def is_authenticated(self):
        return True

    def is_active(self):   
        return True           

    def is_anonymous(self):
        return False          

    def get_id(self):         
        return str(self.id)
    
    def get_uname(self):
        return str(self.uname)


login_manager=LoginManager()
login_manager.init_app(app)
login_manager.login_view='login_result'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def hello_world():
    return render_template("index.html")

@app.route('/login')
def login():
    return render_template("login.html")

@app.route('/loginresult',methods=["POST"])
def login_result():
    name=request.form['uname']
    pwd=request.form['pwd']
    user=User.query.filter_by(uname=name).first()
    if not user or not check_password_hash(user.password,pwd):
        return render_template("login.html",pred="Enter correct Details")
    login_user(user,remember=True)
    #return render_template("loggedin.html",pred=user.to_json())
    return redirect(url_for('user_profile'))



@app.route('/logout')
@login_required
def logout():
    logout_user()
    #return jsonify(**{'result': 200,'data': {'message': 'logout success'}})
    return render_template("logout.html")
@app.route('/userprofile')
def user_profile():
    root=r"users/"+(current_user.get_uname())+"/"
    l=[]
    shirts=[]
    tshirts=[]
    pants=[]
    shoes=[]
    for path, subdirs, files in os.walk(root):
        path_type=(path.replace(root,"")).split("\\")[0]
        for name in files:
            if path_type=="shirt":
                shirts.append(((os.path.join(path, name)).replace("\\","/")).replace("users/",""))
            elif path_type=="pants":
                pants.append(((os.path.join(path, name)).replace("\\","/")).replace("users/",""))
            elif path_type=="t-shirt":
                tshirts.append(((os.path.join(path, name)).replace("\\","/")).replace("users/",""))
            elif path_type== "shoes":
                shoes.append(((os.path.join(path, name)).replace("\\","/")).replace("users/",""))
    return render_template("profile.html",lshirts=shirts,ltshirts=tshirts,lshoes=shoes,lpants=pants)        

@app.route('/updatedwardrobe',methods=["POST"])
def remove_item():
    item_list=request.form.getlist("cloth")
    if(len(item_list)==0):
        flash("Please select atleast one item that is to be removed.")
        return redirect(url_for('user_profile'))
    for item in item_list:
        path="users/"+item
        path_type=item.split("/")[1]
        print("Path type is ",path_type)
        if path_type=="shirt" or path_type=="t-shirt":
            creation_time=time.ctime(os.path.getctime(path))
            print(creation_time)
            party_path=r"users\{}\party\{}".format(current_user.get_uname(),item.split("/")[2])
            party_list=os.listdir(party_path)
            print("Party list is",party_list)
            for shirt in party_list:
                path_party_shirt=party_path+"\{}".format(shirt)
                print("Time of creation for {} is {}".format(shirt,int(os.path.getctime(path_party_shirt))))
                if (time.ctime(os.path.getctime(path_party_shirt)))==creation_time:
                    os.remove(path_party_shirt)
                    if(len(os.listdir(party_path))==0):
                        os.rmdir(party_path)

        os.remove(path)
        new_path=re.sub(r"/[\d].jpg","",path)
        if(len(os.listdir(new_path))==0):
            os.rmdir(new_path)
    #print(list)
    if len(item_list) > 1:
        flash("Items have been removed from the wardrobe")
    else:
        flash("Item has been removed from the wardrobe")
    return redirect(url_for('user_profile'))


@app.route('/signup')
def signup():
    return render_template("signup.html")

@app.route('/signupresult',methods=["POST"])
def signup_result():
    name=request.form['uname']
    pwd=request.form['pwd']
    user=User.query.filter_by(uname=name).first()
    print(user)
    if user:
        return render_template("signup.html",pred="User Already Exists")
    new_user = User(uname=name, password=generate_password_hash(pwd, method='sha256'))
    wardrobe.create_wardrobe(name)
    db.session.add(new_user)
    db.session.commit()
    return render_template("signup_res.html",pred="User has been created. Please sign in.")

@app.route('/logout')
def mogout():
    logout_user()
    return "<h1>Logged Out Successfully<h1>"

@app.route("/fashion")
@login_required
def fashion():
    cv2.imwrite("static/test.jpg",cv2.imread("static/station.jpg"))
    return render_template("fashion.html")

@app.route("/fashionpredict",methods=["POST"])
def fashion_predict():
    filestr = request.files['img'].read()
    npimg = np.fromstring(filestr, np.uint8)
    img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
    cv2.imwrite("static/test.jpg",img)
    # gray=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)           
    # resized=cv2.resize(gray,(100,100))
    # r=resized.reshape(1,100,100,1)
    # predict=fashion_model.predict(r).tolist()
    #predict2=color_model.predict(r).tolist()
    data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)
    # Replace this with the path to your image
    image = Image.open('static/test.jpg')
    #resize the image to a 224x224 with the same strategy as in TM2:
    #resizing the image to be at least 224x224 and then cropping from the center
    size = (224, 224)
    image = ImageOps.fit(image, size, Image.ANTIALIAS)
    #turn the image into a numpy array
    image_array = np.asarray(image)
    # Normalize the image
    normalized_image_array = (image_array.astype(np.float32) / 127.0) - 1
    # Load the image into the array
    data[0] = normalized_image_array
    predict=type_model_2.predict(data)
    predict=type_array[np.argmax(predict[0],axis=0)]
    predict2=color_model_2.predict(data)
    predict2=colors_array[np.argmax(predict2[0],axis=0)]
    #predict=matching(predict[0],type_array)
    #predict2=matching(predict2[0],colors_array)
    return render_template("fashion.html",pred=predict,pred2=predict2,image1="test.jpg")

@app.route('/upload',methods=["POST"])
def outfit_upload():
    try:
        filestr = request.files['img'].read()
        npimg = np.fromstring(filestr, np.uint8)
        img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
        cv2.imwrite("static/test.jpg",img)
    except:
        type=request.form["type"]
        color=request.form["color"]
    finally:
        type=request.form["type"]
        color=request.form["color"]
    #occasion=request.form["occasion"]
    #wardrobe.upload(occasion,type,color,"users/"+current_user.get_uname(),cv2.imread("static/test.jpg"))
    wardrobe.upload(type,color,"users/"+current_user.get_uname(),cv2.imread("static/test.jpg"))
    cv2.imwrite("static/test.jpg",cv2.imread("static/station.jpg"))
    return render_template("fashion.html",pred3="The image of your "+color+" "+type+" has been uploaded successfully.")

@app.route('/uploads/<path:filename>')
def download_file(filename):
    return send_from_directory("users/", filename, as_attachment=True)

@app.route('/select')
def select_clothes():
    global next
    next = 0
    recommender.clear()
    root=r"users/"+(current_user.get_uname())+"/"
    l=[]
    shirts=[]
    tshirts=[]
    pants=[]
    shoes=[]
    for path, subdirs, files in os.walk(root):
        print(files)
        print(subdirs)
        print(path)
        path_type=(path.replace(root,"")).split("\\")[0]
        for name in files:
            if path_type=="shirt":
                shirts.append(((os.path.join(path, name)).replace("\\","/")).replace("users/",""))
            elif path_type=="pants":
                pants.append(((os.path.join(path, name)).replace("\\","/")).replace("users/",""))
            elif path_type=="t-shirt":
                tshirts.append(((os.path.join(path, name)).replace("\\","/")).replace("users/",""))
            elif path_type== "shoes":
                shoes.append(((os.path.join(path, name)).replace("\\","/")).replace("users/",""))
            #l.append(((os.path.join(path, name)).replace("\\","/")).replace("users/",""))
   # print(l)
    #return render_template("display_clothes.html",img=l)
    print(shirts,tshirts,shoes,pants)
    return render_template("display_clothes.html",lshirts=shirts,ltshirts=tshirts,lshoes=shoes,lpants=pants)

@app.route('/recommend',methods=["POST"])
def recommend_combination():
    try:
        pred=(request.form["cloth"]).split("/")
        type=pred[1]
        color=pred[2]
        path=request.form["cloth"]
    except werkzeug.exceptions.BadRequestKeyError:
        type="None"
        color="None"
        path="None"
    occasion=request.form["occasion"]
    #print(pred)
    global next
    next=0
    global res
    res=[[]]
    res=recommender.execute(type,color,path,occasion,current_user.get_uname())
    print(res)
    print(next)
    #print(pred)
    return render_template("display_result.html",img=res[next])

@app.route('/recommendnext')
def recommend_next():
    global next
    next=next+1
    print("Value of next in recommend next:",next)
    global res
    try:
        mes=res[next]
        return render_template("display_result.html",img=mes)
    except IndexError:
        #flash("Reached end of list")
        return render_template("display_result.html",img=res[next-1],hiden="hidden1")

@app.route('/recommendprev')
def recommend_previous():
    global next
    next=next-1
    print("Value of next in recommend prev:",next)
    global res
    if(next>=0):
        mes=res[next]
        return render_template("display_result.html",img=mes)
    else:
        #flash("Reached end of list")
        return render_template("display_result.html",img=res[next+1],hiden="hidden2")

if __name__ == '__main__':
    # Create the tables
    with app.app_context():
        db.create_all()
    app.run(debug=True)