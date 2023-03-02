import json
import boto3

def lambda_handler(event, context):
    # instantiate boto3 client
    client = boto3.client('lex-runtime')
    
    user_prompt = ""
    
    try:
        user_prompt = event["messages"][0]["unstructured"]["text"]
    except:
        print("unable to parse request payload")
    
    # TODO: unique userID needed
    # Get reply from lex bot
    lex_reply = client.post_text(
        botName = 'DiningSuggest',
        botAlias = 'dining',
        userId = 'testID',
        inputText = user_prompt,
    )
    reply_message = lex_reply.get("message")
    
    response = {
        "statuscode": 200,
        "messages": [
        {
          "type": "unstructured",
          "unstructured": {
            "text": reply_message,
          }
        }
      ]
    }
    
    return response
