import boto3 
import pymysql
rds_host  = "contentenginedb.ctpsr3h9wg8h.us-east-1.rds.amazonaws.com"
name = "cedbroot"
password = "cedbpassword"
db_name = "contentengine"

conn = pymysql.connect(rds_host, user=name, passwd=password, db=db_name, connect_timeout=5)

def lambda_handler(event, context):
    #add user info like email, firstname, lastname 
    unstructured_msg = event["messages"][0]["unstructured"]
    slots = unstructured_msg["text"]
    firstname = slots['firstname']
    lastname = slots['lastname']
    email = slots['email']  
    username = slots['username']
    
    values = ", ".join(['"'+s+'"' for s in [firstname, lastname, email, username] ])
    
    with conn.cursor() as cur:
        cur.execute('Insert into Users (firstname, lastname, email, username) values ('+values+')')
        conn.commit()  
        print("USER ID IN RDS: " + str(cur.lastrowid))
    
    unstructured_msg = dict() 
    unstructured_msg["id"] = "0"
    unstructured_msg["text"] = "USER ID IN RDS: " + str(cur.lastrowid)
    unstructured_msg["timestamp"] = "05-02-2018 11:00:00PM"
    
    response = dict()  
    msgs = []
    msgs.append({"unstructured": unstructured_msg})
    response["messages"] = msgs
    return response