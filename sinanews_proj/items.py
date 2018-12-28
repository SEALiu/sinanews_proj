# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy import Item, Field
from scrapy.loader import ItemLoader
from scrapy.loader.processors import MapCompose, TakeFirst
from sinanews_proj.util.tools import html_pure, html_pretty, imgsrc_2_osshash, src2osshash
from sinanews_proj.util.redisUtil import RedisUtil
from scrapy.conf import settings

import re


def strip(value):
    # 去掉 value 两端的空格
    return value.strip() if value else ''


def parse_type(data: list) -> str:
    return '-'.join(data)


def parse_content(data: dict) -> str:
    """
    处理网页内容，提取文章的内容。并去掉html内容中的空格、tabs、换行(压缩)，再去掉节点的属性
    上传内容中的图片至oss，并将文章内容中的图片src替换成oss链接
    :param data: {'html': '', 'value': ''}
    :return: 处理后的文章内容
    """
    assert all(k in data for k in ('html', 'url', 'ossPath'))

    html = data['html']
    url = data['url']
    oss_path = data['ossPath']

    regex_content = r'<section\s+class=\"(art_pic_card\s)?(art_content)[\w\W]*?>([\w\W]*?)</section>'
    matches_content = re.search(regex_content, html, re.MULTILINE)

    content = ''
    if matches_content and len(matches_content.groups()) == 3:
        content = html_pretty(matches_content.group(3))
        content = html_pure(content)

        redis_conn = RedisUtil.connect()

        for (key, value) in imgsrc_2_osshash(content, url, oss_path).items():
            if key == 'html':
                content = value
            else:
                # 将图片的下载链接放入redis数据库，另开进程对redis中的图片进行下载
                json_str = '{{"hash":"{}","src": "{}","oss": "{}"}}'.format(key, value, oss_path)
                RedisUtil.set_add(redis_conn,
                                  settings.get('DOWNLOAD_IMAGE_REDIS_KEY'),
                                  json_str)
                print('image:{}'.format(json_str))
    return content


def parse_keyword(value: str) -> str:
    # 使用@分割关键词
    keywords = value.split(',')
    return '@'.join(keywords)


def parse_image(data: dict) -> str:
    src = data['src']
    url = data['url']
    oss_path = data['ossPath']

    if src:
        d_result = src2osshash(src, url, oss_path)

        # 将头像图片放入 redis 队列，另开进程对redis中的图片进行下载
        json_str = '{{"hash":"{}","src": "{}","oss": "{}"}}'.format(d_result['hash'], d_result['image_download_url'],
                                                                    oss_path)

        redis_conn = RedisUtil.connect()
        RedisUtil.set_add(redis_conn,
                          settings.get('DOWNLOAD_IMAGE_REDIS_KEY'),
                          json_str)
        print('image:{}'.format(json_str))
        return d_result['oss_link']
    else:
        return ''


class SinaNewsLoader(ItemLoader):
    # item loader 对于每个 item 都有两个处理器，一个是输入处理器，一个是输出处理器
    # 可以使用的内置 loaders
    default_output_processor = TakeFirst()


class SinaNewsItem(Item):
    news_id = Field()
    type = Field(input_processor=parse_type)
    title = Field()
    author_id = Field()
    author_name = Field()
    intro = Field()
    content = Field(input_processor=MapCompose(parse_content))
    url = Field()
    time = Field()
    key_word = Field(input_processor=MapCompose(parse_keyword))


class SinaNewsCommentLoader(ItemLoader):
    default_output_processor = TakeFirst()


class SinaNewsCommentItem(Item):
    comment_id = Field()
    user_id = Field()
    nickname = Field()
    ip = Field()
    location = Field()
    time = Field()
    content = Field()
    comment_type = Field()
    reply_id = Field()
    news_id = Field()
    like_num = Field()
    reply_num = Field()


class SinaUserItem(ItemLoader):
    default_output_processor = TakeFirst()


class SinaUserLoader(ItemLoader):
    default_output_processor = TakeFirst()


class SinaUserItem(Item):
    uid = Field()
    nickname = Field()
    profile_img = Field(input_processor=MapCompose(parse_image))
    bio = Field()
    follow_num = Field()
    follower_num = Field()
    weibo_num = Field()
    location = Field()
    tags = Field()
    gender = Field()
    reg_time = Field()
    email = Field()
    phone = Field()
    type_v = Field()
    verify_date = Field()
    account_level = Field()
    company = Field()
    company_location = Field()
    birth_day = Field()
    education_school = Field()
    blog_url = Field()
