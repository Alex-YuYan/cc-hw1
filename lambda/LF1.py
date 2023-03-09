import json
import time
import os
import random
import boto3
from datetime import datetime

import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

''' --- Format Responses --- '''

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

def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
        }
    }
    
def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }
    
def build_validation_result(is_valid, violated_slot, message_content):
    if message_content is None:
        return {
            "isValid": is_valid,
            "violatedSlot": violated_slot,
        }

    return {
        'isValid': is_valid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }
    
def validate(location, cuisine, party, date):
    valid_loc = ["manhattan", "new york", "newyork"]
    valid_cuisine = ["japanese", "chinese", "italian", "french", "thai", "vietnamese", "american", "healthy"]
    if location is not None and location.lower() not in valid_loc:
        return build_validation_result(False, 'Location', f"Our service does not support {location} as location, please try another.")
    if cuisine is not None and cuisine.lower() not in valid_cuisine:
        return build_validation_result(False, 'Cuisine', f"Our service does not support {cuisine} as cuisine type, please try another.")
    if party is not None and int(party) < 1:
        return build_validation_result(False, 'Party', f"Our service does not support {party} as number of people, please try another.")
    if date is not None:
        input_date = datetime.strptime(date, "%Y-%m-%d").date()
        if input_date < datetime.today().date():
            return build_validation_result(False, 'Date', f"Our service does not support {date} as dining date, please try another.")
            
    return build_validation_result(True, None, None)
    
    
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
    email = intent_request['currentIntent']['slots']['Email']
    
    # validate
    source = intent_request['invocationSource']
    if source == 'DialogCodeHook':
        slots = intent_request['currentIntent']['slots']
        validation_result = validate(location, cuisine, party, date)
        
        # didn't pass validation
        if not validation_result['isValid']:
            slots[validation_result['violatedSlot']] = None
            return elicit_slot(intent_request['sessionAttributes'],
                               intent_request['currentIntent']['name'],
                               slots,
                               validation_result['violatedSlot'],
                               validation_result['message'])
        
        # passed validation
        return delegate(session_attributes, slots)
        
    
    possible_answers = ["You’re all set. Expect my suggestions shortly! Have a good day."]

    # Send the message to SQS
    message = {
        'uuid': intent_request['userId'],
        'location': location,
        'cuisine': cuisine,
        'party': party,
        'date': date,
        'time': time,
        'email': email
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