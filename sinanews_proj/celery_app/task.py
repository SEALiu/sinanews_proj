# 使用 celery.task 装饰器包装的函数就是任务的主体
# 使用命令启动worker：
# celery -A [project] worker -l info
# -A/ --app, 指定Celery项目，如果参数给的是一个package，那么celery cmd 会自动搜索celery.py 模块，最终它要加载的是app对象
#
# 使用 -Q 用指定队列的方式启动消费者进程
# celery -A [project] worker -Q [queue_name] -l info
#
# 使用 multi 命令启动一个或多个 worker
# celery multi start [worker-name] -A [project-name] -l info
#
# 启动 Beat 进程，然后启动 worker：
# celery beat -A [project]
# celery -A [project] worker -l info
#
# Beat 进程和 worker 也可以同时启动[windows 不支持]：
# celery -B -A [project] worker -l info
# 使用 -B 用 Celery 的 Beat 进程自动生成任务，然后每隔一段时间执行一次 celery_app.task.sinanews_crawl

import sys

sys.path.append('.')
sys.path.append('..')

from celery_app import app
from spiders.SinaNewsSpider import SinaNewsSpider
from spiders.crawl import crawler_p, crawler_r, crawler_d, crawler_
from util import OssUtil, RedisUtil
from crochet import setup
from celery.utils.log import get_task_logger
from scrapy.conf import settings
import json

import os
import time, datetime

logger = get_task_logger(__name__)
setup()


# celery worker -A celery_app -Q crawl_tasks -P gevent -l info
@app.task(bind=True, ignore_result=True)
def sinanews_crawl(self):
    logger.info(('Executing task id {0.id}, args:{0.args!r}'
                 'kwargs: {0.kwargs!r}').format(self.request))
    try:
        conn = RedisUtil.connect()
        RedisUtil.set_add(conn, SinaNewsSpider.redis_key, 'https://edu.sina.cn/')
        crawler_d()
    except Exception as e:
        raise self.retry(exc=e, countdown=30, max_retries=3)


# celery worker -A celery_app -Q download_image_tasks -P gevent -l info
@app.task(bind=True, ignore_result=True)
def image_2_oss(self):
    logger.info(('Executing task id {0.id}, args:{0.args!r}'
                 'kwargs: {0.kwargs!r}').format(self.request))
    try:
        download_image_redis_key = settings.get('DOWNLOAD_IMAGE_REDIS_KEY')
        oss_util = OssUtil()
        conn = RedisUtil.connect()

        item = RedisUtil.set_pop(conn, download_image_redis_key)
        if item:
            obj = json.loads(item, encoding='utf-8')
            oss_util.download_img_up2oss(url=obj['src'], f_name=obj['oss'] + obj['hash'])
    except Exception as e:
        raise self.retry(exc=e, countdown=5, max_retries=3)


@app.task(bind=True)
def cleaner(self):
    logger.info(('Executing task id {0.id}, args:{0.args!r}'
                 'kwargs: {0.kwargs!r}').format(self.request))

    file_path = '../img_temp/'
    trash_list = []

    for path in os.listdir(file_path):
        name = path
        path = os.path.join(file_path, path)

        if not os.path.isdir(path):

            c_timestamp = os.path.getctime(file_path)
            now_timestamp = time.time()
            delta_seconds = (datetime.datetime.fromtimestamp(now_timestamp) - datetime.datetime.fromtimestamp(
                c_timestamp)).seconds
            print('file:[{}] delta seconds:{}'.format(name, delta_seconds))

            if delta_seconds > 60 * 60 * 2:
                trash_list.append(path)
                print('mark file [{}]:[created at {}] as trash.'.format(
                    name, time.strftime(
                        '%Y-%m-%d %H:%M:%S', time.localtime(c_timestamp)
                    )
                ))

    for trash in trash_list:
        os.remove(trash)

    print('cleaning work is done!')
