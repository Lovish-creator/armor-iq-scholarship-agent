import json, urllib.request

payload = {'simulate_out_of_scope_violation': True}
data = json.dumps(payload).encode('utf-8')
req = urllib.request.Request('http://127.0.0.1:8000/api/agent/run', data=data, headers={'Content-Type':'application/json'})
try:
    with urllib.request.urlopen(req, timeout=60) as resp:
        print(resp.status)
        print(resp.read().decode('utf-8'))
except Exception as e:
    print('ERROR', e)
