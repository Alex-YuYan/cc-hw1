import json
import boto3
import os
import time

os.environ['AWS_ACCESS_KEY_ID'] = 'key'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'key'

txt = open('yelp_results_t.json', 'r').read()
all_jsons = json.loads(txt)
# Create a DynamoDB client
dynamodb = boto3.client('dynamodb', region_name='us-east-1')
# Set the name of your DynamoDB table
table_name = 'yelp-restaurants'

def insert_batch(batch_data):
    request_items = []
    for restaurant in batch_data:
        # Define the partition key for your DynamoDB table
        partition_key = {'S': restaurant['cuisine_category']}

        # Define the item to be uploaded, including any additional attributes
        item = {
            'id': {'S': restaurant['id']},
            'cuisine_category': partition_key,
            'alias': {'S': restaurant['alias']},
            'name': {'S': restaurant['name']},
            'insertedAtTimestamp': {'N': str(restaurant['insertedAtTimestamp'])},
            'review_count': {'N': str(restaurant['review_count'])},
            'rating': {'N': str(restaurant['rating'])},
            'coordinates': {'M': {'latitude': {'N': str(restaurant['coordinates']['latitude'])},
                                'longitude': {'N': str(restaurant['coordinates']['longitude'])}}},
            'location': {'M': {'city': {'S': restaurant['location']['city']},
                            'zip_code': {'S': restaurant['location']['zip_code']},
                            'country': {'S': restaurant['location']['country']},
                            'state': {'S': restaurant['location']['state']},
                            'display_address': {'L': [{'S': address} for address in restaurant['location']['display_address']]}}}
            }
        
        # Add the item to the request list
        request_items.append({'PutRequest': {'Item': item}})

    # Upload the batch of items to DynamoDB
    print(request_items)
    response = dynamodb.batch_write_item(RequestItems={table_name: request_items})
    if 'UnprocessedItems' in response:
        print('Error uploading batch to DynamoDB')
        print(response['UnprocessedItems'])
        return False

for i in range(0, len(all_jsons), 25):
    batch_data = all_jsons[i:i+25]
    print('Uploading batch {} to DynamoDB\n\n'.format(i))
    insert_batch(batch_data)
    