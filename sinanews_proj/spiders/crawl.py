from twisted.internet import reactor, defer
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from sinanews_proj.spiders.SinaNewsSpider import SinaNewsSpider
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from multiprocessing import Process


def crawler_p():
    crawler = CrawlerProcess(get_project_settings())

    def _crawl():
        crawler.crawl(SinaNewsSpider)
        crawler.start()
        crawler.stop()

    p = Process(target=_crawl)
    p.start()
    p.join()


def crawler_r():
    configure_logging({'LOG_FORMAT': '%(levelname)s: %(message)s'})
    runner = CrawlerRunner(get_project_settings())
    runner.crawl(SinaNewsSpider)
    d = runner.join()
    defer.DeferredList(d).addBoth(lambda _: reactor.stop())
    reactor.run()
    # the script will block here until all crawling jobs are finished


# this method can fix 'ReactorNotRestartable' problem
# use this!!!!
def crawler_d():
    configure_logging({'LOG_FORMAT': '%(levelname)s: %(message)s'})
    runner = CrawlerRunner(get_project_settings())

    @defer.inlineCallbacks
    def crawl():
        yield runner.crawl(SinaNewsSpider)
        reactor.stop()

    crawl()
    reactor.run()
    # the script will block here until the last crawl call is finished
