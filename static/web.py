from flask import Flask,render_template,request,url_for

from jinja2 import Environment, PackageLoader

app = Flask(__name__,static_folder='')
app.config['DEBUG'] = True

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/Related')
def Related():
    return render_template('Related.html')

@app.route('/login')
def login():
    return render_template("login.html")

@app.route('/yolo')
def yolo():
    return render_template("yolo.html")


@app.route('/LocalVideo')
def LocalVideo():
    return render_template("LocalVideo.html")
    # return render_template("xuanzexiangce.html")

@app.route('/camera')
def camera():
    return render_template("camera.html")

if __name__ == '__main__':
    app.run(port=8080,host="127.0.0.1")