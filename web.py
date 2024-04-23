from flask import Flask,render_template,request,url_for

from jinja2 import Environment, PackageLoader

app = Flask(__name__,static_folder='')
app.config['DEBUG'] = True

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/Related')
def Related():
    return render_template('Related.html',Related = 'stu-大数据-yolo')

@app.route('/login')
def login():
    return render_template("login.html")

@app.route('/yolo')
def yolo():
    return render_template("yolo.html")

@app.route('/LocalVideo')
def LocalVideo():
    return render_template("LocalVideo.html")

@app.route('/camera')
def camera():
    return render_template("camera.html")

@app.route('/loginProcess', methods=['POST'])
def login_process():
    username = request.form.get('name')
    password = request.form.get('mm')

    # 验证用户输入的账号和密码是否正确
    if username in user_database and user_database[username] == password:
        # 登录成功，重定向到 camera.html 界面
        return redirect(url_for('Related'))
    else:
        # 登录失败，重定向回登录界面
        return redirect(url_for('login'))

@app.route('/video_feed')
# def video_feed():
#     return render_template("1.html",video = Response(genWeb(VideoCamera()),
#                                                mimetype='multipart/x-mixed-replace; boundary=frame'))
def video_feed():
    return Response(genWeb(VideoCamera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_process' ,methods=['POST'])
def video_process():
    uploaded_file = request.files['videoFile']
    if uploaded_file.filename != '':
        # 确保文件名安全
        filename = 'Datatest.mp4'
        # 保存上传的视频文件，覆盖同名文件
        video_path = os.path.join('E:/pythonproject/YOLOv5-Web-Flask/static', filename)
        uploaded_file.save(video_path)
        return Response(genWeb(VideoCamera2(video_path)),
                        mimetype='multipart/x-mixed-replace; boundary=frame')
    else:
        return '没有选择要上传的视频文件'


if __name__ == '__main__':
    app.run(port=8080,host="127.0.0.1")