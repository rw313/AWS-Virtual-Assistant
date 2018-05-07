#import imp
#import sys
#from PIL import Image
#import PIL.Image
#sys.modules["sqlite"] = imp.new_module("sqlite")
#sys.modules["sqlite3.dbapi2"] = imp.new_module("sqlite.dbapi2")
from nltk.tokenize import sent_tokenize
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from bs4 import BeautifulSoup
import feedparser 
import time
from newspaper import Article
import pymysql
#from botocore.vendored import requests
import urllib.request
import json  

rds_host  = "contentenginedb.ctpsr3h9wg8h.us-east-1.rds.amazonaws.com"
name = "cedbroot"
password = "cedbpassword"
db_name = "contentengine"

conn = pymysql.connect(rds_host, user=name, passwd=password, db=db_name, charset='utf8')

def pollSources():
    cursor = conn.cursor() 
    cursor.execute("SELECT sourceId, sourceName, type, endpoint, parseCmd, lastProcessed from sources")
    rows = cursor.fetchall()
    json = [] #a list of 10 dicts holding article info, rank, etc 
    for row in rows:
        source = dict() 
        source["sourceId"] = row[0]
        source["sourceName"] = row[1]
        source["type"] = row[2] 
        source["endpoint"] = row[3]
        source["parseCmd"] = row[4]
        source["lastProcessed"] = row[5]
        
        #check if lastprocessed and source endpoint.updated is valid? 
        print("Processing source: " + source["sourceName"])
        
        if source["type"] == "rss": 
            json += processRSS(source) #processSource should return a dict object 
        elif source["type"] == "api":
            json += processAPI(source)
            
    #update last processed timestamp in sources 
    #print(json)

def parseField(entity):
    if entity:
        return entity.encode('unicode-escape').replace(b'"', b'\\"').replace(b'\'', b"\\'").decode("ascii")
    return ""

def processAPI(source):
    results = []
    
    f = urllib.request.urlopen(source["endpoint"])
    data = json.loads(f.read().decode('utf-8'))
    articles = data["articles"] 
    values = ""
    for a in articles:
        result = dict()
        result["sourceName"] = parseField(a["source"]["name"])
        result["title"] = parseField(a["title"])
        result["link"] = a["url"] 
        result["img"] = a["urlToImage"]
        result["datePublished"] = time.strftime('%Y-%m-%d %H:%M:%S' , time.strptime(a["publishedAt"], "%Y-%m-%dT%H:%M:%SZ")) if a["publishedAt"] else ""
        result["author"] = parseField(a["author"]) 

        article = Article(a["url"])
        try:
            article.download()
            article.parse() 
            article.nlp()
        except:
            print("Had trouble downloading link") 
            continue
        
        sentences_list = sent_tokenize(article.text)[1:5]
        result["description"] = parseField(' '.join(sentences_list))
        result["summary"] = parseField(article.summary) 
        result["keywords"] = article.keywords
        
        sid = SentimentIntensityAnalyzer() 
        ss = sid.polarity_scores(a["title"]) 
        result["compound"] = ss["compound"]
        result["neg"] = ss["neg"]
        result["pos"] = ss["pos"]
        result["neu"] = ss["neu"] 
        
        results.append(result)

        print(".....Article: " + result["title"])
        
        values += " ('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', {}, {}, {}, {}),".format(result["title"], 
                                                                source["sourceId"], 
                                                                result["link"], 
                                                                result["img"], 
                                                                result["author"], 
                                                                result["summary"], 
                                                                result["datePublished"],
                                                                result["description"],
                                                                " ".join(article.keywords).encode('unicode-escape').replace(b'"', b'\\"').replace(b'\'', b"\\'").decode("ascii"),
                                                                result["compound"], result["neg"], result["neu"], result["pos"])
    insertToArticles(values)
    return results

def insertToArticles(values):
    if len(values) == 0: 
        return 
    cursor = conn.cursor()
    sql = """INSERT IGNORE into Articles (`title`,`sourceId`, `link`, 
    `img`, `author`, `summary`, `datePublished`, `description`, `keywords`,
    `compound`, `neg`, `neu`, `pos`
    ) 
    VALUES {}""".format(values[0:-1]) 
    cursor.execute(sql) 
    conn.commit()

def articleExists(link):
    cursor = conn.cursor() 
    sql = "SELECT COUNT(1) from Articles WHERE link='"+link+"'"
    cursor.execute(sql)
    return cursor.fetchone()[0] 

def processRSS(source): 
    results = []
    feed = feedparser.parse(source["endpoint"])
    #feedLastUpdated = feed.date #use updated_parsed for date obj
    #if feedLastUpdated > source["lastProcessed"] 
    values = ""
    for entry in feed.entries:
        if articleExists(entry.link):
            print("..........Already in DB: " + entry.title)
            continue 
        
        result = dict()
        result["sourceName"] = source["sourceName"]
        result["title"] = parseField(entry.title)
        result["link"] = entry.link
        
        article = Article(entry.link)
        try:
            article.download()
            article.parse()
            article.nlp()
        except Exception as e: 
            print(e)
            print("Had trouble downloading" ) 
            continue 
        
        result["img"] = article.top_image 
        result["datePublished"] = time.strftime('%Y-%m-%d %H:%M:%S' , entry.published_parsed) if entry.published_parsed else ""
        result["summary"] = parseField(article.summary)
        sentences_list = sent_tokenize(article.text)[1:5]
        result["description"] = parseField(' '.join(sentences_list))
        
        sid = SentimentIntensityAnalyzer() 
        ss = sid.polarity_scores(entry.title) 
        result["compound"] = ss["compound"]
        result["neg"] = ss["neg"]
        result["pos"] = ss["pos"]
        result["neu"] = ss["neu"] 
                
        result["author"] = parseField(entry.author)
        result["keywords"] = article.keywords
        results.append(result) 

        print(".....Article: " + result["title"])
        
        values += " ('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', {}, {}, {},  {}),".format(result["title"], 
                                                                    source["sourceId"], 
                                                                    result["link"], 
                                                                    result["img"], 
                                                                    result["author"], 
                                                                    result["summary"], 
                                                                    result["datePublished"],
                                                                    result["description"],
                                                                    " ".join(article.keywords).encode('unicode-escape').replace(b'"', b'\\"').replace(b'\'', b"\\'").decode("ascii"),
                                                                    result["compound"], result["neg"], result["neu"], result["pos"])
    
    insertToArticles(values)
    return results

if __name__ == "__main__":
    while (True):
        pollSources()  
        print("Finished polling sources")
        time.sleep(120)  