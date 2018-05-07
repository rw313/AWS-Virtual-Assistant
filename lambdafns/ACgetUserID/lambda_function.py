import boto3
import pymysql
rds_host  = "contentenginedb.ctpsr3h9wg8h.us-east-1.rds.amazonaws.com"
name = "cedbroot"
password = "cedbpassword"
db_name = "contentengine"
conn = pymysql.connect(rds_host, user=name, passwd=password, db=db_name, connect_timeout=5)

def getUser(username):
    result = {}
    cursor = conn.cursor() 
    fetchUsers = """SELECT userID, email, firstname, lastname, username from contentengine.Users where username='{}' LIMIT 1""".format(username)
    
    cursor.execute(fetchUsers)
    rows = cursor.fetchall()
    
    for row in rows: #only 1 row  
        user = dict()
        user["userID"] = str(row[0]) 
        user["email"] = row[1]
        user["firstname"] = row[2]
        user["lastname"] = row[3] 
        user["username"] = row[4]
        print(user)
        return user  
    
def lambda_handler(event, context):   
    unstructured_msg = event["messages"][0]["unstructured"]
    slots = unstructured_msg["text"]
    username = slots["username"] 
     
    unstructured_msg = dict() 
    unstructured_msg["id"] = "0"
    unstructured_msg["text"] = getUser(username)
    unstructured_msg["timestamp"] = "05-02-2018 11:00:00PM"
    
    response = dict()  
    msgs = []
    msgs.append({"unstructured": unstructured_msg})
    response["messages"] = msgs
    return response