import json
import boto3
import logging
import uuid
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def lambda_handler(event, context):
    logger.info("Event is: " + str(event))
    
    the_uuid = event["messages"][0]["unstructured"].get("uuid")
    old_response = ''
    if not the_uuid:
        logger.info("Did not find uuid")
        the_uuid = uuid.uuid4().hex
    else:
        logger.info("Searching for old response for "+ the_uuid)
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('past_recs')
        try:
            response = table.get_item(
                Key={
                    'id': the_uuid
                }
            )
        except Exception as e:
            logger.error(e)
            logger.info("Unable to fetch old rec from DynamoDB")
        else:
            if 'Item' in response:
                logger.info(f"Got item: {response['Item']}")
                item = response['Item']
                response = {
                    "messages": [
                        {
                          "type": "unstructured",
                          "unstructured": {
                            "text": item['rec_string'],
                            "uuid": the_uuid
                          }
                        }
                      ]
                    }
                return response
            else:
                logger.info("Old response not found for uuid " + the_uuid)
    
    # instantiate boto3 client
    client = boto3.client('lex-runtime')
    user_prompt = ""
    
    try:
        user_prompt = event["messages"][0]["unstructured"]["text"]
    except:
        print("unable to parse request payload")
    
    # Get reply from lex bot
    lex_reply = client.post_text(
        botName = 'DiningSuggest',
        botAlias = 'dining',
        userId = str(the_uuid),
        inputText = user_prompt,
    )
    reply_message = lex_reply.get("message")
    
    response = {
        "messages": [
        {
          "type": "unstructured",
          "unstructured": {
            "text": reply_message,
            "uuid": the_uuid
          }
        }
      ]
    }
    return response