import sys

sys.path.append('.')
sys.path.append('..')

from sinanews_proj.util import RedisUtil, OssUtil
from scrapy.conf import settings
import time
import json

if __name__ == '__main__':
    redis_key = settings.get('DOWNLOAD_IMAGE_REDIS_KEY')

    oss = OssUtil()
    redis_conn = RedisUtil.connect()

    while True:
        # 从 redis 中随机取一条图片链接，形式：
        # {
        #   "hash":"8ad6978807383c6766879327035ad49757691d39",
        #   "src": "http://tvax4.sinaimg.cn/crop.0.0.996.996.50/629eb08cly8flwrjq18buj20ro0roju4.jpg",
        #   "oss": "img/profile_image/"
        # }

        item = RedisUtil.set_pop(redis_conn, redis_key)

        if item:
            obj = json.loads(item, encoding='utf-8')
            oss.download_img_up2oss(url=obj['src'], f_name=obj['oss'] + obj['hash'])
            time.sleep(0)
        else:
            # 如果 redis 为空，则等待1秒
            print('waiting for redis-key:[{}]......'.format(redis_key))
            time.sleep(1)
else:
    raise Exception('我不可以被import!')
