from flask import Blueprint, redirect, render_template, request, session
from threading import Thread
from datetime import date
from website import app, auth, db, storage
import sys
import os
import tempfile
import random
import uuid
sys.path.append('C:/xampp/htdocs/LoGo/Lo-Go_Logo-on-the-go/web app/website/generator')

views = Blueprint('views', __name__)

@views.route('/', methods=['POST', 'GET'])
@views.route('/index', methods=['POST', 'GET'])
@views.route('/home', methods=['POST', 'GET'])
def index():
    try:
        logoData=[]
        userData=[]
        allLogos = db.get().val()
        allLogos = dict(allLogos)['logo']
        for user in allLogos.keys():
            for logo in allLogos[user].items():
                logoData.append(logo)
                userData.append(user)
    except Exception as e:
        print(e)
    if request.method == 'POST':
        id = str(uuid.uuid1())
        data = {
            "id":id,
            "name":request.form['name'],
            "email":request.form['email'],
            "subject":request.form['subject'],
            "message":request.form['message']
        }
        db.child('feedback').child(id).set(data)
        return redirect("/")
    return render_template("index.html", logos=logoData, users=userData)

@views.route('/feedback', methods=['POST', 'GET'])
def feedback():
    feedback = db.child('feedback').get()
    comments = []
    if feedback.val() != None:
        for comment in feedback.each():
            comments.append(comment.val())
    if request.method=='POST':
        if "deleteFeedback" in request.form:
            db.child('feedback').child(request.form['commentId']).remove()
            return redirect('/feedback')
    return render_template("feedback.html", comments=comments)

@views.route('/logo-details', methods=['POST', 'GET'])
def logo_details():
    try:
        logoComments = []
        profilePicture = None
        try:
            uid = auth.get_account_info(session['user'])['users'][0]['localId']
            profilePicture = storage.child(f'user/{uid}').get_url(None)
        except:
            pass
        logoFile = request.args['logo']
        logoData = db.child("logo").child(request.args['creator']).get()

        if request.method == 'POST':
            if "deleteComment" in request.form:
                db.child("comments").child(request.form['commentId']).remove()
                return redirect(request.url)
            if "deleteLogo" in request.form:
                for logo in logoData.each():
                    if logo.val()['file'] == logoFile:
                        comments = db.child("comments").get()
                        if comments.val() != None:
                            for comment in comments.each():
                                if comment.val()['logo']==logoFile:
                                    db.child("comments").child(comment.val()['id']).remove()
                db.child('logo').child(request.args['creator']).child(logoFile[:-4]).remove()
                return redirect("/")
            try:
                if len(request.form['commentTextArea'].strip()) !=0:
                    id = str(uuid.uuid1())
                    data={"id": id,
                        "user": uid,
                        "comment": request.form['commentTextArea'],
                        "logo": logoFile,
                        "rating": request.form['rate'],
                        "date":f"{date.today().strftime('%B')} {date.today().day}, {date.today().year}"}
                    db.child("comments").child(id).set(data)
                return redirect(request.url)
            except Exception as e: 
                print(e)
        for logo in logoData.each():
            if logo.val()['file'] == logoFile:
                comments = db.child("comments").get()
                if comments.val() != None:
                    for comment in comments.each():
                        if comment.val()['logo']==logoFile:
                            logoComments.append(comment.val())
                return render_template("logo-details.html",logo=logoFile, logoData=logo.val(),profilePicture=profilePicture,comments=logoComments)
    except Exception as e: 
        print(e)
        return redirect("/")
    

@views.route('/input-name', methods=['POST', 'GET'])
def input_name():
    try:
        return render_template("input/name.html")
    except:
        return redirect("/")
    
@views.route('/input-domain', methods=['POST', 'GET'])
def input_domain():
    try:
        session['name'] = request.form['name']
        session['slogan'] = request.form.get('slogan')
        return render_template("input/domain.html")
    except:
        return redirect("/")
    
@views.route('/input-subdomain', methods=['POST', 'GET'])
def input_subdomain():
    try:
        session['domain'] = request.form['domain']
        return render_template("input/subdomain.html",domain=session['domain'])
    except:
        return redirect("/")
    
    
@views.route('/input-gender', methods=['POST', 'GET'])
def input_gender():
    try:
        session['subdomain'] = request.form['subdomain']
        return render_template("input/gender.html", )
    except:
        return redirect("/")

@views.route('/input-class', methods=['POST', 'GET'])
def input_class():
    try:
        session['gender'] = request.form['gender']
        return render_template("input/class.html")
    except:
        return redirect("/")

@views.route('/input-age', methods=['POST', 'GET'])
def input_age():
    try:
        session['class'] = request.form['class']
        return render_template("input/age.html")
    except:
        return redirect("/")


@views.route('/input-color', methods=['POST', 'GET'])
def input_color():
    try:
        session['style'] = request.form['style']
        return render_template("input/color.html")
    except:
        return redirect("/")


