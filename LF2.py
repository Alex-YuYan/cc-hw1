import json
import boto3
import random
import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def lambda_handler(event, context):
    queue = boto3.client('sqs')

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
        logger.error("Couldn't receive messages from queue: %s", queue)
    else:
        handle_rec_request(message_body)

    # Delete the message from the queue if no exception was raised previously
    try:
        queue.delete_message(
        QueueUrl='https://sqs.us-east-1.amazonaws.com/502395508438/Q1', ReceiptHandle=receipt_handle)
    except Exception as e:
        logger.error("Couldn't delete message from queue: %s", queue)
        
    return "Message successfully sent to target email and deleted from queue"


def handle_rec_request(data):
    location = data['location']
    cuisine = data['cuisine']
    party = data['party']
    date = data['date']
    time = data['time']
    email = data['email']

    # restaurants = get_rec_for_cuisine(cuisine) # should be exactly 3 in a list
    # format restaurant data into a string
    # rec_ses = format_rec_string(restaurants, cuisine)

    ses_send(str(data), email)


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
                    'Data': "Test AWS SES",
                },
            },
            Source="yanalex@foxmail.com",
        )
    # Display an error if something goes wrong.
    except Exception as e:
        logger.error(e)
    else:
        logger.info(f"Email sent! Message ID: {response['MessageId']}")


def format_rec_string(restaurants, cuisine, party, date):
    cuisine = cuisine.capitalize()
    party_string = str(party) + " " + ("person" if party == 1 else "people")
    date_string = str(date)  # TODO: might need formatting
    rest1_string = format_restaurant_string(restaurants[0])
    rest2_string = format_restaurant_string(restaurants[1])
    rest3_string = format_restaurant_string(restaurants[2])

    msg = f"Hello! Here are my {cuisine} restaurant suggestions for {party_string}, " +\
        f"for {date_string}: " +\
        f"1. {rest1_string}, " +\
        f"2. {rest2_string}, "\
        f"3. {rest3_string}. Enjoy yourmeal!"
    return msg


def format_restaurant_string(restaurant):
    name = restaurant['name']
    addr = restaurant['location']['address1']
    if restaurant['location']['address2']:
        addr += " " + restaurant['location']['address2']
    if restaurant['location']['address3']:
        addr += " " + restaurant['location']['address3']

    return f"{name}, located at {addr}"


def get_rec_for_cuisine(cuisine):
    # pull from dynamoDB using elasticsearch
    pass
