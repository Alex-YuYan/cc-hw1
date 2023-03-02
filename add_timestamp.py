import json
import time

f = open('yelp_results.json', 'r')
txt = f.read()

all_jsons = json.loads(txt)
for one in all_jsons:
    one['insertedAtTimestamp'] = int(time.time())
    
f = open('yelp_results_t.json', 'w')
f.write(json.dumps(all_jsons))