import boto3
import pymysql
rds_host  = "contentenginedb.ctpsr3h9wg8h.us-east-1.rds.amazonaws.com"
name = "cedbroot"
password = "cedbpassword"
db_name = "contentengine"
conn = pymysql.connect(rds_host, user=name, passwd=password, db=db_name, connect_timeout=5)

def getUsers():
    result = {}
    cursor = conn.cursor() 
    fetchUsers = """SELECT userID, email, firstname, lastname from contentengine.Users """
    print(fetchUsers)
    cursor.execute(fetchUsers)
    rows = cursor.fetchall()
    
    for row in rows:  
        user = dict()
        user["useriD"] = str(row[0]) 
        user["email"] = row[1]
        user["firstname"] = row[2]
        user["lastname"] = row[3] 
        result[str(row[0])] = user 
    
    return result
    
    
def getInterestsOfAllContacts(userid):
    result = []
    cursor = conn.cursor() 
    fetchContactInterests = """SELECT interests from contentengine.Contacts where userID="""+userid
    print(fetchContactInterests)
    cursor.execute(fetchContactInterests)
    rows = cursor.fetchall()
    
    for row in rows:  
        result.append(row[0])
    print(result)
    return ', '.join(result)
    
def lambda_handler(event, context): 
    sqs = boto3.client('sqs')
    queue_url = 'https://sqs.us-east-1.amazonaws.com/073632995568/assistantcat'
    
    users = getUsers()
    #users = {'1': {"email": "rachelwu313@gmail.com", "firstname": "Rachel", "lastname": "Wu"}} #userid
    for key in users.keys():
        user = users[key]
        keywords = getInterestsOfAllContacts(key)  #rds sql, a comma separated string of keywords/phrases 
        email = user["email"]
        firstname = user["firstname"]
        lastname = user["lastname"] 
        msgAttr = { 'email': {
                                'DataType': 'String',
                                'StringValue': email
                            },
                    'firstname': {
                                'DataType': 'String',
                                'StringValue': email
                            },
                    'lastname': {
                        'DataType': 'String',
                        'StringValue': email
                    },
                    'userID': {
                        'DataType': 'String',
                        'StringValue': key
                    },
                    'interests': {
                                'DataType': 'String',
                                'StringValue': keywords 
                            }
        }
        response = sqs.send_message(
            QueueUrl=queue_url,
            DelaySeconds=10,
            MessageAttributes=msgAttr,
            MessageBody=(
                'This is a message'
            )
        )
        
        print(response['MessageId'])
    
        
    return '' 