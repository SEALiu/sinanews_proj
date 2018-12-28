# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html
import logging
import requests


class ProxyMiddleware(object):
    def __init__(self, proxy_rul):
        self.proxy_url = proxy_rul
        self.proxy = self.get_proxy(self.proxy_url)
        logging.debug('use proxy ip:{}'.format(self.proxy))

    @classmethod
    def from_crawler(cls, crawler):
        return cls(proxy_rul=crawler.settings.get('PROXY_URL'))

    def parse_request(self, request, spider):
        # 可以根据不同的 @param(spider) 设置不同的 ip 代理
        # request.meta['proxy'] = 'http://{}'.format(random.choice(self.proxies))
        request.meta['proxy'] = 'http://{}'.format(self.proxy)

    @staticmethod
    def get_proxy(proxy_url):
        return requests.get(proxy_url).content

    @staticmethod
    def get_proxies(proxy_list):
        return requests.get(proxy_list).content
