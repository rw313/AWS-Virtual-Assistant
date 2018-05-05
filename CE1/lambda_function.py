import sys
import logging
import rds_config
import pymysql
import boto3  
import imp, sys, os, re, time
from botocore.vendored import requests
from datetime import datetime as dt  
import json 

from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.metrics.pairwise import linear_kernel
#rds settings
rds_host  = "contentenginedb.ctpsr3h9wg8h.us-east-1.rds.amazonaws.com"
name = rds_config.db_username
password = rds_config.db_password
db_name = rds_config.db_name


logger = logging.getLogger()
logger.setLevel(logging.INFO)

try:
    conn = pymysql.connect(rds_host, user=name, passwd=password, db=db_name, connect_timeout=5)
except:
    logger.error("ERROR: Unexpected error: Could not connect to MySql instance.")
    sys.exit()

logger.info("SUCCESS: Connection to RDS mysql instance succeeded")

def lambda_handler(event, context): 
    with conn.cursor() as cur:
        cur.execute("select * from Articles limit 3")
        for row in cur: 
            logger.info(row)
            print(row)
    
    return "Finished"


def rank():
    if request.method == "GET": 
        query = request.args.getlist('query')
        userid = request.args.get('userid')
        friendid = request.args.get('friendid')
        if not (query and userid and friendid):
            return "Please make sure query, userid, and friendid parameters are filled in"
        return rankArticles(query, userid, friendid) #request.args.getlist(<paramname>)
    else:
        return "deprecated"
        #return rankArticles(request.form["query"]) 

def rankArticles(query, userid, friendid):
    cursor = mysql.connection.cursor()
    unseenArticlesSql = """ SELECT Articles.articleId, keywords, summary, title, link 
    from Articles left join ArticleShares on Articles.articleId = ArticleShares.articleId 
    where !(ArticleShares.userSeenDate IS NOT NULL and ArticleShares.userId='{}' and ArticleShares.friendId='{}') 
    """.format(userid, friendid)
    
    print(unseenArticlesSql)
    
    cursor.execute(unseenArticlesSql)
    rows = cursor.fetchall()
    articles = [] 
    for row in rows:
        article = dict() 
        article["articleId"] = row[0]
        article["keywords"] = row[1] 
        article["summary"] = row[2] 
        article["title"] = row[3]
        article["link"] = row[4] 

        articles.append(article)  
    return jsonify(results = getMatches(query, articles))

def getMatches(queries, articles): 
    results = [] 
    if not queries or len(queries) < 1:
        return "couldn't parse query parameter"
    for query in queries:
        data_samples = [query] 
        for i in range(0, len(articles)):
            data_samples.append(articles[i]["title"]) # + articles[i]["keywords"]+articles[i]["summary"])

        tfidf_vectorizer = TfidfVectorizer(stop_words='english')
        tfidf = tfidf_vectorizer.fit_transform(data_samples) 
        cosine_similarities = linear_kernel(tfidf[0:1], tfidf).flatten() #replace first param with query 
        related_docs_indices = cosine_similarities.argsort()[:-7:-1]
        
        for j in range(1, len(related_docs_indices)):
            results.append(str(articles[related_docs_indices[j]-1]["articleId"]))
    print(results)
    return fetchRelevantRows(results)

def fetchRelevantRows(results):
    cursor = mysql.connection.cursor() 
    
    if not results or len(results) < 1:
        return [] 
    
    fetchRelevantRows = """SELECT articleId, keywords, summary, title, link, 
    img, author, datePublished, contentengine.Articles.sourceId as sId, sourceName, description 
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
        article["keywords"] = row[1] 
        article["summary"] = row[2] 
        article["title"] = row[3]
        article["link"] = row[4] 
        article["img"] = row[5]
        article["author"] = row[6] 
        article["datePublished"] = row[7]
        article["sId"] = row[8]
        article["sourceName"] = row[9]
        article["description"] = row[10]
        
        
        articles.append(article) 
    return articles


    
def sendEmail(email, resultstr):
        
    from botocore.exceptions import ClientError
    
    # Replace sender@example.com with your "From" address.
    # This address must be verified with Amazon SES.
    SENDER = "Assistant Cat <rachelwu343@gmail.com>"
    
    RECIPIENT = email
    
    # Specify a configuration set. If you do not want to use a configuration
    # set, comment the following variable, and the 
    # ConfigurationSetName=CONFIGURATION_SET argument below.
    #CONFIGURATION_SET = "ConfigSet"
    
    # If necessary, replace us-west-2 with the AWS Region you're using for Amazon SES.
    AWS_REGION = "us-east-1"
    
    # The subject line for the email.
    SUBJECT = "Your restaurant recommendations"
    
    # The email body for recipients with non-HTML email clients.
    BODY_TEXT = (resultstr + "\r\n"
                 "This email was sent with Amazon SES using the "
                 "AWS SDK for Python (Boto)."
                )
                
    # The HTML body of the email.
    BODY_HTML = """<html>
    <head></head>
    <body>
      <p><b>"""+resultstr+"""</b></p>
      <p>This email was sent with
        <a href='https://aws.amazon.com/ses/'>Amazon SES</a> using the
        <a href='https://aws.amazon.com/sdk-for-python/'>
          AWS SDK for Python (Boto)</a>.</p>
    </body>
    </html>
                """            
    
    # The character encoding for the email.
    CHARSET = "UTF-8"
    
    # Create a new SES resource and specify a region.
    client = boto3.client('ses')
    
    # Try to send the email.
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
    
    print("Sent an email")
    
