from __future__ import absolute_import
from kombu import Queue
from datetime import timedelta

import os

worker_log_path = os.path.join(os.path.dirname(os.path.dirname(__file__)) + '/logs', 'celery.log')
beat_log_path = os.path.join(os.path.dirname(os.path.dirname(__file__)) + '/logs', 'beat.log')

BROKER_URL = 'amqp://[rabbitmq-username]:[rabbitmq-pwd]@[host]:5672//'
CELERY_RESULT_BACKEND = 'redis://[redis-username]:[redis-pwd]@[host]:6379/[dbid]'

CELERY_WORKER_MAX_TASKS_PER_CHILD = 1
CELERY_TASK_SERIALIZER = 'msgpack'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TASK_RESULT_EXPIRES = 60 * 60 * 24
CELERY_ACCEPT_CONTENT = ['json', 'msgpack']

CELERY_TIMEZONE = 'Asia/Shanghai'
CELERY_ENABLE_UTC = True

CELERYD_LOG_FILE = worker_log_path
CELERYBEAT_LOG_FILE = beat_log_path

CELERY_IMPORTS = (  # 指定需要导入的任务模块
    'celery_app.task'
)

CELERY_QUEUE = (
    # 路由键以“task.”开头的消息都进default队列
    Queue('default', routing_key='task.#'),
    # 路由键以“crawl.”开头的消息都进 crawl_tasks 队列
    Queue('crawl_tasks', routing_key='crawl.#')
)

# 默认的交换机名字为tasks
CELERY_DEFAULT_EXCHANGE = 'tasks'
# 默认的交换类型是topic
CELERY_DEFAULT_EXCHANGE_TYPE = 'topic'
# 默认的路由键是task.default，这个路由键符合上面的default队列
CELERY_DEFAULT_ROUTING_KEY = 'task.default'

CELERY_ROUTES = {
    # tasks.books_crawl 的消息会进入 web_tasks 队列
    'celery_app.task.sinanews_crawl': {
        'queue': 'crawl_tasks',
        'routing_key': 'crawl.sinanews_crawl',
    }
}

# periodic tasks
CELERYBEAT_SCHEDULE = {
    'add': {
        'task': 'celery_app.task.sinanews_crawl',
        'schedule': timedelta(seconds=0, minutes=5, hours=0, days=0),
        'args': (),
        'options': {
            'queue': 'crawl_tasks',
            'routing_key': 'crawl.sinanews_crawl'
        }
    }
}
