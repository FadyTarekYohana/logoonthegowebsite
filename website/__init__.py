from flask import Flask
import pyrebase

app = Flask(__name__)
app.config['SECRET_KEY'] = 'reb3bG[u@h{xuxUn7;-a]$D6*VqXLZ~L'

firebaseConfig = {
  'apiKey': "AIzaSyBnkuC3vbrhtJavSG0x1Ee1y0wwbdKrGbI",
  'authDomain': "logo-6d3e7.firebaseapp.com",
  'databaseURL': "https://logo-6d3e7-default-rtdb.firebaseio.com",
  'projectId': "logo-6d3e7",
  'storageBucket': "logo-6d3e7.appspot.com",
  'messagingSenderId': "324041777865",
  'appId': "1:324041777865:web:aae3b26cbcc95dc33b2318",
  'measurementId': "G-5F5N3JNJL4"
}

firebase = pyrebase.initialize_app(firebaseConfig)

auth = firebase.auth()
db = firebase.database()
storage = firebase.storage()

from .views import views

app.register_blueprint(views, url_prefix='/')

