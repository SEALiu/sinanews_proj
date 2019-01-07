# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

# pipeline 作用：
# 1. 查重并丢弃
# 2. 将爬取的数据保存至数据库

from twisted.enterprise import adbapi
from pymysql import cursors
from sinanews_proj.util.mysqlUtil import get_i_sql
from sinanews_proj.items import SinaNewsItem, SinaNewsCommentItem, SinaUserItem

import logging
import traceback


class MysqlTwistedPipeline(object):
    # 同步写入数据速度比较慢,而爬虫速度比较快,可能导致数据最后写入不到数据库中'
    # 1.引入twisted.enterprise.adbapi  pymysql.cursors
    # 2.在settings中配置数据库连接参数
    # 3.创建pipeline,实现from_settings函数,从settings获取数据库连接参数,根据参数创建连接池对象,返回当前pipeline的对象,并且把连接池赋值给该对象属性
    # 4.实现process_item函数,使用db_pool.runInteraction(函数,函数需要的参数) 将数据库的处理操作放入连接池s,还需要将操作数据的函数实现,使用cursor执行sql
    # 5.拿到runInteraction()函数返回的处理结果,添加错误回调函数,在函数中将错误原因打印

    def __init__(self, dbpool):
        self.dbpool = dbpool

    @classmethod
    def from_settings(cls, settings):
        # 准备数据库的链接参数,是一个字典
        db_params = dict(
            host=settings['MYSQL_HOST'],
            port=settings['MYSQL_PORT'],
            user=settings['MYSQL_USER'],
            password=settings['MYSQL_PASS'],
            db=settings['MYSQL_DB'],
            charset=settings['MYSQL_CHARSET'],
            use_unicode=True,
            # 指定使用的游标类型
            cursorclass=cursors.DictCursor
        )
        # 创建连接池
        # 1.使用的操作数据库的包名称
        # 2.准备的数据库链接参数
        db_pool = adbapi.ConnectionPool('pymysql', **db_params)
        # 返回创建好的对象
        return cls(db_pool)

    def process_item(self, item, spider):
        # 使用twisted将mysql插入变成异步执行
        # 可以根据 @param(item) 存入不同的数据库.
        if isinstance(item, SinaNewsItem):
            self.dbpool.connect()
            query = self.dbpool.runInteraction(self.do_insert_news, item)
            query.addErrback(self.handle_error, item, spider)
        elif isinstance(item, SinaNewsCommentItem):
            self.dbpool.connect()
            query = self.dbpool.runInteraction(self.do_insert_comment, item)
            query.addErrback(self.handle_error, item, spider)
        elif isinstance(item, SinaUserItem):
            self.dbpool.connect()
            query = self.dbpool.runInteraction(self.do_insert_user, item)
            query.addErrback(self.handle_error, item, spider)

        return item

    # 处理异步插入的异常
    @staticmethod
    def handle_error(failure, item, spider):
        logging.debug('spider[{}] save item failed, with error-info: {}\n{}'
                      .format(spider, failure.value, ''.join(traceback.format_tb(failure.tb))))

    def do_insert_news(self, cursor, item):
        sql = get_i_sql(table='tb_sina_news', column_value=item)
        try:
            cursor.execute(sql)
            self.dbpool.disconnect()
            return item
        except Exception as err:
            logging.debug('MysqlTwistedPipeline do_insert_news() failed with executing sql:[{}], error-info:{}'
                          .format(sql, err))

    def do_insert_comment(self, cursor, item):
        sql = get_i_sql(table='tb_sina_news_comments', column_value=item)
        try:
            cursor.execute(sql)
            self.dbpool.disconnect()
            return item
        except Exception as err:
            logging.debug('MysqlTwistedPipeline do_insert_comment() failed with executing sql:[{}], error-info:{}'
                          .format(sql, err))

    def do_insert_user(self, cursor, item):
        sql = get_i_sql(table='tb_sina_user', column_value=item)
        try:
            cursor.execute(sql)
            self.dbpool.disconnect()
            return item
        except Exception as err:
            logging.debug('MysqlTwistedPipeline do_insert_user() failed with executing sql:[{}], error-info:{}'
                          .format(sql, err))
