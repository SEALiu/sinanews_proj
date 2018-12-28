import pymysql


def safe(s: str) -> str:
    return pymysql.escape_string(s)


def get_i_sql(table: str, column_value: dict) -> str:
    """
    生成insert的sql语句
    :param table，插入记录的表名
    :param column_value,插入的数据，字典
    :return: sql
    """
    sql = 'insert into %s set' % table
    sql += dict_2_str(column_value)
    return sql


def dict_2_str(dict_: dict) -> str:
    """
    将字典变成，key='value',key='value' 的形式
    :param dict_: 一个字典
    :return:
    """
    a_list = []
    for k, v in dict_.items():
        tmp = "%s='%s'" % (str(k), safe(str(v)))
        a_list.append(' ' + tmp + ' ')
    return ','.join(a_list)
