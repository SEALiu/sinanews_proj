 ### 1. project intro
 sinanews_proj is a scrapy project crawling the news article, comments and user's profile information from `http://edu.sina.cn`. And it can be 
 scheduled by celery with RabbitMQ as task queue and redis as backend storage. **This project is an open-source software under GNU GENERAL PUBLIC LICENSE,
 you can change and republish source code with the same license.**
 
 **NOTICE:** with celery 4.1.1(>4.0), this project is not support Windows OS.


 ### 2. how to start?
 
```
pip install -r requirements.txt
```

*TODO: change config-file below:*
 1. `/sinanews_proj/sinanews_proj/celery_app/celeryconfig.example.py`  
 <small>Rename this file to celeryconfig.py, then modify `BROKER_URL` and `CELERY_RESULT_BACKEND`.</small>
 2. `/sinanews_proj/sinanews_proj/util/ossUtil.example.py`  
 <small>set your own Aliyun-oss configuration.</small>
 3. `/sinanews_proj/sinanews_proj/settings.example.py`  
 <small>set your own redis and mysql configuration.</small>


**running scrapy crawler manually**
```commandline
scrapy crawl sina_news_spider
python downloadImage.py
```


**running scrapy crawler with celery**
```python
cd /sinanews_proj/sinanews_proj/

celery beat -A celery_app

# crawl news, comments, users-info from 'http://edu.sina.cn/'"
celery worker -A celery_app -Q crawl_tasks -P gevent -l info -n worker@crawler

# download images and upload to aliyun oss
celery worker -A celery_app -Q download_image_tasks -P gevent -l info -n worker@downloader

# clean up the folder 'img_temp'
celery worker -A celery_app -Q clean_tasks -P gevent -l info -n worker@cleaner

# use `--`
```

**custom task scheduling interval:**  
```python
# celeryconfig.py

CELERYBEAT_SCHEDULE = {
    'sinanews_crawl': {
        'task': 'celery_app.task.sinanews_crawl',
        'schedule': timedelta(<set your custom interval here>),
        'args': (),
        'options': {
            'queue': 'crawl_tasks',
            'routing_key': 'crawl.sinanews_crawl'
        }
    },
    
    # ...
    # same as celey_app.task.cleaner
}
```

### 3. you may need ...
 - [github.com/jhao104/proxy_pool](https://github.com/jhao104/proxy_pool)
 - install RabbitMQ
 - [optional] `pip install flower`