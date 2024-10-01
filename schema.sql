DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS comment;
DROP TABLE IF EXISTS post;
DROP TABLE IF EXISTS vehicle_type;
DROP TABLE IF EXISTS model;
DROP TABLE IF EXISTS customization;
DROP TABLE IF EXISTS brand;
DROP TABLE IF EXISTS color;
DROP TABLE IF EXISTS wheel_set;
DROP TABLE IF EXISTS car_builds;

CREATE TABLE user (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    email TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    admin INTEGER DEFAULT 0 -- In SQLite, BOOLEAN is represented as INTEGER (0 for false, 1 for true)
);


CREATE TABLE comment (
    comment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE post (
    post_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customization_id INTEGER,
    user_id INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE vehicle_type (
    type_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(20) NOT NULL
);


CREATE TABLE model (
    model_id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand_id INTEGER NOT NULL,
    type_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL
);


CREATE TABLE customization (
    customization_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    model_id INTEGER NOT NULL,
    color_id INTEGER NOT NULL,
    wheel_id INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE brand (
    brand_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(20)
);

CREATE TABLE color (
    color_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50)
);

CREATE TABLE wheel_set (
    wheel_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100),
    description TEXT
);

CREATE TABLE car_builds
    (id INTEGER PRIMARY KEY AUTOINCREMENT,
        brand TEXT,
        body TEXT,
        color TEXT,
        wheels TEXT);