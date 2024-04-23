# CPU版本 基于YOLOv5的多物体跟踪检测与计数


-  Python 3.9.19。


## 功能
- 基于Flask框架与多个Html代码，实现web网页界面
- 实现摄像头实时检测与对上传的视频进行分析检测。
- 相关数据导入mysql数据库并在程序终止后导出为xls文件，文件保存在templates文件夹中，可在Flask.py 文件第400行修改保存路径
- 实现了出/入 分别计数。
- 实现了显示物体流动密度
- 默认是 南/北 方向检测，若要检测不同位置和方向，可在 Flask.py 文件第73行和82行，修改2个polygon的点。
- 默认检测类别：行人、自行车、小汽车、摩托车、公交车、卡车。
- 检测类别可在 detector.py 文件第60行修改。


## 运行环境

- python 3.9.10，pip 22.0.3+
- pytorch 1.12.1+cpu
- pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
- 链接数据库账户密码在Flask.py第368行修改


## 如何运行

# 第一步
cd YOLOv5-Web-Flask
pip install -r requirements.txt
pip install --upgrade scipy
# 第二步
python Flask.py


## 使用框架

- https://github.com/Sharpiless/Yolov5-deepsort-inference
- https://github.com/ultralytics/yolov5/
- https://github.com/ZQPei/deep_sort_pytorch
