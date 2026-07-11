import requests
import json

response = requests.get('http://206.189.129.232:8000/api/stream', stream=True)
for line in response.iter_lines():
    if line:
        line = line.decode('utf-8')
        if line.startswith('data:'):
            data = json.loads(line[5:])
            print("Keys:", data.keys())
            print("research_tips len:", len(data.get('research_tips', [])))
            break
