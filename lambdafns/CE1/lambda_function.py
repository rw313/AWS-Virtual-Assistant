import sys
import pymysql
import boto3  
import imp, sys, os, re, time
from botocore.vendored import requests
from datetime import datetime as dt  
import json 
from botocore.exceptions import ClientError
import time 

from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.metrics.pairwise import linear_kernel
#rds settings 
rds_host  = "contentenginedb.ctpsr3h9wg8h.us-east-1.rds.amazonaws.com"
name = "cedbroot"
password = "cedbpassword"
db_name = "contentengine"

ACCESS_KEY = "AKIAIJPM437OILLSOWCA" #AWS_ACCESS_KEY 
SECRET_KEY = "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" #AWS_SECRET_KEY
REGION = "us-east-1"  #AWS_DEFAULT_REGION 

conn = pymysql.connect(rds_host, user=name, passwd=password, db=db_name, connect_timeout=5)
print("Connected to DB")

def processQueue(): 
    sqs = boto3.client('sqs',
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        region_name=REGION
    )
    queue_url = 'https://sqs.us-east-1.amazonaws.com/073632995568/assistantcat'
    
    response = sqs.receive_message(
        QueueUrl=queue_url,
        AttributeNames=[
            'SentTimestamp'
        ],
        MaxNumberOfMessages=5,
        MessageAttributeNames=[
            'All'
        ],
        VisibilityTimeout=0,
        WaitTimeSeconds=3 
    )
    if response == None or 'Messages' not in response or len(response['Messages']) == 0:
        return {}
    
    message = response['Messages'][0]
    receipt_handle = message['ReceiptHandle'] 
    print(message) 
    slots = message['MessageAttributes']  
    emailrecipient = slots['email']['StringValue'] 
    fullname = slots['firstname']['StringValue']  + " " + slots['lastname']['StringValue'] 
    interests = slots['interests']['StringValue'].split(", ")
    userid = slots['userID']['StringValue']
    ktc = json.loads(slots['keywordToContacts']['StringValue'])
    friendid = -1 #slots['contactID']['StringValue'] 
    
    emailMsg = "Hi " + fullname + "! Based on the interests of your friends, here are the articles ranked by relevance." 
    
    for query in interests:
        rankedArticles = rank(interests, userid, friendid)
        for ac in rankedArticles:
            acHtml = "<div id="+str(ac["articleId"])+">"
            acHtml += "<b style='color:#FF69B4'>"+"("+ac["sourceName"]+") "+ac["title"]+": </b>" 
            acHtml += "<p style='font-size:8px;color=#787878'>By: "+ac["author"] 
            #acHtml += ", Date: "+ac["datePublished"].strftime("%Y-%m-%d %H:%M:%S") if ac["datePublished"] is not None else "N/A" +"</p>" 
            acHtml += "<p style='font-size:10px;color=#444'>"+ac["description"]+"</p>" 
            acHtml += "<p style='font-size:5px;color=#787878'>"+" or ".join(ktc[query] if query in ktc else ["Someone"])+" might be interested</p>" 
            acHtml += "<a style='font-weight:normal;text-decoration:none' href='"+ac["link"]+"'>"
            acHtml += "<img style='height:150px' src='"+ac["img"]+"'/>" 
            acHtml += "</a>"+"</div><hr/> " 
            emailMsg += acHtml 
        
    sendEmail(emailrecipient, emailMsg)
    sqs.delete_message(
        QueueUrl=queue_url,
        ReceiptHandle=receipt_handle
    )
    print('Received and deleted message: %s' % slots)    
    return receipt_handle 

def rank(query, userid, friendid): 
    return rankArticles(query, userid, friendid) #request.args.getlist(<paramname>)

def rankArticles(query, userid, friendid):
    cursor = conn.cursor()
    unseenArticlesSql = """ SELECT Articles.articleId, keywords, description, title, link 
    from Articles left join ArticleShares on Articles.articleId = ArticleShares.articleId 
    where !(ArticleShares.userSeenDate IS NOT NULL and ArticleShares.userId='{}') 
    """.format(userid)
    
    cursor.execute(unseenArticlesSql)
    rows = cursor.fetchall()
    articles = [] 
    for row in rows:
        article = dict() 
        article["articleId"] = row[0]
        article["keywords"] = row[1] if row[1] is not None else "N/A"
        article["description"] = row[2]  if row[2] is not None else "N/A"
        article["title"] = row[3]
        article["link"] = row[4] 

        articles.append(article)  
    return getMatches(query, articles, userid)

