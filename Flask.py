from flask import Flask, Response, render_template,request,redirect, url_for
import cv2
from PIL import Image, ImageDraw, ImageFont
import time
import pymysql
import schedule
import atexit
from threading import Thread
import numpy as np
from flask import request
import tracker
from detector import Detector
import os


os.environ["KMP_DUPLICATE_LIB_OK"]  =  "TRUE"

def onlysql(sql):
    cursor.execute(sql)
    conn.commit()

def sql2(sql,result):
    nowTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    value = {"count": result, "ptime": nowTime}
    cursor.execute(sql, value)
    conn.commit()

class VideoCamera(object):
    def __init__(self):
        self.video = cv2.VideoCapture(0)
    def __del__(self):
        self.video.release()
    def get_frame(self):
        success, image = self.video.read()
        return success, image

class VideoCamera2(object):
    def __init__(self, video_path):
        self.video = cv2.VideoCapture(video_path)
        # self.video = cv2.VideoCapture(r'video\car-data.mp4')
    def __del__(self):
        self.video.release()
    def get_frame(self):
        success, image = self.video.read()
        return success, image

app = Flask(__name__,static_folder='')
def run_flask():
    app.run(host='0.0.0.0', threaded=True)
# 读取用户数据
def read_user_data():
    user_data = {}
    with open('templates/user.txt', 'r') as f:
        for line in f:
            username, password = line.strip().split(',')
            user_data[username] = password
    return user_data

# 写入用户数据
def write_user_data(username, password):
    with open('templates/user.txt', 'a') as f:
        f.write(f'{username},{password}\n')
        # f.write('\n')  # 写入换行符

# 初始化用户数据
user_database = read_user_data()


