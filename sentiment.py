import time
import json
import urllib2
from pymongo import Connection

class Sentiment:
    BASE_URL = "http://api.contextvoice.com/1.2/mentions/search/mongo/?q=%(q)s&count=100&apikey=%(apikey)s"
    def __init__(self, apikey, q, sleep=0):
        self.apikey = apikey
        self.q = q
        self.sleep = sleep
        self.url = self.BASE_URL % {"apikey": apikey, "q": q}
        
    def connect(self, host, port, database):
        self.con = Connection(host, port)
        self.db = self.con[database]

    def initialize(self):
        self.stocks = list(self.db.stock.find())
        print self.stocks
        for stock in self.stocks:   
            stock["keywords_str"] = " ".join(stock["keywords"])
            stock["sentiment"] = self.db.sentiment.find_one({"stock_id": stock["_id"]})
            if stock["sentiment"] is None:
                stock["sentiment"] = {
                    "stock_id"  : stock["_id"],
                    "daily"      : []
                }
        
    def run(self):
        self.initialize()
        while True:
            for stock in self.stocks:
                print "Restart!"
                self._query(stock)       
            time.sleep(self.sleep)
            
    def _query(self, stock):
        print stock["name"]
        mentions = []
        since = None if len(stock["sentiment"]["daily"])==0 \
                else stock["sentiment"]["daily"][-1]["time"]
        since_param = "" if since is None else "&since=%d"% since
        until = None
        until_param = ""
        for i in xrange(100):
            url = self.url + since_param + until_param
            paged_mentions = json.loads(urllib2.urlopen(url).read())["results"]
            if len(paged_mentions) == 0: break
            if (paged_mentions[-1]["published"] == until): break
            until = paged_mentions[-1]["published"]
            until_param = "&until=%d" % paged_mentions[-1]["published"]
            mentions.extend(paged_mentions)
            
        self._append(stock, mentions)
        
    def _append(self, stock, mentions):
        for i in xrange(len(mentions)-1, -1, -1):
            mention = mentions[i]
            if not mention.has_key("sentiment"): continue
            if len(stock["sentiment"]["daily"]) > 0 \
            and Sentiment._same_date(mention["published"], stock["sentiment"]["daily"][-1]["time"]):
                stock["sentiment"]["daily"][-1][mention["sentiment"]] += 1
            else:
                t = {
                    "time": Sentiment._date_round(mention["published"]), 
                    "positive": 0, 
                    "negative": 0, 
                    "neutral": 0, 
                    "none": 0
                }
                t[mention["sentiment"]] += 1
                stock["sentiment"]["daily"].append(t)
    
        if stock["sentiment"].has_key("_id"):
            self.db.sentiment.update({"_id": stock["sentiment"]["_id"]}, stock["sentiment"])
        else:
            self.db.sentiment.insert(stock["sentiment"])
    
    @staticmethod
    def _same_date(d1, d2):
        return Sentiment._date_round(d1)==Sentiment._date_round(d2)
        
    @staticmethod
    def _date_round(d):
        return d - (d % (24*3600))
    
    def test(self):
        pass
        
if __name__ == "__main__":
    sentiment = Sentiment("759e4dda83db9853484569458464b990", "ipad")
    sentiment.connect("109.123.66.160", 27017, "instatrade")
    sentiment.run()
