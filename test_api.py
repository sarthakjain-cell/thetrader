import requests

try:
    url = "http://206.189.129.232:8000/api/chat"
    res = requests.post(url, json={"message": "hello"})
    print("Status:", res.status_code)
    print("Response:", res.text)
except Exception as e:
    print("Error:", e)
