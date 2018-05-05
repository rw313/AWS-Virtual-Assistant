import boto3 
import pymysql
rds_host  = "contentenginedb.ctpsr3h9wg8h.us-east-1.rds.amazonaws.com"
name = "cedbroot"
password = "cedbpassword"
db_name = "contentengine"

conn = pymysql.connect(rds_host, user=name, passwd=password, db=db_name, connect_timeout=5)

def lambda_handler(event, context):
    #send person into to DynamoDB
    slots = event['currentIntent']['slots']
    
    #userid = slots["userid"]
    name = slots['name']
    notes = slots['notes']
    closeness = slots['closeness'] 
    compat = slots['compat'] 
    eagerness = slots['eagerness'] 
    interests = slots['interests'] 
    
    userID = event['userID'] if "userID" in event else '1'
    
    values = ", ".join(['"'+s+'"' for s in [name, notes, closeness, compat, eagerness, interests, userID] ])
    
    with conn.cursor() as cur:
        cur.execute('Insert into Contacts (name, notes, closeness, compat, eagerness, interests, userID) values ('+values+')')
        conn.commit()  
    
    return { 
              "dialogAction": {
                    "type": "Close",
                    "fulfillmentState": "Fulfilled",
                    "message": {
                      "contentType": "PlainText",
                      "content": "Great! I've added this person to your contacts."
                    }
                  }
            }
