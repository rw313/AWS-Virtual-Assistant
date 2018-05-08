import boto3 
from botocore.vendored import requests
import json
import time
import datetime 

def getEvents(): 
    cities =[("Bridgeport","CT")]
    api_key= "4b2b7c173622721682d505b38682421" 
    result = "Here are 3 upcoming events based on your preferred location "
    for (city, state) in cities:
        per_page = 3
        results_we_got = per_page
        offset = 0
        if (results_we_got > 0):
            # Meetup.com documentation here: http://www.meetup.com/meetup_api/docs/2/groups/
            response=get_results({"sign":"true","country":"US", "city":city, "state":state, "radius": 10, "key":api_key, "page":per_page, "offset":offset })
            time.sleep(1)
            offset += 1 
            result +=  response['city']['city']+", "+response['city']['zip']+": " 
            for event in response['events'][0:per_page]:
                link = event['link']
                eventname = event['name']
                eventgroup = event['group']['name'] 
                rsvps = event['yes_rsvp_count']
                
                s = event['time'] + event['utc_offset']
                when = time.strftime('%a %b %d, %I:%M%p', time.gmtime(s/1000.0))
                
                result += "<a href='"+link+"'>"
                result += eventname + " (Hosted by "+eventgroup+", Current RSVPs:"+str(rsvps)+") is happening on " + when
                result += "</a>..... "
                #print([link, eventname, eventgroup, str(rsvps), when]) 
    return result 
        
def get_results(params):
    request = requests.get("http://api.meetup.com/find/upcoming_events",params=params)
    data = request.json()
    return data

def lambda_handler(event, context):
    msg = ""
    try:
        msg = getEvents()
    except:
        msg = "Oops! Couldn't get anything right now. Try again later?"
        
    return { 
              "dialogAction": {
                    "type": "Close",
                    "fulfillmentState": "Fulfilled",
                    "message": {
                      "contentType": "PlainText",
                      "content": msg
                    }
                  }
            }
