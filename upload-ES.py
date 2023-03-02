import os

os.environ['AWS_ACCESS_KEY_ID'] = 'key'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'key'

import boto3

credentials = boto3.Session().get_credentials()
region='us-east-1' # for example

# Now set up the AWS 'Signer'
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth
auth = AWSV4SignerAuth(credentials, region)

# And finally the OpenSearch client
host=f"search-cc-hw1-search-mge6fhse3jskjt4n3uwuvqwlmy.us-east-1.es.amazonaws.com" # fill in your hostname (minus the https://) here
client = OpenSearch(
    hosts = [{'host': host, 'port': 443}],
    http_auth = auth,
    use_ssl = True,
    verify_certs = True,
    connection_class = RequestsHttpConnection
)

import json
data = json.loads(open('yelp_results_t_5380_ES.json', 'r').read())

def payload_constructor(data,action):
    # "All my own work"

    action_string = json.dumps(action) + "\n"

    payload_string=""

    for datum in data:
        payload_string += action_string
        this_line = json.dumps(datum) + "\n"
        payload_string += this_line
    return payload_string

action={
    "index": {
        "_index": "restaurants"
    }
}

print(len(data))

# response=client.bulk(body=payload_constructor(data, action),index="restaurants")