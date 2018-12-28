import json


class JsonUtil(object):
    """
    Json 工具类
    """

    @staticmethod
    def is_json(string):
        """
        判断 string 是否属于 json
        :param string: 一个字符串
        :return: True or False (是否属于 json)
        """
        try:
            json.loads(string, strict=False)
        except ValueError:
            return False
        return True

    @staticmethod
    def parse(string):
        """
        将 string 转化为 python 的 json 对象
        :param string: 一个字符串
        :return: python 的 json 对象，如果 string 不符合 json 格式，则返回错误信息（json）
        """
        if JsonUtil.is_json(string):
            return json.loads(string, strict=False)
        else:
            return json.loads('{"status":"error","msg":"the string given is not json-format"}')
