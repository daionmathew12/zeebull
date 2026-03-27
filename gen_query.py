import base64
query = "SELECT table_name, column_name FROM information_schema.columns WHERE table_schema = 'public' AND (column_name LIKE '%image%' OR column_name LIKE '%photo%')"
print(base64.b64encode(query.encode()).decode())
