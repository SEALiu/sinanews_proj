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

# because of the bug in celery4.1, it cannot set timezone except UTC.
# CELERY_TIMEZONE = 'Asia/Shanghai'
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
    Queue('crawl_tasks', routing_key='crawl.#'),
)

# 默认的交换机名字为tasks
CELERY_DEFAULT_EXCHANGE = 'tasks'
# 默认的交换类型是topic
CELERY_DEFAULT_EXCHANGE_TYPE = 'topic'
# 默认的路由键是task.default，这个路由键符合上面的default队列
CELERY_DEFAULT_ROUTING_KEY = 'task.default'

CELERY_ROUTES = {
    # celery_app.task.sinanews_crawl 的消息会进入 crawl_tasks 队列
    'celery_app.task.sinanews_crawl': {
        'queue': 'crawl_tasks',
        'routing_key': 'crawl.sinanews_crawl',
    },

    # celery_app.task.image_2_oss 的消息会进入 download_image_tasks 队列
    'celery_app.task.image_2_oss': {
        'queue': 'download_image_tasks',
        'routing_key': 'download.image_2_oss',
    },

    # celery_app.task.cleaner 的消息会进入 clean_tasks 队列
    'celery_app.task.cleaner': {
        'queue': 'clean_tasks',
        'routing_key': 'clean.cleaner',
    },
}

# periodic tasks
CELERYBEAT_SCHEDULE = {
    'sinanews_crawl': {
        'task': 'celery_app.task.sinanews_crawl',
        'schedule': timedelta(seconds=0, minutes=30, hours=0, days=0),
        'args': (),
        'options': {
            'queue': 'crawl_tasks',
            'routing_key': 'crawl.sinanews_crawl'
        }
    },

    'image_2_oss': {
        'task': 'celery_app.task.image_2_oss',
        'schedule': timedelta(seconds=0.1),
        'args': (),
        'options': {
            'queue': 'download_image_tasks',
            'routing_key': 'download.image_2_oss'
        }
    },

    'cleaner': {
        'task': 'celery_app.task.cleaner',
        'schedule': timedelta(seconds=0, minutes=0, hours=0, days=1),
        'args': (),
        'options': {
            'queue': 'clean_tasks',
            'routing_key': 'clean.cleaner'
        }
    }
}
