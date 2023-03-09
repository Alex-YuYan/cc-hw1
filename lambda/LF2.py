import json
import boto3
import random
import datetime
import logging
import urllib3

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def lambda_handler(event, context):
    
    queue = boto3.client('sqs')

    # Poll from queue
    try:
        messages = queue.receive_message(
            QueueUrl='https://sqs.us-east-1.amazonaws.com/502395508438/Q1',
            MessageAttributeNames=['All'],
            MaxNumberOfMessages=1,
            WaitTimeSeconds=2
        )
        message = messages["Messages"][0]
        receipt_handle = message["ReceiptHandle"]
        logger.info(f"Received message: {message}")
        message_body = json.loads(message["Body"])
    except Exception as e:
        logger.error("Couldn't receive messages from queue")
        return "Couldn't receive messages from queue"
    else:
        handle_rec_request(message_body)

    # Delete the message from the queue if no exception was raised previously
    try:
        queue.delete_message(
        QueueUrl='https://sqs.us-east-1.amazonaws.com/502395508438/Q1', ReceiptHandle=receipt_handle)
    except Exception as e:
        logger.error("Couldn't delete message from queue")
        return "Couldn't delete message from queue"
        
    return "Message successfully sent to target email and deleted from queue"


def handle_rec_request(data):
    location = data['location']
    cuisine = data['cuisine'].lower()
    party = data['party']
    date = data['date']
    time = data['time']
    email = data['email']
    uuid = data['uuid']

    rec_ids = get_rec_for_cuisine(cuisine)
    restaurants = dynamo_fetch(cuisine, rec_ids)
    formatted = format_rec_string(restaurants, cuisine, party, date, time)
    write_uuid_to_db(uuid, formatted)
    
    ses_send(formatted, email)


def write_uuid_to_db(uuid, rec_string):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('past_recs')
    try:
        response = table.put_item(
            Item={
                'id': uuid,
                'rec_string': rec_string
            }
        )
    except Exception as e:
        logger.error(e)
        logger.info("Unable to fetch old rec from DynamoDB")

def ses_send(msg, email):
    client = boto3.client('ses')
    logger.debug(email)
    logger.debug(msg)

    try:
        # Provide the contents of the email.
        response = client.send_email(
            Destination={
                'ToAddresses': [
                    email,
                ],
            },
            Message={
                'Body': {
                    'Text': {
                        'Data': msg,
                    },
                },
                'Subject': {
                    'Data': "Your Dining Suggest",
                },
            },
            Source="yanalex@foxmail.com",
        )
    # Display an error if something goes wrong.
    except Exception as e:
        logger.error(e)
    else:
        logger.info(f"Email sent! Message ID: {response['MessageId']}")


def format_rec_string(restaurants, cuisine, party, date, time):
    cuisine = cuisine.capitalize()
    party_string = str(party) + " " + ("person" if party == 1 else "people")
    date_string = str(date)
    time_string = str(time)
    if time_string == "MO":
        time_string = "morning"
    elif time_string == "AF":
        time_string = "afternoon"
    elif time_string == "EV":
        time_string = "evening"
    if date == datetime.date.today():
        date_string = "today"
    rest1_string = format_restaurant_string(restaurants[0])
    rest2_string = format_restaurant_string(restaurants[1])
    rest3_string = format_restaurant_string(restaurants[2])

    msg = f"Hello! Here are my {cuisine} restaurant suggestions for {party_string}, " +\
        f"for {date_string} " +\
        f"at {time_string}: " +\
        f"1. {rest1_string}, " +\
        f"2. {rest2_string}, "\
        f"3. {rest3_string}. Enjoy your meal!"
    return msg


def format_restaurant_string(restaurant):
    name = restaurant[0]
    addr = restaurant[1]

    return f"{name}, located at {addr}"


def get_rec_for_cuisine(cuisine):
    http = urllib3.PoolManager()
    headers = urllib3.make_headers(basic_auth='master2:Search!@#123')
    r = http.request('GET', f'https://search-cc-hw1-search-mge6fhse3jskjt4n3uwuvqwlmy.us-east-1.es.amazonaws.com/restaurants/_search?q={cuisine}&pretty=true', headers=headers)
    data = json.loads(r.data)
    
    return [d['_source']["id"] for d in data['hits']['hits'][:3]]

def dynamo_fetch(cuisine, ids):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('yelp-restaurants')
    results = []

    for id in ids:
        try:
            response = table.get_item(
                Key={
                    'cuisine_category': cuisine,
                    'id': id
                }
            )
        except Exception as e:
            logger.error(e)
        else:
            if 'Item' in response:
                logger.info(f"Got item: {response['Item']}")
                item = response['Item']
                name = item.get('name')
                location = item.get('location').get('display_address')[0]
                results.append((name, location))
            else:
                logger.info("However, queried item not found")

    return results