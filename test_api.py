import urllib.request, json, urllib.error
req = urllib.request.Request('http://206.189.129.232:8000/api/chat', data=json.dumps({'message':'hello'}).encode('utf-8'), headers={'Content-Type':'application/json'})
try:
    print(urllib.request.urlopen(req).read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print(e.read().decode('utf-8'))
