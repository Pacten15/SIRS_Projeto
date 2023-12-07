import psycopg2
import json
from sshtunnel import SSHTunnelForwarder

def read_json_file(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    f.close()
    return data



tunnel =  SSHTunnelForwarder(
        ("192.168.0.100", 22),
        ssh_username="kali",
        ssh_password="",
        remote_bind_address=('192.168.0.100', 5433))

tunnel.start()

conn = psycopg2.connect(host="localhost", database="documents", user="luis", password="123", port=tunnel.local_bind_port)


cur = conn.cursor()

cur.execute("""
    CREATE TABLE IF NOT EXISTS json_documents (
        id SERIAL PRIMARY KEY,
        data JSONB UNIQUE
    )
""")

cur.execute(""" INSERT INTO json_documents (data) VALUES (%s)""", (json.dumps(read_json_file('example.json')),))

cur.execute("""SELECT * FROM json_documents;""")

rows = cur.fetchall()

print('\n')
for row in rows:
    print(row)

conn.commit()
cur.close()
conn.close()
tunnel.close()