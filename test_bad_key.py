import requests

url = "http://206.189.129.232:8000/api/keys"
requests.post(url, json={"gemini_key": "invalid_key_123"})

url = "http://206.189.129.232:8000/api/chat"
res = requests.post(url, json={"message": "hello"})
print("STATUS:", res.status_code)
print("HEADERS:", res.headers)
try:
    print("JSON:", res.json())
except Exception as e:
    print("NOT JSON:", res.text)
