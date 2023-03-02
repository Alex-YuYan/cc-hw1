import requests

headers = {
    'Authorization': 'Bearer yelp key',
    'accept': 'application/json',
}

all_cats = ['japanese', 'chinese', 'italian', 'french', 'thai', 'vietnamese', 'american', 'healthy']
results = []

for cat in all_cats:
    print('Processing category: {}'.format(cat))
    offset = 0
    while offset < 1000:
        if offset % 100 == 0:
            print('Processing offset: {}'.format(offset))
        params = {
            'location': 'Manhattan',
            'categories': cat,
            'offset': offset,
            'sort_by': 'best_match',
        }
        ranout = False
        while True:
            try:
                response = requests.get('https://api.yelp.com/v3/businesses/search', params=params, headers=headers)
                # check if the response is valid
                if response.status_code == 200:
                    # parse json
                    data = response.json()
                    bizs = data['businesses']
                    for b in bizs:
                        b['cuisine_category'] = cat
                    results += bizs
                    offset += len(bizs)
                    if len(bizs) == 0:
                        ranout = True
                        print("ranout")
                    break
                else:
                    print('Error: {}'.format(response.status_code))
            except Exception as e:
                print(e)
                continue
        if ranout:
            break
            
# save results
import json
print("total results: {}".format(len(results)))
with open('yelp_results.json', 'w') as f:
    json.dump(results, f)
    
