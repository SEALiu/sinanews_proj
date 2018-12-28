 #### how to start?
 
```
pip install -r requirements.txt
```

*TODO: change config-file below:*
 1. `/sinanews_proj/sinanews_proj/celery_app/celeryconfig.example.py`
 2. `/sinanews_proj/sinanews_proj/util/ossUtil.example.py`
 3. `/sinanews_proj/sinanews_proj/settings.example.py`

**running scrapy crawler manually**
```commandline
scrapy crawl sina_news_spider
python downloadImage.py
```

**running scrapy crawler with celery**
```commandline
cd /sinanews_proj/sinanews_proj/

celery beat -A celery_app
celery worker -A celery_app -Q crawl_tasks -l info
```
