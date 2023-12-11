
from flask import Flask
from flask import request
from flask import url_for
from flask import render_template
from sshtunnel import SSHTunnelForwarder

from Crypto.PublicKey import RSA

import json
import psycopg2

app = Flask(__name__)

tunnel =  SSHTunnelForwarder(
        ("192.168.0.100", 22),
        ssh_username="kali",
        ssh_password="kali",
        remote_bind_address=('192.168.0.100', 5432))

tunnel.start()

database = psycopg2.connect(host="192.168.0.100", database="sirs_bombappetit", user="sirs_dbadmin", password="sirs_dbpassword")

private_rsa = RSA.generate(2048)
CREATE_TABLES = ("CREATE TABLE IF NOT EXISTS ba_restaurants ( id SERIAL PRIMARY KEY, data JSONB NOT NULL );"
                 "CREATE TABLE IF NOT EXISTS ba_users ( name TEXT PRIMARY KEY, public_key TEXT );"
                 "CREATE TABLE IF NOT EXISTS ba_vouchers ("
                            "code          TEXT PRIMARY KEY,"
                            "description   TEXT NOT NULL,"
                            "restaurant_id SERIAL REFERENCES ba_restaurants (id),"
                            "user_name     TEXT REFERENCES ba_users (name)"
                 ");"
                 "CREATE TABLE IF NOT EXISTS ba_reviews ("
                            "rating        INTEGER NOT NULL,"
                            "comment       TEXT,"
                            "restaurant_id SERIAL REFERENCES ba_restaurants (id),"
                            "user_name     TEXT REFERENCES ba_users (name),"
                            "UNIQUE (restaurant_id, user_name)"
                 ");")

with database, database.cursor() as db:
    db.execute(CREATE_TABLES)

@app.get("/")
def home():
    pub = private_rsa.public_key().export_key().decode('utf-8')
    return render_template("index.html", public_rsa=pub)

# ----- RESTAURANTS -----

@app.post("/api/restaurants")
def create_restaurant():
    INSERT_RESTAURANT = "INSERT INTO ba_restaurants (data) VALUES (%s) RETURNING id;"

    data = request.get_json()
    if data is None:
        return { "message": "Missing JSON data" }, 400

    with database, database.cursor() as db:
        db.execute(INSERT_RESTAURANT, (json.dumps(data),))
        restaurant_id = db.fetchone()[0]

    return { "message": f"Restaurant created", "id": restaurant_id }, 201

@app.get("/api/restaurants")
def read_all_restaurants():
    SELECT_ALL_RESTAURANTS = "SELECT data FROM ba_restaurants;"

    with database, database.cursor() as db:
        db.execute(SELECT_ALL_RESTAURANTS)
        restaurant_data = list( i[0] for i in db.fetchall() )

    return restaurant_data

@app.get("/api/restaurants/<int:restaurant_id>")
def read_restaurant(restaurant_id):
    SELECT_RESTAURANT = "SELECT data FROM ba_restaurants WHERE id = (%s);"

    with database, database.cursor() as db:
        db.execute(SELECT_RESTAURANT, (restaurant_id,))
        get_data = db.fetchone()

    if get_data is none:
        return { "message": f"Restaurant {restaurant_id} not found." }, 404

    return get_data[0], 200

@app.put("/api/restaurants/<int:restaurant_id>")
def update_restaurant(restaurant_id):
    UPDATE_RESTAURANT = "UPDATE ba_restaurants SET data = (%s) WHERE id = (%s);"

    data = request.get_json()
    if data is None:
        return { "message": "Missing JSON data" }, 400
 
    with database, database.cursor() as db:
        db.execute(UPDATE_RESTAURANT, (json.dumps(data), restaurant_id))
        database.commit()
        effect = db.rowcount

    if effect > 0:
        return { "message": f"Restaurant {restaurant_id} updated" }, 200

    return { "message": f"Restaurant {restaurant_id} not found" }, 404

@app.delete("/api/restaurants/<int:restaurant_id>")
def delete_restaurant(restaurant_id):
    DELETE_RESTAURANT = "DELETE FROM ba_restaurants WHERE id = (%s);"

    with database, database.cursor() as db:
        db.execute(DELETE_RESTAURANT, (restaurant_id,))
        database.commit()
        effect = db.rowcount

    if effect > 0:
        return { "message": f"Restaurant {restaurant_id} deleted" }, 200

    return { "message": f"Restaurant {restaurant_id} not found" }, 404

# ----- USERS -----

def valid_name(name):
    for ch in name:
        if ch not in "qwertyuiopasdfghjklzxcvbnm_QWERTYUIOPASDFGHJKLZXCVBNM":
            return False
    return True

