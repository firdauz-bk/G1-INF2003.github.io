DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS comment;
DROP TABLE IF EXISTS post;
DROP TABLE IF EXISTS vehicle_type;
DROP TABLE IF EXISTS model;
DROP TABLE IF EXISTS customization;
DROP TABLE IF EXISTS brand;
DROP TABLE IF EXISTS color;
DROP TABLE IF EXISTS wheel_set;

CREATE TABLE user (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(64) NOT NULL,
    email VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    admin INTEGER DEFAULT 0 -- In SQLite, BOOLEAN is represented as INTEGER (0 for false, 1 for true)
);

CREATE TABLE comment (
    comment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (post_id) REFERENCES post(post_id),
    FOREIGN KEY (user_id) REFERENCES user(user_id)
);

CREATE TABLE post (
    post_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customization_id INTEGER,
    user_id INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customization_id) REFERENCES customization(customization_id),
    FOREIGN KEY (user_id) REFERENCES user(user_id)
);

CREATE TABLE vehicle_type (
    type_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(20) NOT NULL
);

CREATE TABLE model (
    model_id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand_id INTEGER NOT NULL,
    type_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    FOREIGN KEY (brand_id) REFERENCES brand(brand_id),
    FOREIGN KEY (type_id) REFERENCES vehicle_type(type_id)
);

CREATE TABLE customization (
    customization_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    model_id INTEGER NOT NULL,
    color_id INTEGER NOT NULL,
    wheel_id INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(user_id),
    FOREIGN KEY (model_id) REFERENCES model(model_id),
    FOREIGN KEY (color_id) REFERENCES color(color_id),
    FOREIGN KEY (wheel_id) REFERENCES wheel_set(wheel_id)
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