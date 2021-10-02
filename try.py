import requests
import json
import time
import pymysql
from selenium.webdriver import Chrome, ChromeOptions
import traceback
import sys


# 爬取json文件
url1 = "https://view.inews.qq.com/g2/getOnsInfo?name=disease_h5"
url2 = "https://view.inews.qq.com/g2/getOnsInfo?name=disease_other"
headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.70 Safari/537.36'
}
r1 = requests.get(url1, headers)
r2 = requests.get(url2, headers)

# json字符串转字典
res1 = json.loads(r1.text)
res2 = json.loads(r2.text)

data_all1 = json.loads(res1["data"])
data_all2 = json.loads(res2["data"])

# 历史数据
history = {}
for i in data_all2["chinaDayList"]:
    ds = "2020." + i["date"]

    tup = time.strptime(ds, "%Y.%m.%d")  # 拆成时间元组

    ds = time.strftime("%Y-%m-%d", tup)  # 改变时间输入格式，不然插入数据库会报错，数据库是datatime格式
    # print(ds)

    confirm = i["confirm"]
    suspect = i["suspect"]
    heal = i["heal"]
    dead = i["dead"]
    history[ds] = {"confirm": confirm, "suspect": suspect, "heal": heal, "dead": dead}
    # print(history)

for i in data_all2["chinaDayAddList"]:
    ds = "2020." + i["date"]
    tup = time.strptime(ds, "%Y.%m.%d")  # 匹配时间
    ds = time.strftime("%Y-%m-%d", tup)  # 改变时间输入格式，不然插入数据库会报错，数据库是datatime格式
    # print(history[ds])
    confirm = i["confirm"]
    suspect = i["suspect"]
    heal = i["heal"]
    dead = i["dead"]
    history[ds].update({"confirm_add": confirm, "suspect_add": suspect, "heal_add": heal, "dead_add": dead})
    # print(history)
# print(history)
# 当日详细数据
details = []
update_time = data_all1["lastUpdateTime"]
data_country = data_all1["areaTree"]  # list 25个国家
data_province = data_country[0]["children"]  # 中国各省
# print(data_province)
for pro_infos in data_province:
    province = pro_infos["name"]  # 省名
    for city_infos in pro_infos["children"]:
        city = city_infos["name"]
        confirm = city_infos["total"]["confirm"]
        confirm_add = city_infos["today"]["confirm"]
        heal = city_infos["total"]["heal"]
        dead = city_infos["total"]["dead"]
        details.append([update_time, province, city, confirm, confirm_add, heal, dead])

    # print(details)



# 建立连接
conn = pymysql.connect(host="192.168.40.128", user="root", password="123456", db="COVID-19", charset="utf8")
# 创建游标
cursor = conn.cursor()
present_details = details  # 0位是history，1位是present





dic = history  # 0代表历史数据字典
print(f"{time.asctime()}开始插入历史数据")
sql = "insert into history values (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
for k, v in dic.items():
    cursor.execute(sql, [k, v.get("confirm"), v.get("confirm_add"), v.get("suspect"),
                         v.get("suspect_add"), v.get("heal"), v.get("heal_add"),
                         v.get("dead"), v.get("dead_add")])
    conn.commit()
print(f"{time.asctime()}插入历史数据完毕")



# 更新历史数据



# dic = history  # 0代表历史数据字典
# print(f"{time.asctime()}开始更新历史数据")
# sql = "insert into history values (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
# sql_query = "select confirm from history where ds=%s"
# for k, v in dic.items():
#     if not cursor.execute(sql_query, k):
#         cursor.execute(sql, [k, v.get("confirm"), v.get("confirm_add"), v.get("suspect"),
#                              v.get("suspect_add"), v.get("heal"), v.get("heal_add"),
#                              v.get("dead"), v.get("dead_add")])
#     conn.commit()
# print(f"{time.asctime()}历史数据更新完毕")



