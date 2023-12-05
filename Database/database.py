import psycopg2

conn = psycopg2.connect(host="localhost", database="documents", user="luis", password="123", port=5432)


cur = conn.cursor()

cur.execute("""
    CREATE TABLE json_documents (
        id SERIAL PRIMARY KEY,
        data JSONB UNIQUE
    )
""")

conn.commit()
cur.close()
conn.close()