@app.post("/api/users")
def create_user():
    INSERT_USER = "INSERT INTO ba_users (name, public_key) VALUES (%s, %s);"

    data = request.get_json()
    name = data.get('name')
    public_key = data.get('public_key')

    if name is None:
        return { "error": "Missing name parameter" }, 400

    if not valid_name(name) or len(name) < 1:
        return { "error": "Name must be have atleast 1 character and only include 'a-Z', 'A-Z', '_'" }, 400

    with database, database.cursor() as db:
        try:
            db.execute(INSERT_USER, (name, public_key))
            database.commit()
        except psycopg2.errors.UniqueViolation:
            return { "message": f"Name has been taken" }, 500

    return { "message": f"User {name} created" }, 201

@app.get("/api/users/<user_name>")
def read_user(user_name):
    SELECT_USER = "SELECT * FROM ba_users WHERE name = (%s);"

    with database, database.cursor() as db:
        db.execute(SELECT_USER, (user_name,))
        get_data = db.fetchone()

    if get_data is None:
        return { "message": f"User {user_name} not found" }, 404

    return { 'name': get_data[0], 'public_key': get_data[1] }, 200

@app.put("/api/users/<user_name>")
def update_user(user_name):
    UPDATE_USER = "UPDATE ba_users SET public_key = (%s) WHERE name = (%s);"

    data = request.get_json()
    public_key = data.get('public_key')

    with database, database.cursor() as db:
        db.execute(UPDATE_USER, (public_key, user_name))
        database.commit()
        effect = db.rowcount

    if effect > 0:
        return { "message": f"User {user_name} updated successfully" }, 200
    else:
        return { "message": f"User {user_name} not found" }, 404

@app.delete("/api/users/<user_name>")
def delete_user(user_name):
    DELETE_USER = "DELETE FROM ba_users WHERE name = (%s);"

    with database, database.cursor() as db:
        db.execute(DELETE_USER, (user_name,))
        database.commit()
        effect = db.rowcount

    if effect > 0:
        return { "message": f"User {user_name} deleted" }, 200
    else:
        return { "message": f"User {user_name} not found" }, 404

# ----- VOUCHERS -----

@app.post("/api/vouchers")
def create_voucher():
    INSERT_VOUCHER = "INSERT INTO ba_vouchers (code, description, restaurant_id, user_name) VALUES (%s, %s, %s, %s);"

    data = request.get_json()
    user_name = data.get('user_name')
    restaurant_id = data.get('restaurant_id')
    code = data.get('code')
    description = data.get('description')

    if user_name is None:
        return { "message": "Missing user_name parameter" }, 400

    if restaurant_id is None:
        return { "message": "Missing restaurant_id parameter" }, 400

    if code is None:
        return { "message": "Missing code parameter" }, 400

    if description is None:
        return { "message": "Missing description parameter" }, 400
    
    try:
        with database, database.cursor() as db:
            db.execute(INSERT_VOUCHER, (code, description, restaurant_id, user_name))
    except psycopg2.errors.ForeignKeyViolation:
        return { "message": "user_name or restaurant_id not found" }, 404

    return { "message": "Voucher created" }, 201

@app.get("/api/vouchers")
def read_vouchers():
    SELECT_VOUCHERS = "SELECT * FROM ba_vouchers WHERE restaurant_id = (%s) OR user_name = (%s);"

    data = request.get_json()
    user_name = data.get('user_name')
    restaurant_id = data.get('restaurant_id')

    if user_name is None and restaurant_id is None:
        return { "message": "Missing restaurant_id and user_name parameter, at least one is required" }, 400

    try:
        with database, database.cursor() as db:
            db.execute(SELECT_VOUCHERS, (restaurant_id, user_name))
            vouchers = db.fetchall()
            voucher_data = list( { "code": v[0], "description": v[1], "restaurant_id": v[2], "user_name": v[3] } for v in vouchers )
    except psycopg2.errors.ForeignKeyViolation:
        return { "message": "user_name or restaurant_id not found" }, 404

    return voucher_data, 200

@app.put("/api/vouchers")
def update_voucher():
    UPDATE_VOUCHER = "UPDATE ba_vouchers SET user_name = (%s) WHERE code = (%s);"

    data = request.get_json()
    user_name = data.get('user_name')
    code = data.get('code')

    if user_name is None:
        return { "message": "Missing user_name parameter" }, 400

    if code is None:
        return { "message": "Missing code parameter" }, 400
 
    with database, database.cursor() as db:
        db.execute(UPDATE_VOUCHER, (user_name, code))
        database.commit()
        effect = db.rowcount

    if effect > 0:
        return { "message": "Voucher updated" }, 200

    return { "message": f"Voucher {code} not found" }, 404

