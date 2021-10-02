import requests
import json
import time
import pymysql
from selenium.webdriver import Chrome, ChromeOptions
import traceback
import sys


# 返回历史数据和当日详细数据
def get_all_data():
    # 爬取json文件
    url1 = "https://view.inews.qq.com/g2/getOnsInfo?name=disease_h5"
    url2 = "https://view.inews.qq.com/g2/getOnsInfo?name=disease_other"
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.70 Safari/537.36'
    }
    r1 = requests.get(url1, headers)
    r2 = requests.get(url2, headers)

    # json字符串转字典
    dic_data1 = json.loads(r1.text)
    dic_data2 = json.loads(r2.text)

    all_data1 = json.loads(dic_data1["data"])
    all_data2 = json.loads(dic_data2["data"])

    # 历史数据
    history = {}
    # 得到本日存量，即目前的情况
    for i in all_data2["chinaDayList"]:
        date_time = "2020." + i["date"]
        time_tuple = time.strptime(date_time, "%Y.%m.%d")  # 拆成时间元组
        date_time = time.strftime("%Y-%m-%d", time_tuple)  # 按照2020-01-13的格式输入到数据库
        confirm = i["confirm"]
        suspect = i["suspect"]
        heal = i["heal"]
        dead = i["dead"]
        # 每天对应每种情况
        history[date_time] = {"confirm": confirm, "suspect": suspect, "heal": heal, "dead": dead}

    # 得到流量，即变化的情况
    for i in all_data2["chinaDayAddList"]:
        date_time = "2020." + i["date"]
        time_tuple = time.strptime(date_time, "%Y.%m.%d")  # 拆成时间元组
        date_time = time.strftime("%Y-%m-%d", time_tuple)  # 按照2020-01-13的格式输入到数据库
        confirm = i["confirm"]
        suspect = i["suspect"]
        heal = i["heal"]
        dead = i["dead"]
        # 每天对应每种情况
        history[date_time].update({"confirm_add": confirm, "suspect_add": suspect, "heal_add": heal, "dead_add": dead})

    # 当日各省市的详细数据，返回字典列表【{}，{}。。。】
    present = []
    update_time = all_data1["lastUpdateTime"]
    data_country = all_data1["areaTree"]
    data_province = data_country[0]["children"]  # 中国各省
    for province_message in data_province:
        province = province_message["name"]  # 省名
        for city_message in province_message["children"]:
            city = city_message["name"]
            confirm = city_message["total"]["confirm"]
            confirm_add = city_message["today"]["confirm"]
            heal = city_message["total"]["heal"]
            dead = city_message["total"]["dead"]
            present.append([update_time, province, city, confirm, confirm_add, heal, dead])
    return history, present


def get_conn(host_,user_,password_,db_):
    # 建立连接
    conn = pymysql.connect(host=host_, user=user_, password=password_, db=db_, charset="utf8")
    # 创建游标
    cursor = conn.cursor()
    return conn, cursor


def close_conn(conn, cursor):
    if cursor:
        cursor.close()
    if conn:
        conn.close()


# 插入present数据
def update_present(host_,user_,password_,db_):
    cursor = None
    conn = None
    try:
        present_details = get_all_data()[1]  # 0位是history，1位是present
        conn, cursor = get_conn(host_,user_,password_,db_)
        # 要注意格式化SQL语句时，有些原本就是字符串，不能加‘’
        sql = "insert into Present(update_time,province,city,confirm,confirm_add,heal,dead) values(%s,%s,%s,'%s','%s','%s','%s')"
        sql_query = "select %s=(select update_time from Present order by update_time desc limit 1)"  # 对比当前最大时间戳
        # 对比当前最大时间戳
        cursor.execute(sql_query, present_details[0][0])
        if not cursor.fetchone()[0]:
            print(f"{time.asctime()}开始更新数据")
            for item in present_details:
                cursor.execute(sql, item)
            conn.commit()
            print(f"{time.asctime()}更新到最新数据")
        else:
            print(f"{time.asctime()}已是最新数据！")
    except:
        traceback.print_exc()
    finally:
        close_conn(conn, cursor)