@views.route('/input-style', methods=['POST', 'GET'])
def input_style():
    try:
        session['age'] = request.form['age']
        return render_template("input/style.html")
    except:
        return redirect("/")


@views.route('/output', methods=['POST', 'GET'])
def output():
    uid = auth.get_account_info(session['user'])['users'][0]['localId']
    firstlogo = storage.child(f"logo/{uid}/firstlogo.png").get_url(None)
    secondlogo = storage.child(f"logo/{uid}/secondlogo.png").get_url(None)
    if request.method == 'POST':
        if "logoOne" in request.form:
            filename = uuid.uuid1()
            storage.child(f"logo/{uid}/firstlogo.png").download(uid+".png")
            storage.child(f"logo/{str(filename)}.png").put(uid+".png")
            data={"created_by": get_user()['user']['username'],
                "date_created":f"{date.today().strftime('%B')} {date.today().day}, {date.today().year}",
                "file":f"{str(filename)}.png",
                'name':session['name'],
                'slogan':session['slogan'],
                'labels':{
                    'age':decodeAge(session['age']),
                    'gender':decodeGender(session['gender']),
                    'color':session['color'],
                    'style':session['style'],
                    'domain':decodeDomain(session['domain']),
                    'subdomain':decodeSubdomain(session['subdomain']),
                    'class':decodeClass(session['class'])
                }}
            db.child('logo').child(uid).push(data)
            os.remove(uid+".png")
            return redirect("/profile")
        if "logoTwo" in request.form:
            filename = uuid.uuid1()
            storage.child(f"logo/{uid}/secondlogo.png").download(uid+".png")
            storage.child(f"logo/{str(filename)}.png").put(uid+".png")
            data={"created_by": get_user()['user']['username'],
                "date_created":f"{date.today().strftime('%B')} {date.today().day}, {date.today().year}",
                "file":f"{str(filename)}.png",
                'name':session['name'],
                'slogan':session['slogan'],
                'labels':{
                    'age':decodeAge(session['age']),
                    'gender':decodeGender(session['gender']),
                    'color':session['color'],
                    'style':session['style'],
                    'domain':decodeDomain(session['domain']),
                    'subdomain':decodeSubdomain(session['subdomain']),
                    'class':decodeClass(session['class'])
                }}
            db.child('logo').child(uid).push(data)
            os.remove(uid+".png")
            return redirect("/profile")
    return render_template("output.html",firstlogo=firstlogo,secondlogo=secondlogo)


@views.route('/generating-logo', methods=['POST', 'GET'])
def generating_logo():
    session['color'] = request.form['color']

    from generate import generate_images

    t = Thread(target=generate_images)
    t.start()

    return render_template("loading.html")

@views.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        try:
            user = auth.sign_in_with_email_and_password(request.form['email'],request.form['password'])
            user = auth.refresh(user['refreshToken'])
            session['user'] = user['idToken']
            return redirect("/")
        except:
            print("could not login")

    return render_template("auth/login-page.html")

@views.route('/sign-up', methods=['POST', 'GET'])
def sign_up():
    if request.method == 'POST':
        try:
            if len(request.form['code'].strip()) !=0:
                if request.form['code']=='admin':
                    user = auth.create_user_with_email_and_password(request.form['email'],request.form['password'])
                    user = auth.refresh(user['refreshToken'])
                    session['user'] = user['idToken']
                    uid = auth.get_account_info(session['user'])['users'][0]['localId']
                    data = {"username": request.form['username'], "email": request.form['email'], "type":"admin"}
                    db.child("users").child(uid).set(data)
                    storage.child(f"user/{uid}").put("web app/website/static/assets/img/default-profile-photo.jpg")
                    return redirect("/")
                elif request.form['code']=='designer':
                    user = auth.create_user_with_email_and_password(request.form['email'],request.form['password'])
                    user = auth.refresh(user['refreshToken'])
                    session['user'] = user['idToken']
                    uid = auth.get_account_info(session['user'])['users'][0]['localId']
                    data = {"username": request.form['username'], "email": request.form['email'], "type":"designer"}
                    db.child("users").child(uid).set(data)
                    storage.child(f"user/{uid}").put("web app/website/static/assets/img/default-profile-photo.jpg")
                    return redirect("/")
            else:
                user = auth.create_user_with_email_and_password(request.form['email'],request.form['password'])
                user = auth.refresh(user['refreshToken'])
                session['user'] = user['idToken']
                uid = auth.get_account_info(session['user'])['users'][0]['localId']
                data = {"username": request.form['username'], "email": request.form['email'], "type":"user"}
                db.child("users").child(uid).set(data)
                storage.child(f"user/{uid}").put("web app/website/static/assets/img/default-profile-photo.jpg")
            return redirect("/")
        except:
            print("could not sign up")


    return render_template("auth/signup-page.html")

