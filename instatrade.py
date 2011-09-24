import markdown
import os.path
import re
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
from pymongo import Connection

import datetime
print(datetime.datetime.fromtimestamp(int("1284101485")).strftime('%Y-%m-%d %H:%M:%S'))

from tornado.options import define, options

define("port", default=8888, help="run on the given port", type=int)

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", HomeHandler),
            (r"/tag/([^/]+)", StockHandler)
        ]
        settings = dict(
            blog_title=u"Instatrade",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            ui_modules={"Entry": EntryModule},
            xsrf_cookies=True,
            cookie_secret="11oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=",
            login_url="/auth/login",
            autoescape=None,
            con = Connection('109.123.66.160', 27017),
            
        )
        tornado.web.Application.__init__(self, handlers, **settings)

        # Have one global connection to the blog DB across all handlers
        self.db = self.settings['con']["instatrade"]


class BaseHandler(tornado.web.RequestHandler):
    @property
    def db(self):
        return self.application.db

class HomeHandler(BaseHandler):
    def get(self):
        entries = list(self.db.stock.find())
        if not entries:
            return self.render_string("No entries")
        self.render("home.html", entries=entries)

class EntryHandler(BaseHandler):
    def get(self, name):
        entry = list(self.db.values.find({'name': name}))[0]
        if not entry: raise tornado.web.HTTPError(404)
        self.render("entry.html", entry=entry)

class EntryModule(tornado.web.UIModule):
    def render(self, entry):
        return self.render_string("modules/entry.html", entry=entry)

class StockHandler(BaseHandler):
    def get(self, name):
        stock = list(self.db.stock.find({'name': name}))[0]
        #values = list(self.db.values.find({'stock_id': stock['_id']}))[0]
        sentiment = list(self.db.sentiment.find({'stock_id': stock['_id']}))[0]
        for day_sentiments in sentiment['daily']:
            day_sentiments['time'] = datetime.datetime.fromtimestamp(int(day_sentiments['time'])).strftime('%Y-%m-%d')
        # if not values: raise tornado.web.HTTPError(404)
        self.render("stock.html", stock=stock, sentiment=sentiment)

def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