def getMatches(queries, articles, userid): 
    results = [] 
    if not queries or len(queries) < 1:
        return "couldn't parse query parameter"
    for query in queries:
        data_samples = [query] 
        for i in range(0, len(articles)):
            data_samples.append(articles[i]["title"]) #+ articles[i]["keywords"]+articles[i]["description"])

        tfidf_vectorizer = TfidfVectorizer(stop_words='english')
        tfidf = tfidf_vectorizer.fit_transform(data_samples) 
        cosine_similarities = linear_kernel(tfidf[0:1], tfidf).flatten() #replace first param with query 
        related_docs_indices = cosine_similarities.argsort()[:-3:-1]
        
        for j in range(1, len(related_docs_indices)):
            results.append(str(articles[related_docs_indices[j]-1]["articleId"]))
    print(results)
    return fetchRelevantRows(results, userid)

def fetchRelevantRows(results, userid):
    cursor = conn.cursor()
    
    if not results or len(results) < 1:
        return [] 
    
    fetchRelevantRows = """SELECT articleId, keywords, description, title, link, 
    img, author, datePublished, contentengine.Articles.sourceId as sId, sourceName 
    from contentengine.Articles 
    left join contentengine.sources on contentengine.sources.sourceId = contentengine.Articles.sourceId 
    where articleId in ({}) 
    """.format(','.join(results)) 
    print(fetchRelevantRows)
    cursor.execute(fetchRelevantRows)
    rows = cursor.fetchall() 
    
    articles = [] 
    for row in rows:
        article = dict() 
        article["articleId"] = row[0]
        article["keywords"] = row[1]  if row[1] is not None else "N/A"
        article["description"] = row[2]  if row[2] is not None else "N/A"
        article["title"] = row[3]  if row[3] is not None else "N/A"
        article["link"] = row[4]  if row[4] is not None else "N/A"
        article["img"] = row[5] if row[5] is not None else "N/A"
        article["author"] = row[6]  if row[6] is not None else "N/A"
        article["datePublished"] = row[7]  
        article["sId"] = row[8]  if row[8] is not None else "N/A"
        article["sourceName"] = row[9]  if row[9] is not None else "N/A" 
        articles.append(article) 
        
        sql = '''Insert into `contentengine`.`ArticleShares` (`articleId`, `userSeenDate`, `userId`)  
            VALUES ({}, NOW(), '{}') on duplicate key update `userSeenDate`=NOW();'''.format(str(row[0]), str(userid))
        cursor.execute(sql) 
    conn.commit()   
    return articles
    
def sendEmail(email, HTML): 
    # This address must be verified with Amazon SES.
    SENDER = "Assistant Cat <rachelwu343@gmail.com>" 
    RECIPIENT = email  
    #CONFIGURATION_SET = "ConfigSet"
    AWS_REGION = "us-east-1" 
    SUBJECT = "Your Custom Headlines for today" 
    BODY_TEXT = HTML 
                
    BODY_HTML = """<html>
    <head>
    <style>
        @import url(http://fonts.googleapis.com/css?family=Roboto:100,300,400,600);
        body > * { font-family: 'Roboto', sans-serif; } 
    </style>
    </head>
    <body>
      """+HTML+"""
    </body>
    </html> """            
    
    CHARSET = "UTF-8"
    
    client = boto3.client('ses',
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        region_name=REGION)
    
    try:
        #Provide the contents of the email.
        response = client.send_email(
            Destination={
                'ToAddresses': [
                    RECIPIENT,
                ],
            },
            Message={
                'Body': {
                    'Html': {
                        'Charset': CHARSET,
                        'Data': BODY_HTML,
                    },
                    'Text': {
                        'Charset': CHARSET,
                        'Data': BODY_TEXT,
                    },
                },
                'Subject': {
                    'Charset': CHARSET,
                    'Data': SUBJECT,
                },
            },
            Source=SENDER,
            # If you are not using a configuration set, comment or delete the
            # following line
            #ConfigurationSetName=CONFIGURATION_SET,
        )
    # Display an error if something goes wrong. 
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['ResponseMetadata']['RequestId']) 
    
if __name__ == '__main__':
    #add timer 
    while (True): 
        processQueue() 
        print("Processed, sent email") 
        time.sleep(60*60*12) #sends an email every 12 hours 
        