# 插入历史数据
def insert_history(host_,user_,password_,db_):
    cursor = None
    conn = None
    try:
        dic = get_all_data()[0]  # 0代表历史数据字典
        print(f"{time.asctime()}开始插入历史数据")
        conn, cursor = get_conn(host_,user_,password_,db_)
        sql = "insert into history values (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        for k, v in dic.items():
            # K代表日期
            cursor.execute(sql, [k, v.get("confirm"), v.get("confirm_add"), v.get("suspect"),
                                 v.get("suspect_add"), v.get("heal"), v.get("heal_add"),
                                 v.get("dead"), v.get("dead_add")])
        conn.commit()
        print(f"{time.asctime()}插入历史数据完毕")
    except:
        traceback.print_exc()
    finally:
        close_conn(conn, cursor)


# 更新历史数据
def update_history(host_,user_,password_,db_):
    cursor = None
    conn = None
    try:
        dic = get_all_data()[0]  # 0代表历史数据字典
        print(f"{time.asctime()}开始更新历史数据")
        conn, cursor = get_conn(host_,user_,password_,db_)
        sql = "insert into history values (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        sql_query = "select confirm from history where ds=%s"
        for k, v in dic.items():
            if not cursor.execute(sql_query, k):
                cursor.execute(sql, [k, v.get("confirm"), v.get("confirm_add"), v.get("suspect"),
                                     v.get("suspect_add"), v.get("heal"), v.get("heal_add"),
                                     v.get("dead"), v.get("dead_add")])
        conn.commit()
        print(f"{time.asctime()}历史数据更新完毕")
    except:
        traceback.print_exc()
        print("目前数据未更新")
    finally:
        close_conn(conn, cursor)


# 返回百度疫情热搜
def get_baidu_hot():
    option = ChromeOptions()  # 创建谷歌浏览器实例
    option.add_argument("--headless")  # # 浏览器不提供可视化页面
    option.add_argument("--no-sandbox")  # 禁用沙盒模式

    url = 'https://voice.baidu.com/act/virussearch/virussearch?from=osari_map&tab=0&infomore=1'
    brower = Chrome(options=option)
    brower.get(url)
    # 找到查看更多按钮
    but = brower.find_element_by_xpath(
        '//*[@id="ptab-0"]/div/div[1]/section/div')  # 定位到按钮
    but.click()  # 点击展开

    time.sleep(1)  # 模拟人等待1秒(盗亦有道)

    c = brower.find_elements_by_xpath('//*[@id="ptab-0"]/div/div[2]/section/a/div/span[2]')
    context = [i.text for i in c]  # 获取热点事件内容
    # print(context)
    return context


# 将疫情热搜插入数据库
def update_hotsearch(host_,user_,password_,db_):
    # 初始化连接，保证数据库安全
    cursor = None
    conn = None
    try:
        context = get_baidu_hot()
        print(f"{time.asctime()}开始更新热搜数据")
        conn, cursor = get_conn(host_,user_,password_,db_)
        sql = "insert into hotsearch(dt,content) values(%s,%s)"
        ts = time.strftime("%Y-%m-%d %X")  # 获取此时时间
        for i in context:
            cursor.execute(sql, (ts, i))  # 插入数据
        conn.commit()  # 提交事务保存数据
        print(f"{time.asctime()}数据更新完毕")
    except:
        traceback.print_exc()
        print("目前数据未更新")
    finally:
        close_conn(conn, cursor)


if __name__ == "__main__":
    # host = "192.168.40.128", user = "root", password = "123456", db = "COVID-19", charset = "utf8"
    host = input("请输入host：")
    user = input("请输入用户名：")
    password = input("请输入密码：")
    db = input("请输入数据库名称：")
    # sys.argv 获得执行时的参数
    # 提醒用户以python spider.py [函数代名词]的形式执行
    # 例如：python spider.py up_pre ------>执行update_present（）函数

    l = len(sys.argv)
    # 提示用户执行某种方法
    if l == 1:
        s = """
        请输入参数
        参数说明，
        up_his 更新历史记录表
        up_hot 更新实时热搜
        up_pre 更新最新全国情况
        up_all
        """
        print(s)
    else:
        order = sys.argv[1]
        if order == "up_his":
            update_history(host,user,password,db)
        elif order == "up_pre":
            update_present(host,user,password,db)
        elif order == "up_hot":
            update_hotsearch(host,user,password,db)
        elif order=="up_all":
            update_history(host, user, password, db)
            update_present(host, user, password, db)
            update_hotsearch(host, user, password, db)

