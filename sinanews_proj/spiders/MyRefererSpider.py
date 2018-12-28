from scrapy_redis.spiders import RedisSpider
from scrapy.http import Request
import six


def bytes_to_str(s, encoding='utf-8'):
    """Returns a str if a bytes object is given."""
    if six.PY3 and isinstance(s, bytes):
        return s.decode(encoding)
    return s


class MyRefererSpider(RedisSpider):

    def parse(self, response):
        pass

    def make_request_from_data(self, data):
        """
        构造request，并把header.referer设置为自己，
        覆盖了父类Spider的方法
        :param data:
        :return:
        """
        url = bytes_to_str(data, self.redis_encoding)
        return Request(url, headers={'referer': url})