def genWeb(camera):
    mask_image_temp = np.zeros((1080, 1920), dtype=np.uint8)

    # 初始化2个撞线polygon
    list_pts_blue = [[204, 305], [227, 431], [605, 522], [1101, 464], [1900, 601], [1902, 495], [1125, 379], [604, 437],
                     [299, 375], [267, 289]]
    # list_pts_blue = [[0, 500], [2000, 500], [2000, 530], [0, 530]]  ##矩形检测区域
    ndarray_pts_blue = np.array(list_pts_blue, np.int32)
    polygon_blue_value_1 = cv2.fillPoly(mask_image_temp, [ndarray_pts_blue], color=1)
    polygon_blue_value_1 = polygon_blue_value_1[:, :, np.newaxis]

    # 填充第二个polygon
    mask_image_temp = np.zeros((1080, 1920), dtype=np.uint8)
    list_pts_yellow = [[181, 305], [207, 442], [603, 544], [1107, 485], [1898, 625], [1893, 701], [1101, 568],
                       [594, 637], [118, 483], [109, 303]]
    # list_pts_yellow = [[0, 535], [2000, 535], [2000, 565], [0, 565]]
    ndarray_pts_yellow = np.array(list_pts_yellow, np.int32)
    polygon_yellow_value_2 = cv2.fillPoly(mask_image_temp, [ndarray_pts_yellow], color=2)
    polygon_yellow_value_2 = polygon_yellow_value_2[:, :, np.newaxis]

    # 撞线检测用mask，包含2个polygon，（值范围 0、1、2），供撞线计算使用
    polygon_mask_blue_and_yellow = polygon_blue_value_1 + polygon_yellow_value_2

    # 缩小尺寸，1920x1080->960x540
    polygon_mask_blue_and_yellow = cv2.resize(polygon_mask_blue_and_yellow, (960, 540))

    # 蓝 色盘 b,g,r
    blue_color_plate = [255, 0, 0]
    # 蓝 polygon图片
    blue_image = np.array(polygon_blue_value_1 * blue_color_plate, np.uint8)

    # 黄 色盘
    yellow_color_plate = [0, 255, 255]
    # 黄 polygon图片
    yellow_image = np.array(polygon_yellow_value_2 * yellow_color_plate, np.uint8)

    # 彩色图片（值范围 0-255）
    color_polygons_image = blue_image + yellow_image
    # 缩小尺寸，1920x1080->960x540
    color_polygons_image = cv2.resize(color_polygons_image, (960, 540))

    # list 与蓝色polygon重叠
    list_overlapping_blue_polygon = []

    # list 与黄色polygon重叠
    list_overlapping_yellow_polygon = []

    # 进入数量
    global up_count
    # 出去数量
    global down_count
    # 初始化 yolov5
    detector = Detector()

    # 设置时间间隔7s
    schedule.every(7).seconds.do(job)

    while True:
        _, im = camera.get_frame()
        if im is None:
            break
        im = cv2.resize(im, (960, 540))
        list_bboxs = []
        bboxes = detector.detect(im)
        if len(bboxes) > 0:
            list_bboxs = tracker.update(bboxes, im)
            # 画框
            # 撞线检测点，(x1，y1)，y方向偏移比例 0.0~1.0
            output_image_frame = tracker.draw_bboxes(im, list_bboxs, line_thickness=None)
            pass
        else:
            # 如果画面中 没有bbox
            output_image_frame = im
        pass
        output_image_frame = cv2.add(output_image_frame, color_polygons_image)
        if len(list_bboxs) > 0:
            # ----------------------判断撞线----------------------
            for item_bbox in list_bboxs:
                x1, y1, x2, y2, label, track_id = item_bbox

                # 撞线检测点，(x1，y1)，y方向偏移比例 0.0~1.0
                y1_offset = int(y1 + ((y2 - y1) * 0.6))

                # 撞线的点
                y = y1_offset
                x = x1

                if polygon_mask_blue_and_yellow[y, x] == 1:
                    # 如果撞 蓝polygon
                    if track_id not in list_overlapping_blue_polygon:
                        list_overlapping_blue_polygon.append(track_id)
                    pass

                    # 判断 黄polygon list 里是否有此 track_id
                    # 有此 track_id，则 认为是 外出方向
                    if track_id in list_overlapping_yellow_polygon:
                        # 外出+1
                        up_count += 1


                        print(
                            f'类别: {label} | id: {track_id} | 上行撞线 | 上行撞线总数: {up_count} | 上行id列表: {list_overlapping_yellow_polygon}')

                        # 删除 黄polygon list 中的此id
                        list_overlapping_yellow_polygon.remove(track_id)

                        pass
                    else:
                        # 无此 track_id，不做其他操作
                        pass

                elif polygon_mask_blue_and_yellow[y, x] == 2:
                    # 如果撞 黄polygon
                    if track_id not in list_overlapping_yellow_polygon:
                        list_overlapping_yellow_polygon.append(track_id)
                    pass

                    # 判断 蓝polygon list 里是否有此 track_id
                    # 有此 track_id，则 认为是 进入方向
                    if track_id in list_overlapping_blue_polygon:
                        # 进入+1
                        down_count += 1

                        print(
                            f'类别: {label} | id: {track_id} | 下行撞线 | 下行撞线总数: {down_count} | 下行id列表: {list_overlapping_blue_polygon}')

                        # 删除 蓝polygon list 中的此id
                        list_overlapping_blue_polygon.remove(track_id)

                        pass
                    else:
                        # 无此 track_id，不做其他操作
                        pass
                    pass
                else:
                    pass
                pass

            pass
            list_overlapping_all = list_overlapping_yellow_polygon + list_overlapping_blue_polygon
            for id1 in list_overlapping_all:
                is_found = False
                for _, _, _, _, _, bbox_id in list_bboxs:
                    if bbox_id == id1:
                        is_found = True
                        break
                    pass
                pass

                if not is_found:
                    # 如果没找到，删除id
                    if id1 in list_overlapping_yellow_polygon:
                        list_overlapping_yellow_polygon.remove(id1)
                    pass
                    if id1 in list_overlapping_blue_polygon:
                        list_overlapping_blue_polygon.remove(id1)
                    pass
                pass
            list_overlapping_all.clear()
            pass

            # 清空list
            list_bboxs.clear()

            pass
        else:
            # 如果图像中没有任何的bbox，则清空list
            list_overlapping_blue_polygon.clear()
            list_overlapping_yellow_polygon.clear()
            pass
        pass

        # 创建一个与 output_image_frame 相同高度、宽度为300的黑色区域
        black_region = np.zeros((output_image_frame.shape[0], 300, 3), dtype=np.uint8)

        # 将黑色区域和 output_image_frame 水平拼接
        output_image_with_black_region = np.hstack((output_image_frame, black_region))

        # 使用 Pillow 绘制文本
        imgtemp = Image.fromarray(output_image_with_black_region)  # 转换为PIL库可以处理的图片形式
        draw = ImageDraw.Draw(imgtemp)

        font_path = "./simsun.ttc"  # 字体文件路径
        font = ImageFont.truetype(font_path, 40)

        draw.text((980, 50), "出：", font=font, fill=(0, 0, 255))
        draw.text((980, 150), "入：", font=font, fill=(0, 0, 255))
        draw.text((960, 250), "流动密度：", font=font, fill=(0, 0, 255))
        num = up_count+down_count
        if num >= 0 and num <= 10:
            draw.text((1000, 310), "目标较少", font=font, fill=(0, 255, 0))
        elif num >= 11 and num <= 20:
            draw.text((1000, 310), "目标较多", font=font, fill=(255, 0, 0))
        else:
            draw.text((1000, 310), "目标拥挤", font=font, fill=(0, 0, 255))

        draw.text((1050, 42), str(up_count), font=font, fill=(255, 255, 255))
        draw.text((1050, 132), str(down_count), font=font, fill=(255, 255, 255))
        output_image_frame = np.array(imgtemp)  # 转换回OpenCV格式
        ret, jpeg = cv2.imencode('.jpg', output_image_frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
        schedule.run_pending()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/Related')
def Related():
    return render_template('Related.html')


@app.route('/camera')
def camera():
    return render_template("camera.html")

@app.route('/login')
def login():
    return render_template("login.html")

@app.route('/loginProcess', methods=['POST'])
def login_process():
    username = request.form.get('name')
    password = request.form.get('mm')

    # 验证用户输入的账号和密码是否正确
    if username in user_database and user_database[username] == password:
        # 登录成功，重定向到 Related.html 界面
        return redirect(url_for('Related'))
    else:
        # 登录失败，重定向回登录界面
        return redirect(url_for('login'))

@app.route('/register')
def register():
    return render_template("register.html")

@app.route('/registerprocess', methods=['POST'])
def register_process():
    username = request.form.get('name')
    password = request.form.get('mm')
    # 检查用户是否已经存在
    if username in user_database:
        return redirect(url_for('login'))  # 用户已存在，重定向回登录页面
    # 注册新用户并写入数据文件
    write_user_data(username, password)
    user_database[username] = password
    # 注册成功后返回登录界面
    return redirect(url_for('login', name=username, mm=password))

@app.route('/yolo')
def yolo():
    return render_template("yolo.html")

@app.route('/LocalVideo')
def LocalVideo():
    return render_template("LocalVideo.html")

@app.route('/video_feed')
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
        video_path = os.path.join('static', filename)
        video_path = os.path.join('E:/pythonproject/YOLOv5-Web-Flask/static', filename)
        uploaded_file.save(video_path)
        return Response(genWeb(VideoCamera2(video_path)),
                        mimetype='multipart/x-mixed-replace; boundary=frame')
    else:
        return '没有选择要上传的视频文件'



def job():
    global up_count
    global down_count
    global down_count_all
    global up_count_all
    down_count_all += down_count
    up_count_all += up_count
    sql = 'INSERT INTO DETECT(PICTURE,PTIME) VALUE(%(count)s,%(ptime)s);'
    result = "进来"+str(down_count)+"物体,"+"出去"+str(up_count)+"物体"
    sql2(sql, result)
    down_count = 0
    up_count = 0

if __name__ == '__main__':
    down_count_all = 0
    up_count_all = 0
    down_count = 0
    up_count = 0
    conn = pymysql.Connection(host='localhost', user='root', password='701203', port=3306, database='yolo', charset='utf8')
    cursor = conn.cursor()
    sql = "select * from information_schema.tables where table_name = 'detect';"
    onlysql(sql)
    # 表存在返回1,否则创建表
    if (cursor.execute(sql)):
        print("detect exists")
        if(input("create new table input (yes) or input other character :") == "yes"):
            sql = 'DROP TABLE DETECT'
            onlysql(sql)
            sql = 'CREATE TABLE DETECT(PICTURE CHAR (40),PTIME CHAR (25) PRIMARY KEY);'
            onlysql(sql)
            print("create new table detect")
        else:
            print("use original table detect")

    else:
        sql = 'CREATE TABLE DETECT(PICTURE CHAR (40),PTIME CHAR (25) PRIMARY KEY);'
        onlysql(sql)
        print("create table detect")
    app.run(host='0.0.0.0', threaded=True)
    if (down_count_all == 0 and up_count_all == 0):
        print("no one in or out")
        sql = 'INSERT INTO DETECT(PICTURE,PTIME) VALUE(%(count)s,%(ptime)s);'
        result = "没有人进出"
        sql2(sql, result)
    else:
        sql = 'INSERT INTO DETECT(PICTURE,PTIME) VALUE(%(count)s,%(ptime)s);'
        result = "总共进来" + str(down_count_all) + "物体," + "出去" + str(up_count_all) + "物体"
        sql2(sql, result)

        # 将数据库表导出，先配置my.ini文件
    file_path = 'E:/pythonproject/YOLOv5-Web-Flask/templates/test.xls'
    if os.path.exists(file_path):
        os.remove(file_path)
    sql = f"select * from yolo.detect into outfile '{file_path}';"
    cursor.execute(sql)
    conn.commit()
    cursor.close()
    conn.close()
