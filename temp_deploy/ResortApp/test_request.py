import requests
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhQGguY29tIiwiZXhwIjoxNzgwNTk4OTMxfQ.nvv2iJAkc5ZcwCOBxztJGEp9P-s32DUtaHR9H_yzcUFc"
headers = {"Authorization": f"Bearer {token}", "accept": "application/json"}
res = requests.get("https://teqmates.com/orchidapi/api/service-requests?limit=1000", headers=headers, verify=False)
data = res.json()
print(f"Total entries: {len(data)}")
for r in data:
    print(f" - {r.get('id')} / {r.get('type')} / {r.get('status')} / {r.get('employee_name')}")
