/*For VM4*/

DROP TABLE IF EXISTS ba_restaurants;
DROP TABLE IF EXISTS ba_users;
DROP TABLE IF EXISTS ba_vouchers;
DROP TABLE IF EXISTS ba_reviews;

CREATE TABLE ba_restaurants (
	id SERIAL PRIMARY KEY,
	data JSONB NOT NULL
);

CREATE TABLE ba_users (
	name TEXT UNIQUE PRIMARY KEY,
    password TEXT NOT NULL,
	public_key TEXT UNIQUE NOT NULL
);

CREATE TABLE ba_vouchers (
	code TEXT UNIQUE NOT NULL,
	description TEXT NOT NULL,
	rest_id SERIAL NOT NULL,
	user_name TEXT NOT NULL,
	FOREIGN KEY (rest_id) REFERENCES ba_restaurants (id),
	FOREIGN KEY (user_name) REFERENCES ba_users (name),
);

CREATE TABLE ba_reviews (
	valuation INTEGER NOT NULL,
	description TEXT,
	rest_id SERIAL NOT NULL,
	user_name TEXT NOT NULL,
	FOREIGN KEY (rest_id) REFERENCES ba_restaurants (id),
	FOREIGN KEY (user_name) REFERENCES ba_users (name),
);