@app.delete("/api/vouchers")
def delete_voucher():
    DELETE_VOUCHER = "DELETE FROM ba_vouchers WHERE code = (%s);"

    data = request.get_json()
    code = data.get('code')

    if code is None:
        return { "message": "Missing code parameter" }, 400
 
    with database, database.cursor() as db:
        db.execute(DELETE_VOUCHER, (code,))
        database.commit()
        effect = db.rowcount

    if effect > 0:
        return { "message": f"Voucher deleted" }, 200

    return { "message": f"Voucher {code} not found" }, 404

# ----- REVIEWS ------

@app.post("/api/reviews")
def create_review():
    INSERT_REVIEW = "INSERT INTO ba_reviews (rating, comment, restaurant_id, user_name) VALUES (%s, %s, %s, %s);"

    data = request.get_json()
    user_name = data.get('user_name')
    restaurant_id = data.get('restaurant_id')
    rating = data.get('rating')
    comment = data.get('comment')

    if user_name is None:
        return { "message": "Missing user_name parameter" }, 400

    if restaurant_id is None:
        return { "message": "Missing restaurant_id parameter" }, 400

    if rating is None:
        return { "message": "Missing rating parameter" }, 400

    if comment is None:
        return { "message": "Missing comment parameter" }, 400

    if rating < 1 or rating > 5:
        return { "message": "Rating must be between 1 and 5 stars" }, 400

    try:
        with database, database.cursor() as db:
            db.execute(INSERT_REVIEW, (rating, comment, restaurant_id, user_name))
    except psycopg2.errors.ForeignKeyViolation:
        return { "message": "user_name or restaurant_id not found" }, 404

    return { "message": "Review created" }, 201

@app.get("/api/reviews")
def read_reviews():
    SELECT_REVIEWS = "SELECT * FROM ba_reviews WHERE restaurant_id = (%s) OR user_name = (%s);"

    data = request.get_json()
    user_name = data.get('user_name')
    restaurant_id = data.get('restaurant_id')

    if user_name is None and restaurant_id is None:
        return { "message": "Missing restaurant_id and user_name parameter, at least one is required" }, 400

    try:
        with database, database.cursor() as db:
            db.execute(SELECT_REVIEWS, (restaurant_id, user_name))
            reviews = db.fetchall()
            review_data = list( { "rating": r[0], "comment": r[1], "restaurant_id": r[2], "user_name": r[3] } for r in reviews )
    except psycopg2.errors.ForeignKeyViolation:
        return { "message": "user_name or restaurant_id not found" }, 404

    return review_data, 200

@app.put("/api/reviews")
def update_review():
    UPDATE_REVIEW = "UPDATE ba_reviews SET rating = (%s), comment = (%s) WHERE restaurant_id = (%s) AND user_name = (%s);"

    data = request.get_json()
    user_name = data.get('user_name')
    restaurant_id = data.get('restaurant_id')
    rating = data.get('rating')
    comment = data.get('comment')

    if user_name is None:
        return { "message": "Missing user_name parameter" }, 400

    if restaurant_id is None:
        return { "message": "Missing restaurant_id parameter" }, 400

    if rating is None:
        return { "message": "Missing rating parameter" }, 400

    if comment is None:
        return { "message": "Missing comment parameter" }, 400

    if rating < 1 or rating > 5:
        return { "message": "Rating must be between 1 and 5 stars" }, 400

    with database, database.cursor() as db:
        db.execute(UPDATE_REVIEW, (rating, comment, restaurant_id, user_name))
        database.commit()
        effect = db.rowcount

    if effect > 0:
        return { "message": "Review updated" }, 200

    return { "message": "Review not found" }, 404

@app.delete("/api/reviews")
def delete_review():
    DELETE_REVIEW = "DELETE FROM ba_reviews WHERE restaurant_id = (%s) AND user_name = (%s);"

    data = request.get_json()
    user_name = data.get('user_name')
    restaurant_id = data.get('restaurant_id')

    if user_name is None:
        return { "message": "Missing user_name parameter" }, 400

    if restaurant_id is None:
        return { "message": "Missing restaurant_id parameter" }, 400
 
    with database, database.cursor() as db:
        db.execute(DELETE_REVIEW, (restaurant_id, user_name))
        database.commit()
        effect = db.rowcount

    if effect > 0:
        return { "message": "Review deleted" }, 200

    return { "message": "Review not found" }, 404

