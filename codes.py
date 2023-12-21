import requests
import json

r = requests.get('https://api-na.hosted.exlibrisgroup.com/almaws/v1/conf/code-tables/MandatoryBorrowingWorkflowSteps?apikey=l8xx58220ca55660427d87a3fa8de473a472&format=json')
codes = json.loads(r.text)['row']
for code in codes:
    f = open('codes.csv', 'a')
    f.write(code['code'] + ',' + code['description'] + '\n')
    f.close()

r = requests.get('https://api-na.hosted.exlibrisgroup.com/almaws/v1/conf/code-tables/OptionalBorrowingWorkflowSteps?apikey=l8xx58220ca55660427d87a3fa8de473a472&format=json')
codes = json.loads(r.text)['row']
for code in codes:
    f = open('codes.csv', 'a')
    f.write(code['code'] + ',' + code['description'] + '\n')
    f.close()
