import urllib
from bs4 import BeautifulSoup
from botocore.vendored import requests

def lambda_handler(event, context):
    #key is searchname 
    unstructured_msg = event["messages"][0]["unstructured"]
    slots = unstructured_msg["text"]
    name = slots["searchname"] 
    
    text = name +" recent news" 
    text = urllib.parse.quote_plus(text)
    
    url = 'https://google.com/search?q=' + text 
    response = requests.get(url, headers={ 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36' })
    
    soup = BeautifulSoup(response.text, "html.parser")
    html = "<ul>"
    for div in soup.find_all(class_='g')[2:]: 
        html += "<li>"
        try:
            html += "<a href='"+div.find('a')['href']+"'>" 
            html += div.find('a').contents[0]  
            html += "</a>"
        except:
            print("Error ")
        html += "</li>"
    html += "</ul>"
    
    
    unstructured_msg = dict() 
    unstructured_msg["id"] = "0"
    unstructured_msg["text"] = html
    unstructured_msg["timestamp"] = "05-02-2018 11:00:00PM"
    
    response = dict()  
    msgs = []
    msgs.append({"unstructured": unstructured_msg})
    response["messages"] = msgs
    return response 
