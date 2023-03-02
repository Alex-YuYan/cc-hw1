import json
import time
import os
import random
import boto3
import requests

import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }

    return response
    
    
""" --- Intent Handlers ---"""
def greet(intent_request):
    """
    Simply greets the user and ask for further input
    """
    session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
    possible_answers = ['Hello! How can I help you?', 'Hi there, how can I help?', "Welcome. How may I assist you today?",\
                        "Good day! How can I help you with your request?", "Hello there! How may I be of service to you?",\
                        "Welcome! Is there anything I can do to help?"]
    return close(
        session_attributes,
        'Fulfilled',
        {
            'contentType': 'PlainText',
            'content': random.choice(possible_answers)
        }
    )
    
def thankyou(intent_request):
    """
    Simply replies after the user says thank you
    """
    session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
    possible_answers = ["You're welcome!", "My pleasure!", "No problem at all!", "Happy to help!", "Anytime!"]
    return close(
        session_attributes,
        'Fulfilled',
        {
            'contentType': 'PlainText',
            'content': random.choice(possible_answers)
        }
    )

def dining(intent_request):
    """
    Sends a restaurant suggestion to SQS based on the date, time, party number, cuisine type and location provided by the user
    """
    session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
    location = intent_request['currentIntent']['slots']['Location']
    cuisine = intent_request['currentIntent']['slots']['Cuisine']
    party = intent_request['currentIntent']['slots']['Party']
    date = intent_request['currentIntent']['slots']['Date']
    time = intent_request['currentIntent']['slots']['Time']
    phone = intent_request['currentIntent']['slots']['PhoneNum']
    possible_answers = ["I have sent your request to our restaurant suggestion system. You will receive a text message shortly with your restaurant suggestion.",\
                        "Your request has been sent to our restaurant suggestion system. You will receive a text message shortly with your restaurant suggestion.",\
                        "Please wait while I send your request to our restaurant suggestion system. You will receive a text message shortly with your restaurant suggestion."]

    # Send the message to SQS
    message = {
        'location': location,
        'cuisine': cuisine,
        'party': party,
        'date': date,
        'time': time,
        'phone': phone
    }
    sqs_client = boto3.client('sqs')

    try: 
        response = sqs_client.send_message(
            QueueUrl = 'https://sqs.us-east-1.amazonaws.com/502395508438/Q1',
            MessageBody = json.dumps(message)
        )
        logger.info(response)
    except Exception as e:
        logger.error(e)
        possible_answers = ["Sorry, Unable to send your request to our restaurant suggestion system right now. Please try again later."]

    return close(
        session_attributes,
        'Fulfilled',
        {
            'contentType': 'PlainText',
            'content': random.choice(possible_answers)
        }
    )

    
    
""" --- Dispatch Intents --- """

def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    logger.debug('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))
    intent_name = intent_request['currentIntent']['name']

    # Dispatch to your bot's intent handlers
    if intent_name == 'GreetingIntent':
        return greet(intent_request)
    elif intent_name == 'ThankYouIntent':
        return thankyou(intent_request)
    elif intent_name == 'DiningSuggestionsIntent':
        return dining(intent_request)

    raise Exception('Intent with name ' + intent_name + ' not supported')


""" -- Entry Point --- """
def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    # By default, treat the user request as coming from the America/New_York time zone.
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    logger.debug(event)
    logger.debug('event.bot.name={}'.format(event['bot']['name']))

    return dispatch(event)
    
    
