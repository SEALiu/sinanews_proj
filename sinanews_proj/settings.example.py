# -*- coding: utf-8 -*-

# Scrapy settings for sinanews_proj project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://doc.scrapy.org/en/latest/topics/settings.html
#     https://doc.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://doc.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = 'sinanews_proj'

SPIDER_MODULES = ['sinanews_proj.spiders']
NEWSPIDER_MODULE = 'sinanews_proj.spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
# USER_AGENT = 'sinanews_proj (+http://www.yourdomain.com)'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
# CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See https://doc.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
# DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
# CONCURRENT_REQUESTS_PER_DOMAIN = 16
# CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
# TELNETCONSOLE_ENABLED = False

# Override the default request headers:
# DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
# }

# Enable or disable spider middlewares
# See https://doc.scrapy.org/en/latest/topics/spider-middleware.html
# SPIDER_MIDDLEWARES = {
#    'sinanews_proj.middlewares.SinanewsProjSpiderMiddleware': 543,
# }

# Enable or disable downloader middlewares
# See https://doc.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    # 'sinanews_proj.middlewares.SinanewsProjDownloaderMiddleware': 543,
    'sinanews_proj.middlewares.ProxyMiddleware': 100,
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'scrapy_fake_useragent.middleware.RandomUserAgentMiddleware': 400,
}

# Enable or disable extensions
# See https://doc.scrapy.org/en/latest/topics/extensions.html
EXTENSIONS = {
    # 'scrapy.extensions.telnet.TelnetConsole': None,
    'sinanews_proj.extensions.RedisSpiderSmartIdleClosedExtensions': 500,
}

# Configure item pipelines
# See https://doc.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    'sinanews_proj.pipelines.MysqlTwistedPipeline': 100,
    # 'sinanews_proj.pipelines.SinanewsProjPipeline': 300,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://doc.scrapy.org/en/latest/topics/autothrottle.html
AUTOTHROTTLE_ENABLED = True
# The initial download delay
AUTOTHROTTLE_START_DELAY = 1
# The maximum download delay to be set in case of high latencies
# AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
# AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
# AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://doc.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
HTTPCACHE_ENABLED = True
HTTPCACHE_POLICY = 'scrapy.contrib.httpcache.RFC2616Policy'
# HTTPCACHE_EXPIRATION_SECS = 0
# HTTPCACHE_DIR = 'httpcache'
# HTTPCACHE_IGNORE_HTTP_CODES = []
# HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'

#########################################
#         CUSTOM setting items          #
#########################################
REDIRECT_ENABLED = True

MYEXT_ENABLED = True
IDLE_NUMBER = 10  # 配置空闲持续时间单位为10个 ，一个时间单位为5s

#########################################
#             LOG setting               #
#########################################
# By default, RFPDupeFilter only logs the first duplicate request.
# Setting DUPEFILTER_DEBUG to True will make it log all duplicate requests.
# DUPEFILTER_DEBUG = True
# LOG_ENABLED = True
# LOG_LEVEL = 'INFO'
# LOG_FORMAT = '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
# LOG_DATEFORMAT = '%Y-%m-%d %H:%M:%S'
# 是否将控制台输出全部放入日志文件中
# LOG_STDOUT = False
# LOG_FILE = './logging.log'

#########################################
#        UA/Proxy-list setting          #
#########################################
#  todo 修改 proxy-pool-host
RANDOM_UA_TYPE = 'random'
RANDOM_UA_PER_PROXY = True

PROXY_URL = 'http://[proxy-pool-host]:5010/get/'
PROXY_MODE = 0
RETRY_TIMES = 10
RETRY_HTTP_CODES = [500, 503, 504, 400, 403, 404, 408]

#########################################
#          DupeFilter setting           #
#########################################
# 使用 bloom filter
# SCHEDULER = "scrapy_redis_bloomfilter.scheduler.Scheduler"
# DUPEFILTER_CLASS = "scrapy_redis_bloomfilter.dupefilter.RFPDupeFilter"

# Redis Memory Bit of Bloomfilter Usage, 31 means 2^31 = 256MB, defaults to 30
# BLOOMFILTER_BIT = 31

# Number of Hash Functions to use, defaults to 6
# 为了让 BloomFilter 的漏失率降到 10e-4 级别，
# 如果去重对象的数量不超过：0.67亿条，hash-seed可选择：4（此时漏失率最大为：0.000191）
# 如果去重对象的数量不超过：0.79亿条，hash-seed可选择：5（此时漏失率最大为：0.000138）
# 如果去重对象的数量不超过：0.93亿条，hash-seed可选择：6（此时漏失率最大为：0.000117）
# BLOOMFILTER_HASH_NUMBER = 6

#########################################
#            REDIS setting              #
#########################################
# todo 修改 redis 配置
SCHEDULER_PERSIST = True
REDIS_START_URLS_AS_SET = True
# 默认的scrapy-redis请求队列形式（按优先级）
SCHEDULER_QUEUE_CLASS = "scrapy_redis.queue.SpiderPriorityQueue"
# 队列形式，请求先进先出
# SCHEDULER_QUEUE_CLASS = "scrapy_redis.queue.SpiderQueue"
# 栈形式，请求先进后出
# SCHEDULER_QUEUE_CLASS = "scrapy_redis.queue.SpiderStack"

# REDIS_URL = 'redis://root:Peishen1!@192.168.10.103:6379'
REDIS_HOST = '[host]'
REDIS_PORT = 6379
REDIS_PARAMS = {'password': '[password]'}
REDIS_BID = 0
DOWNLOAD_IMAGE_REDIS_KEY = 'image:download_url'

#########################################
#            MySQL setting              #
#########################################
# todo 修改 mysql 配置
MYSQL_HOST = '[host]'
MYSQL_PORT = 3306
MYSQL_USER = '[username]'
MYSQL_PASS = '[password]'
MYSQL_DB = '[database name]'
MYSQL_CHARSET = 'utf8'
