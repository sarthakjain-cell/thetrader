import sys
try:
    from dhanhq import dhanhq
    from dhanhq import DhanContext
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "dhanhq"])
    from dhanhq import dhanhq
    from dhanhq import DhanContext

client_id = "1112946078"
access_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzg2Mjk2NjQ2LCJpYXQiOjE3ODYyMTAyNDYsInRva2VuQ29uc3VtZXJUeXBlIjoiU0VMRiIsIndlYmhvb2tVcmwiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMTEyOTQ2MDc4In0.bavCoVwcQc6vpySLAFT7ReNhuWV5_pibhAw4L_n3N3GjwJfGYQCj6EA8Z--AutyDk5mm1CDAaFJX8kHfGU9pNA"

print("Initializing DhanHQ...")
try:
    dhan = dhanhq(client_id, access_token)
    
    # Try fetching fund limit to verify auth
    funds = dhan.get_fund_limits()
    print("Auth Success! Funds Data:", funds)
except Exception as e:
    print(f"Auth Failed: {e}")
