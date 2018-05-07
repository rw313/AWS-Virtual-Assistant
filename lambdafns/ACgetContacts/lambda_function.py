import boto3
import pymysql
from datetime import datetime 
rds_host  = "contentenginedb.ctpsr3h9wg8h.us-east-1.rds.amazonaws.com"
name = "cedbroot"
password = "cedbpassword"
db_name = "contentengine"
conn = pymysql.connect(rds_host, user=name, passwd=password, db=db_name, connect_timeout=5)

def getContacts(userid):
    results = []
    cursor = conn.cursor() 
    fetchContacts = """SELECT contactID,timeCreated,name,notes,interests,closeness,eagerness,compat  from contentengine.Contacts where userID="""+userid
    #print(fetchContacts)
    cursor.execute(fetchContacts)
    rows = cursor.fetchall()
    
    for row in rows:    
        result = {"contactID": row[0], "timeCreated": datetime.strftime(row[1], "%Y-%m-%d %H:%M:%S"), "name": row[2], "notes": row[3], "interests": row[4], "closeness": row[5], "eagerness": row[6], "compat": row[7] }
        results.append(result)
    return results
    
def lambda_handler(event, context):  
    unstructured_msg = event["messages"][0]["unstructured"]
    slots = unstructured_msg["text"]
    userID = str(slots["userID"]) 
     
    unstructured_msg = dict() 
    unstructured_msg["id"] = "0"
    unstructured_msg["text"] = getContacts(userID)
    unstructured_msg["timestamp"] = "05-02-2018 11:00:00PM"
    
    response = dict()  
    msgs = []
    msgs.append({"unstructured": unstructured_msg})
    response["messages"] = msgs
    return response