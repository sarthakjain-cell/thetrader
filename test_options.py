import requests

url = "http://206.189.129.232:8000/api/chat"
headers = {
    "Origin": "http://localhost",
    "Access-Control-Request-Method": "POST",
    "Access-Control-Request-Headers": "content-type"
}
res = requests.options(url, headers=headers)
print("STATUS:", res.status_code)
print("HEADERS:", res.headers)
print("BODY:", res.text)
