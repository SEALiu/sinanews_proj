import redis
from scrapy.conf import settings


class RedisUtil(object):
    """
    redis 数据库工具类
    """

    @staticmethod
    def connect(host=settings.get('REDIS_HOST'),
                port=settings.get('REDIS_PORT'),
                password=settings.get('REDIS_PARAMS').get('password')):
        """
        连接 redis 数据库
        :param host: redis_host
        :param port: redis_port
        :param password: redis_password
        :return: redis connection
        """
        return redis.Redis(host=host, port=port, password=password)

    @staticmethod
    def set_add(conn, key, value=None) -> None:
        if value:
            conn.sadd(key, value)

    @staticmethod
    def set_pop(conn, key: str) -> str:
        """
        Get return a random element
        :param conn: redis connection
        :param key: redis key
        :return:
        """
        b = conn.spop(key)
        return str(b, encoding='utf-8') if b else None