@views.route('/logout', methods=['POST', 'GET'])
def logout():
    session['user'] = None
    return redirect("/")

@views.route('/profile', methods=['POST', 'GET'])
def profile():
    logoData = []
    uid = auth.get_account_info(session['user'])['users'][0]['localId']
    profilePicture = storage.child(f'user/{uid}').get_url(None)
    logos = db.child("logo").child(uid).get()
    if logos.val() != None:  
        for logo in logos.each():
            logoData.append(logo.val())

    try:
        if request.method == "POST":
            uid = auth.get_account_info(session['user'])['users'][0]['localId']
            picture = request.files['file']
            temp = tempfile.NamedTemporaryFile(delete=False)
            picture.save(temp.name)
            storage.child(f"user/{uid}").put(temp.name)
            
            os.remove(temp.name)

            return redirect(request.url)
    except WindowsError:
        pass
    except Exception as e: 
            print(e)
            return redirect("/")

    return render_template("profile.html", profilePicture=profilePicture, logoData=logoData, creatorId=uid)

@app.context_processor
def get_logo_file():
    def getLogo(logo_name):
        return storage.child(f"logo/{logo_name}").get_url(None)
    return dict(get_logo_file=getLogo)

@app.context_processor
def get_user():
    user = None
    try:
        if session.get('user'):
            uid = auth.get_account_info(session['user'])['users'][0]['localId']
            user = dict(db.child("users").child(uid).get().val())
    except:
        print("couldnt get user data")
    return dict(user=user)

@app.context_processor
def get_other_users():
    def get_other_users(user_id):
        data = {
            "username": db.child("users").child(user_id).child("username").get().val(),
            "type": db.child("users").child(user_id).child("type").get().val(),
            "profilePicture": storage.child(f'user/{user_id}').get_url(None)
        }
        return data
    return dict(get_other_users=get_other_users)

def decodeGender(gender):
    if gender == '0':
        return 'Male'
    elif gender == '1':
        return 'Female'
    elif gender == '2':
        return 'Both'
    
def decodeClass(socialClass):
    if socialClass == '0':
        return 'All'
    elif socialClass == '1':
        return 'Lower'
    elif socialClass == '2':
        return 'Middle'
    elif socialClass == '3':
        return 'Upper'
    elif socialClass == '4':
        return 'Middle Upper'
    elif socialClass == '5':
        return 'Lower Middle'
    
def decodeAge(age):
    if age == '0':
        return 'All'
    elif age == '1':
        return '10-15'
    elif age == '2':
        return '15-20'
    elif age == '3':
        return '20-30'
    elif age == '4':
        return '30-40'
    elif age == '5':
        return '40-60'
    elif age == '6':
        return '60+'
    elif age == '7':
        return '20-50'
    
def decodeDomain(domain):
    if domain == '0':
        return 'Food & Natural Resources'
    elif domain == '1':
        return 'Technology'
    elif domain == '2':
        return 'Transportation'
    elif domain == '3':
        return 'Fashion & Accessories'
    elif domain == '4':
        return 'Sports'
    elif domain == '5':
        return 'Other'
    
def decodeSubdomain(subdomain):
    if subdomain == '0':
        return 'No Subdomain'
    elif subdomain == '100':
        return 'Fast Food'
    elif subdomain == '101':
        return 'Cafes'
    elif subdomain == '102':
        return 'Pizzerias'
    elif subdomain == '103':
        return 'Drinks'
    elif subdomain == '104':
        return 'Other'
    elif subdomain == '10':
        return 'Cameras'
    elif subdomain == '11':
        return 'Cell Phones'
    elif subdomain == '12':
        return 'Computers'
    elif subdomain == '13':
        return 'Speakers'
    elif subdomain == '14':
        return 'All'
    elif subdomain == '15':
        return 'Other'
    elif subdomain == '20':
        return 'Cars'
    elif subdomain == '21':
        return 'Motorcycles'
    elif subdomain == '22':
        return 'Bicycles'
    elif subdomain == '23':
        return 'Other'
    elif subdomain == '24':
        return 'All'
    elif subdomain == '30':
        return 'Classic'
    elif subdomain == '31':
        return 'Casual'
    elif subdomain == '32':
        return 'Shoes'
    elif subdomain == '33':
        return 'Sportswear'
    elif subdomain == '34':
        return 'Watches'
    elif subdomain == '35':
        return 'Bags'
    elif subdomain == '36':
        return 'All'
    elif subdomain == '37':
        return 'Other'
    elif subdomain == '40':
        return 'Football'
    elif subdomain == '41':
        return 'Basketball'
    elif subdomain == '42':
        return 'Tennis'
    elif subdomain == '43':
        return 'Swimming'
    elif subdomain == '44':
        return 'All'
    elif subdomain == '45':
        return 'Other'