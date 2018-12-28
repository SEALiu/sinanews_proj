import os
import oss2
import random
import string
import requests
import logging

from concurrent.futures import ThreadPoolExecutor
from functools import wraps


def singleton(cls):
    instances = {}

    @wraps(cls)
    def get_instance(*args, **kw):
        if cls not in instances:
            instances[cls] = cls(*args, **kw)
        return instances[cls]

    return get_instance


@singleton
class OssUtil(object):
    """
    使用单例模式
    以下代码展示了文件上传的高级用法，如断点续传、分片上传等。
    基本的文件上传如上传普通文件、追加文件，请参见object_basic.py

    首先初始化AccessKeyId、AccessKeySecret、Endpoint等信息。
    通过环境变量获取，或者把诸如“<你的AccessKeyId>”替换成真实的AccessKeyId等。

    以杭州区域为例，Endpoint可以是：
      http://oss-cn-hangzhou.aliyuncs.com
      https://oss-cn-hangzhou.aliyuncs.com
    分别以HTTP、HTTPS协议访问。
    """

    def __init__(self):
        # todo 修改Aliyun-oss参数：
        access_key_id = os.getenv('OSS_TEST_ACCESS_KEY_ID', '<你的AccessKeyId>')
        access_key_secret = os.getenv('OSS_TEST_ACCESS_KEY_SECRET', '<你的AccessKeySecret>')
        bucket_name = os.getenv('OSS_TEST_BUCKET', '<你的Bucket>')
        endpoint = os.getenv('OSS_TEST_ENDPOINT', '<你的Endpoint>')
        # 创建Bucket对象，所有Object相关的接口都可以通过Bucket对象来进行
        self.bucket = oss2.Bucket(oss2.Auth(access_key_id, access_key_secret), endpoint, bucket_name)
        self.executor = ThreadPoolExecutor(max_workers=20)
        # 确认上面的参数都填写正确了
        for param in (access_key_id, access_key_secret, bucket_name, endpoint):
            assert '<' not in param, '请设置参数：' + param

    def __upload_oss(self, f_name: str, f_path: str, multipart_threshold: int = None) -> None:
        """
        断点续传
        :param f_name: 保存的文件名（ossBasePath + hash）其中包含上传oss的路径
        :param f_path: 上传的文件本地路径
        :param multipart_threshold: 分片上传参数（k）
        """
        bucket = self.bucket

        if multipart_threshold:
            # 断点续传一：因为文件比较小（小于oss2.defaults.multipart_threshold），
            # 所以实际上用的是oss2.Bucket.put_object
            oss2.resumable_upload(bucket, f_name, f_path, num_threads=8)
        else:
            # 断点续传二：为了展示的需要，我们指定multipart_threshold可选参数，确保使用分片上传
            # multipart_threshold: 100 * 1024(100k)
            oss2.resumable_upload(bucket, f_name, f_path, multipart_threshold, num_threads=8)

    def __do_download_img_up2oss(self, url: str, f_name: str, multi: int) -> None:
        """
        保存图片至本地，然后使用本地图片路径上传至oss
        :param url: 下载图片地址
        :param f_name: 图片的名称（ossBasePath + hash）
        :param multi: multipartThreshold: 分片上传参数（k）
        """
        that = self

        def up2oss(res, *args, **kwargs):
            if res:
                img_temp_dir = '.' + os.sep + 'img_temp'
                try:
                    if not os.path.exists(img_temp_dir):
                        os.makedirs(img_temp_dir)
                    # 保存图片的文件夹存在，接下来获取暂存本地图片路径
                    # 随机为图片命名，拼接获得图片的本地路径
                    name_temp = ''.join(random.choice(string.ascii_lowercase) for _ in range(32))
                    local_path = '{dir}{osSep}{name}'.format(dir=img_temp_dir, osSep=os.sep, name=name_temp)
                    with open(local_path, 'wb') as img:
                        for chunk in res.iter_content(1024):
                            img.write(chunk)

                    logging.debug('uploading img:{}'.format(f_name))
                    that.__upload_oss(f_name, local_path, multi)
                except IOError as e:
                    logging.error('mkdir {} occurred IO exception: {}'.format(img_temp_dir, e))
                except Exception as e:
                    logging.error('def up2oss(res, *args, **kwargs): Exception: {}'.format(e))

        requests.get(url, hooks={'response': up2oss})

    def download_img_up2oss(self, url, f_name, multipart_threshold=None):
        """
        使用线程池下载图片，创建需求并添加至线程池
        :param url: 下载图片地址
        :param f_name: 保存的文件名（ossBasePath + hash）
        :param multipart_threshold: 分片上传参数（k）
        """
        self.executor.submit(self.__do_download_img_up2oss, url, f_name, multipart_threshold)
