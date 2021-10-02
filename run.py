from flask import Flask
from flask import render_template
from flask import jsonify
from jieba.analyse import extract_tags
import utils
import string
from datetime import timedelta

app = Flask(__name__)
# 配置缓存时间，方便调试
app.config['DEBUG'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = timedelta(seconds=1)  # 将缓存时间设为1s


# 函数最后返回需要在用户浏览器中显示的信息
# 创建多个路由，返回多个不同数据
@app.route('/')
def hello_world():
    return render_template('main.html')


@app.route('/c1')
def get_center1_data():
    data = utils.get_center1_data()
    return jsonify({"confirm": data[0], "suspect": data[1], "heal": data[2], "dead": data[3]})


@app.route('/c2')
def get_center2_data():
    res = []
    for tup in utils.get_center2_data():
        res.append({"name": tup[0], "value": int(tup[1])})
    return jsonify({"data": res})


@app.route("/l1")
def get_left1_data():
    data = utils.get_left1_data()
    day, confirm, suspect, heal, dead = [], [], [], [], []
    for a, b, c, d, e in data[7:]:  # 很多卫健委网站前7天都是没有数据的，所以把前7天砍掉了
        day.append(a.strftime("%m-%d"))  # a是datatime类型
        confirm.append(b)
        suspect.append(c)
        heal.append(d)
        dead.append(e)
    return jsonify({"day": day, "confirm": confirm, "suspect": suspect, "heal": heal, "dead": dead})


@app.route("/l2")
def get_left2_data():
    data = utils.get_left2_data()
    day, confirm_add, suspect_add = [], [], []
    for a, b, c in data[7:]:
        day.append(a.strftime("%m-%d"))  # a是datatime类型
        confirm_add.append(b)
        suspect_add.append(c)
    return jsonify({"day": day, "confirm_add": confirm_add, "suspect_add": suspect_add})


@app.route("/r1")
def get_right1_data():
    data = utils.get_right1_data()
    city = []
    confirm = []
    for k, v in data:
        city.append(k)
        confirm.append(int(v))
    return jsonify({"city": city, "confirm": confirm})


@app.route("/r2")
def get_right2_data():
    data = utils.get_right2_data()  # 格式 (('民警抗疫一线奋战16天牺牲1037364',), ('四川再派两批医疗队1537382',)
    d = []
    for i in data:
        k = i[0].rstrip(string.digits)  # 移除热搜数字
        v = i[0][len(k):]  # 获取热搜数字
        ks = extract_tags(k)  # 使用jieba 提取关键字
        for j in ks:
            if not j.isdigit():
                d.append({"name": j, "value": v})
    return jsonify({"kws": d})


@app.route('/time')
def gettime():
    return utils.get_time()


# 测试使用模板
@app.route('/tem')
def hello_world3():
    return render_template("index.html")


@app.route('/ajax', methods=["get", "post"])  # 保证ajax请求能顺利
def hello_world4():
    return '10000'


if __name__ == '__main__':
    app.jinja_env.auto_reload = True
    app.run(debug=True, host="192.168.137.1", port="7777")
