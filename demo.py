import traceback

import requests
import json,time
import csv,pymysql
def save_csv(head,name,result):
    with open(name, "w", encoding="utf-8", newline='') as f:
        writer = csv.DictWriter(f, head)
        writer.writeheader()
        writer.writerows(result)
        print("已存入")

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
    return (history, present)

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


host = "49.235.0.110"
user = "root"
password = "123456"
db = "covid"
insert_history(host,user,password,db)