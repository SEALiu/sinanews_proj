import logging
import re

from urllib import parse
from scrapy.http import Request
from sinanews_proj.items import SinaNewsLoader, SinaNewsItem, SinaNewsCommentLoader, SinaNewsCommentItem, \
    SinaUserLoader, SinaUserItem
from sinanews_proj.spiders.MyRefererSpider import MyRefererSpider
from sinanews_proj.util import JsonUtil, RedisUtil


class SinaNewsSpider(MyRefererSpider):
    name = 'sina_news_spider'
    # sadd sina_news_spider:start_urls https://edu.sina.cn/
    redis_key = 'sina_news_spider:start_urls'
    oss_base_path = 'img/news/sina/'
    oss_profile_path = 'img/profile_image/'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.redis_conn = RedisUtil.connect()

    def parse(self, response):
        logging.debug('response url:{}'.format(response.url))
        # print("response url:{}".format(response.url))

        if JsonUtil.is_json(response.text):
            logging.debug('response[{}]\'s format is json'.format(response.url))
            # response 为异步 ajax 请求，将其返回结果转成 json 对象，然后交给 json_parse 处理

            if response.url:
                yield from self.json_parse(response=response)

        else:
            # response 为网页
            logging.debug('response[{}]\'s format is html'.format(response.url))
            top_nav_urls = response.xpath(
                "//section[@id='j_comment_nav1']//nav/a[starts-with(@href, 'http://edu.sina.cn/')]/@href").extract()
            article_title = response.xpath("//h1[@class='art_tit_h1']/text()").extract()
            comment_head = response.xpath("//a[@title='评论']").extract()

            if top_nav_urls:
                # 当前爬取的是新浪新闻的教育首页（https://edu.sina.cn）
                # 就把 https://edu.sina.cn  页面顶部的导航链接加入 redis（sina_news_spider:start_urls） 中
                for url in top_nav_urls:
                    RedisUtil.set_add(self.redis_conn, self.redis_key, url)
                    # print("home-navUrl:{}".format(url))

                # 构造页面的异步请求url，并添加至 redis（sina_news_spider:start_urls）中
                # 首页的异步请求不是分页请求的，每次请求都是不同的数据，即：首页是实现了无限滚动，可能包含重复内容
                # 应该将这个url一直保留在 redis（sina_news_spider:start_urls）中
                regex = r'\"(//cre.dp.sina.cn[\w/\?=&]*)\"\,[\s\r\n\w:\",{}]*channel[\s:]+([\d]+)\,'
                matches = re.search(regex, response.text, re.MULTILINE)
                if matches and len(matches.groups()) == 2:
                    '''需要构造的api-url结构：
                    https:
                    //cre.dp.sina.cn/api/v3/get?cateid=I&cre=tianyi&mod=wedu&merge=3&statics=1&length=20&tm=1489716199
                    &ad={channel:130270}
                    &action=1
                    '''
                    api_url = 'https:' + matches.group(1) + '&ad={channel:' + matches.group(2) + '}&action=1'
                    RedisUtil.set_add(self.redis_conn, self.redis_key, api_url)
                    # print("home-infiniteApi:{}".format(api_url))
                else:
                    logging.error('can not find {} in html[{}]'.format(regex, response.url))

            elif article_title:
                yield from self.article_parse(response)
            elif comment_head:
                regex = r'getcomments[:\s]+\'([\W\w]*?)\','
                matches = re.search(regex, response.text, re.MULTILINE)
                if matches:
                    '''
                    构造新闻的评论接口
                    https://cmnt.sina.cn/aj/v2/list?channel=wj&newsid=comos-hqhqcir7468558&group=0&thread=1&page=1
                    
                    request header:
                    Referer: response.url
                    '''

                    url_info = parse.urlparse(response.url)
                    comment_api_url = '{}://{}{}'.format(url_info.scheme, url_info.netloc, matches.group(1))

                    # 保证commentApiUrl中存在： &page=1
                    comment_api_url = re.sub(r'&?page=\d+', '', comment_api_url)
                    comment_api_url = comment_api_url + '&page=1'

                    request = Request(comment_api_url, callback=self.parse, headers={'referer': response.url})
                    # print('comment request====================>: {}'.format(request.headers))
                    yield request

            else:
                # 当前爬取的是新浪新闻的教育分类页面
                # MBA 和移民栏目的异步请求 url 和其他页不同

                # 获取当前分类下的子分类id，用于构造异步请求的url
                sub_type_ids = response.xpath("//ul[@id='j_nav_main']/li/@id").extract()
                if sub_type_ids:
                    # 获取页面上方的几篇孤立文章的url，添加至待爬取队列 redis（sina_news_spider:start_urls）中
                    separated_url = response.xpath(
                        "//div[@class='-live-page-widget']/section[contains(@class, 'card_module')]/section/a/@href") \
                        .extract()
                    if separated_url:
                        for url in separated_url:
                            yield Request(url, callback=self.parse)

                    # 构造页面的异步请求url，并添加至 redis（sina_news_spider:start_urls）中
                    regex = r'\'(//interface.sina.cn/[\w/.?&=]*)\'\,'
                    matches = re.search(regex, response.text, re.MULTILINE)
                    # matches.groups()
                    # group-1: api-url(异步请求url)
                    for col in sub_type_ids:
                        regex_col = r'([\d]+)'
                        matches_col = re.search(regex_col, col, re.DOTALL)

                        if matches_col and matches and matches.group(1):
                            '''需要构造的 api-url 结构：
                            https://interface.sina.cn/wap_api/layout_col.d.json?&showcid=78163
                            &col=78175
                            &show_num=30
                            &page=1
                            '''
                            api_url = 'https:' + matches.group(1) + '&col=' + matches_col.group(1) + '&page=1'
                            RedisUtil.set_add(self.redis_conn, self.redis_key, api_url)
                            # print("subtype-apiUrl:{}".format(api_url))
                else:
                    # MBA 和移民栏目的子分类 id 获取方式不同
                    sub_type_ids_another = response.xpath(
                        "//section[contains(@id, 'tabnews_conf')]//ul/li/@data-cat").extract()

                    regex_json_data = r'data\[\'tabnews_conf[_\d]+\'\][\s=]+([\{\}\[\]\"\w:,\\/.\-\s?=&%]+);'
                    matches_json_data = re.search(regex_json_data, response.text, re.MULTILINE)

                    '''需要从页面 <script></script> 中提取的 api-url 结构
                    MBA：http://interface.sina.cn/ent/subject_spot_news.d.json?subjectID=201214&domainprefix=edu&show=&modelID=
                    移民：http://interface.sina.cn/ent/subject_spot_news.d.json?subjectID=201887&domainprefix=edu&show=&modelID=
                    &cat=all
                    &page=1
                    
                    还需要从 <script></script> 中提取的 json 数据
                    '''
                    if matches_json_data and matches_json_data.group(1) and JsonUtil.is_json(
                            matches_json_data.group(1)):
                        json_data = JsonUtil.parse(matches_json_data.group(1))

                        if 'load_api' in json_data:
                            # 转化正确！继续处理 json 数据中的内容
                            json_data['request_url'] = response.url
                            self.json_parse(json_data=json_data)

                            # 构造页面的异步请求url，并添加至 redis（sina_news_spider:start_urls）中
                            for cat in sub_type_ids_another:
                                api_url = json_data['load_api'] + '&cat=' + cat + '&page=1'
                                RedisUtil.set_add(self.redis_conn, self.redis_key, api_url)
                                # print("subtype-apiUrl(移民/MBA):{}".format(api_url))

    def json_parse(self, response=None, json_data=None):
        # parse json-data
        if json_data:
            value = json_data
        elif response:
            value = JsonUtil.parse(response.text)
            value['request_url'] = response.url
        else:
            logging.error('json_parse() 需要至少一个参数：response  jsondata')
            # print('json_parse() 需要至少一个参数：response  jsondata')
            return

        # 由于该函数需要处理多种异步请求方式返回的 json 数据，所以需要根据 value['request_url'] 进行判断：
        # print('request_url:{}'.format(value['request_url']))

        # 首页
        regex_1 = r'https?://cre.dp.sina.cn/api[\w.?=&%-/:]*'
        # 分类页面
        regex_2 = r'https?://interface.sina.cn/wap_api/layout_col.d.json[\w.?=&%-]*'
        # 移民/MBA
        regex_3 = r'https?://interface.sina.cn/ent/subject_spot_news.d.json[\w.?=&%-]*'
        # 评论页面
        regex_4 = r'https?://cmnt.sina.cn/aj/v2/list[\w.?=&%-]*'

        match_1 = re.search(regex_1, value['request_url'], re.MULTILINE)
        match_2 = re.search(regex_2, value['request_url'], re.MULTILINE)
        match_3 = re.search(regex_3, value['request_url'], re.MULTILINE)
        match_4 = re.search(regex_4, value['request_url'], re.MULTILINE)

        if match_1:
            # 首页
            # 首页的 ajax-URL 不需要修改参数，每次请求都是不同的数据
            logging.debug('首页 ajax-URL:{}'.format(value['request_url']))
            RedisUtil.set_add(self.redis_conn, self.redis_key, value['request_url'])

            # 解析 json
            # json 格式参考：../scrapy_proj/helper_doc/ajax_response_sample/sina.home.json
            for data in value['data']:
                article_url = data['surl'] if 'surl' in data else ''
                if article_url is not '':
                    yield Request(article_url, callback=self.parse)
                    logging.debug('add 首页 ajax-URL//article_url:{} to queue'.format(article_url))
        elif match_2:
            # 分类页面
            # 如果 json 中的数据部分不为空，则让页数加一后，将 url 添加至 redis 中
            # https://interface.sina.cn/wap_api/layout_col.d.json?&showcid=78163&col=78175&show_num=30&page=1
            # json 格式参考：../scrapy_proj/helper_doc/ajax_response_sample/subtype.json
            if len(value['result']['data']['list']) != 0:
                api_url = re.sub(r'page=(\d+)', lambda m: 'page={}'.format(int(m.group(1)) + 1), value['request_url'])
                RedisUtil.set_add(self.redis_conn, self.redis_key, api_url)
                # print("subtype-apiUrl-nextPage:{}".format(api_url))

                # 解析 json
                for item in value['result']['data']['list']:
                    article_url = item['URL'] if 'URL' in item else ''
                    if article_url is not '':
                        yield Request(article_url, callback=self.parse)
                        logging.debug('add 分类页面 article_url:{} to queue'.format(article_url))
        elif match_3:
            # 移民/MBA
            # http://interface.sina.cn/ent/subject_spot_news.d.json?subjectID=201887&domainprefix=edu&show=&modelID=&cat=all&page=1
            if len(value['data']) == 0:
                api_url = re.sub(r'page=(\d+)', lambda m: 'page={}'.format(int(m.group(1)) + 1), value['request_url'])
                RedisUtil.set_add(self.redis_conn, self.redis_key, api_url)
                # print("subtype-apiUrl(移民/MBA)-nextPage:{}".format(api_url))

                # 解析 json
                for data in value['data']:
                    article_url = data['url'] if 'url' in data else ''
                    if article_url is not '':
                        yield Request(article_url, callback=self.parse)
                        logging.debug('add 移民/MBA article_url:{} to queue'.format(article_url))

        elif match_4:
            # print('评论页面 ajax-URL============================>:{}'.format(value['request_url']))
            logging.debug('评论页面 ajax-URL:{}'.format(value['request_url']))

            if len(value['result']['cmntlist']) != 0:
                api_url = re.sub(r'page=(\d+)', lambda m: 'page={}'.format(int(m.group(1)) + 1), value['request_url'])
                RedisUtil.set_add(self.redis_conn, self.redis_key, api_url)
                # print("comment-apiUrl-nextPage:{}".format(api_url))
                # print("评论页面的下一页url：================================>{}".format(apiUrl))

            # 解析 json
            yield from self.comment_parse(response)

    def article_parse(self, response):
        # 解析文章页面，从文章详情页面可以获得内容有：
        # 文章标题、内容、类型、源地址
        # 发布者的微博号id，昵称
        # 评论页面的 url
        logging.debug('parsing article:{}'.format(response.url))

        # 将文章下的评论页面添加至 redis 待爬取队列
        regex_comment = r'\"__cmntListUrl\"[:\s]\"([\w\W]*?)\",'
        match = re.search(regex_comment, response.text, re.MULTILINE)
        if match:
            comment_api = str.replace(match.group(1), '\\', '')
            RedisUtil.set_add(self.redis_conn, self.redis_key, comment_api)
            # print("comment-apiUrl:{}".format(comment_api))

        # 将微博账户页面添加至 redis 待爬取队列
        author_id = response.xpath("//figure[@class='weibo_info look_info']/attribute::data-uid").extract()
        author_name = response.xpath("//meta[@property='article:author']/@content").extract()
        # authorUrl = 'https://m.weibo.cn/u/' + author_id if author_id else ''
        # RedisUtil.set_add(self.redis_conn, self.redis_key, authorUrl)

        # 处理文章的基本信息
        regex_news_id = r'[\"\']{0,1}newsid[\"\']{0,1}[\s:]+[\"\']{0,1}([\w\W]+?)[\"\']{0,1},'
        match_news_id = re.search(regex_news_id, response.text, re.MULTILINE)

        item_loader = SinaNewsLoader(item=SinaNewsItem(), response=response)

        if match_news_id:
            item_loader.add_value('news_id', match_news_id.group(1))

        item_loader.add_xpath('type', "//h2[@class='hd_tit_l']/a/@title")
        item_loader.add_xpath('title', "//title/text()")
        item_loader.add_value('author_id', author_id)
        item_loader.add_value('author_name', author_name)
        item_loader.add_xpath('intro', "//meta[@name='description']/@content")
        item_loader.add_value('content',
                              {'html': response.text, 'url': response.url, 'ossPath': SinaNewsSpider.oss_base_path})
        item_loader.add_value('url', response.url)
        item_loader.add_xpath('time', "//meta[@property='article:published_time']/@content")
        item_loader.add_xpath('key_word', "//meta[@name='keywords']/@content")

        item = item_loader.load_item()
        yield item

        # 处理文章发布者的信息
        profile_img = response.xpath("//figure[@class='weibo_info look_info']//img/@src").extract_first()

        user_loader = SinaUserLoader(item=SinaUserItem(), response=response)
        user_loader.add_value('uid', author_id)
        user_loader.add_value('nickname', author_name)
        user_loader.add_value('profile_img',
                              {'src': profile_img, 'url': response.url, 'ossPath': SinaNewsSpider.oss_profile_path})

        yield user_loader.load_item()

    def comment_parse(self, response):
        """
        todo 解析评论接口的返回json数据，从评论json中获取：评论人，时间，评论内容，地理位置，点赞数，评论回复数
        :param response:
        """
        value = JsonUtil.parse(response.text)
        value['request_url'] = response.url
        request_url = value['request_url']

        # 处理评论的基本信息，普通评论和热门评论

        # 普通评论
        for cmnt in value['result']['cmntlist']:
            # 解析评论人的信息
            user_loader = SinaUserLoader(item=SinaUserItem(), response=response)
            user_loader.add_value('uid', cmnt['uid'])
            user_loader.add_value('nickname', cmnt['nick'])
            user_loader.add_value('profile_img',
                                  {'src': cmnt['profile_img'], 'url': request_url,
                                   'ossPath': SinaNewsSpider.oss_profile_path})
            user_loader.add_value('location', cmnt['area'])

            user_item = user_loader.load_item()
            yield user_item

            # 解析评论内容
            comment_loader = SinaNewsCommentLoader(item=SinaNewsCommentItem(), response=response)
            comment_loader.add_value('comment_id', cmnt['mid'])
            comment_loader.add_value('user_id', cmnt['uid'])
            comment_loader.add_value('nickname', cmnt['nick'])
            comment_loader.add_value('ip', cmnt['ip'])
            comment_loader.add_value('location', cmnt['area'])
            comment_loader.add_value('time', cmnt['time'])
            comment_loader.add_value('content', cmnt['content'])
            # 评论类型（0:对文章内容评论，1:对其他用户的内容进行评论）
            comment_loader.add_value('comment_type', 0)
            comment_loader.add_value('news_id', cmnt['newsid'])
            comment_loader.add_value('like_num', cmnt['agree'])

            # 这条评论的回复
            if cmnt['mid'] in value['result']['threaddict']:
                replies = value['result']['threaddict'][cmnt['mid']]
                if replies:
                    comment_loader.add_value('reply_num', replies['count'])
                    for reply in replies['list']:
                        # 解析回复人的信息
                        replier_loader = SinaUserLoader(item=SinaUserItem(), response=response)
                        replier_loader.add_value('uid', cmnt['uid'])
                        replier_loader.add_value('nickname', cmnt['nick'])
                        replier_loader.add_value('profile_img',
                                                 {'src': cmnt['profile_img'], 'url': request_url,
                                                  'ossPath': SinaNewsSpider.oss_profile_path})
                        replier_loader.add_value('location', cmnt['area'])

                        replier_item = replier_loader.load_item()
                        yield replier_item

                        # 解析回复内容
                        reply_loader = SinaNewsCommentLoader(item=SinaNewsCommentItem(), response=response)
                        reply_loader.add_value('comment_id', reply['mid'])
                        reply_loader.add_value('user_id', reply['uid'])
                        reply_loader.add_value('nickname', reply['nick'])
                        reply_loader.add_value('ip', reply['ip'])
                        reply_loader.add_value('location', reply['area'])
                        reply_loader.add_value('time', reply['time'])
                        reply_loader.add_value('content', reply['content'])
                        reply_loader.add_value('comment_type', 1)
                        reply_loader.add_value('reply_id', reply['parent'])
                        reply_loader.add_value('news_id', reply['newsid'])
                        reply_loader.add_value('like_num', reply['agree'])

                        reply_item = reply_loader.load_item()
                        yield reply_item

            comment_item = comment_loader.load_item()
            yield comment_item
