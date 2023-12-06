import psycopg2
import json

def read_json_file(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    f.close()
    return data

conn = psycopg2.connect(host="192.168.0.100", database="documents", user="luis", password="123", port=5433)

cur = conn.cursor()



cur.execute(""" INSERT INTO json_documents (data) VALUES (%s)""", (json.dumps(read_json_file('example.json')),))
conn.commit()

cur.close()
conn.close()