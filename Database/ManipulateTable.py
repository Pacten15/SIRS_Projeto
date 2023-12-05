import psycopg2

conn = psycopg2.connect(host="localhost", database="documents", user="luis", password="123", port=5432)

cur = conn.cursor()

cur.execute("""SELECT * FROM json_documents;""")

rows = cur.fetchall()

print('\n')
for row in rows:
    print(row)

cur.execute("""DELETE FROM json_documents;""")

conn.commit()

cur.close()
conn.close()