import time
import pymysql


def get_time():
    time_str = time.strftime("%Y{}%m{}%d{} %X")
    return time_str.format("年", "月", "日")  # 因为直接写不支持中文


# return: 连接，游标
def get_conn():
    # 创建连接
    conn = pymysql.connect(host="192.168.40.128",
                           user="root",
                           password="123456",
                           db="COVID-19",
                           charset="utf8")
    # 创建游标
    cursor = conn.cursor()  # 执行完毕返回的结果集默认以元组显示
    return conn, cursor


def close_conn(conn, cursor):
    cursor.close()
    conn.close()


def query(sql, *args):
    """
    封装通用查询
    :param sql:
    :param args:
    :return: 返回查询到的结果，((),(),)的形式
    """
    conn, cursor = get_conn()
    cursor.execute(sql, args)
    result = cursor.fetchall()
    close_conn(conn, cursor)
    return result


def get_center1_data():
    """
    :return: 返回大屏div id=c1 的数据
    """
    # 取时间戳最新的那组数据
    sql = "select sum(confirm)," \
          "(select suspect from history order by ds desc limit 1)," \
          "sum(heal)," \
          "sum(dead) " \
          "from Present " \
          "where update_time=(select update_time from Present order by update_time desc limit 1) "
    result = query(sql)
    # 返回一个元组
    return result[0]


# 返回各省直辖市 确诊总数
def get_center2_data():
    # 因为会更新多次数据，取时间戳最新的那组数据
    sql = "select province,sum(confirm) from Present " \
          "where update_time=(select update_time from Present " \
          "order by update_time desc limit 1) " \
          "group by province"
    result = query(sql)
    return result


def get_left1_data():
    '''返回历来确诊，疑似，重症，死亡人数'''
    sql = "select ds,confirm,suspect,heal,dead from history"
    result = query(sql)
    return result


def get_left2_data():
    '''返回历来新增的确诊，疑似，重症，死亡人数'''
    sql = "select ds,confirm_add,suspect_add from history"
    result = query(sql)
    return result


def get_right1_data():
    '''返回非湖北地区城市确诊人数前5名（关注直辖市与特别行政区的特殊情况）'''
    sql = 'SELECT city,confirm FROM ' \
          '(select city,confirm from Present ' \
          'where update_time=(select update_time from Present order by update_time desc limit 1) ' \
          'and province not in ("湖北","北京","上海","天津","重庆","香港","台湾") ' \
          'union all ' \
          'select province as city,sum(confirm) as confirm from Present  ' \
          'where update_time=(select update_time from Present order by update_time desc limit 1) ' \
          'and province in ("北京","上海","天津","重庆","香港","台湾") group by province) as a ' \
          'order by confirm desc limit 5'
    result = query(sql)
    return result


# 返回最近的20条热搜
def get_right2_data():
    sql = 'select content from hotsearch order by id desc limit 20'
    result = query(sql)  # 数据格式： (('吉林市火车站停运963548',), )
    return result

# 测试使用
# if __name__ == "__main__":
#     print(get_right2_data())
