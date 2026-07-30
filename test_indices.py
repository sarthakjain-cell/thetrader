import requests

try:
    res = requests.get("http://206.189.129.232:8000/api/indices", timeout=5)
    print("STATUS:", res.status_code)
    print("BODY:", res.text)
except Exception as e:
    print("ERROR:", e)
