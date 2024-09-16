from flask import Flask, render_template, request, jsonify
import sqlite3

app = Flask(__name__)

car_components = {
    'brand': ['BMW', 'Honda', 'Mustang'],
    'body': ['Sedan', 'SUV', 'Hatchback', 'Convertible'],
    'color': ['Red', 'Blue', 'Black', 'White', 'Silver'],
    'wheels': ['17 inch', '18 inch', '19 inch', '20 inch']
}

def get_db_connection():
    conn = sqlite3.connect('car_builds.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS car_builds
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     brand TEXT,
                     body TEXT,
                     color TEXT,
                     wheels TEXT)''')
    conn.close()

@app.route('/')
def index():
    return render_template('index.html', components=car_components)

@app.route('/build_car', methods=['POST'])
def build_car():
    selected_components = request.form.to_dict()
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO car_builds (brand, body, color, wheels) VALUES (?, ?, ?, ?)",
                (selected_components['brand'], selected_components['body'],
                 selected_components['color'], selected_components['wheels']))
    conn.commit()
    build_id = cur.lastrowid
    conn.close()
    
    return jsonify({'message': 'Car built successfully!', 'car': selected_components, 'build_id': build_id})

@app.route('/builds')
def get_builds():
    conn = get_db_connection()
    builds = conn.execute('SELECT * FROM car_builds').fetchall()
    conn.close()
    return jsonify([dict(ix) for ix in builds])

if __name__ == '__main__':
    init_db()
    app.run(debug=True)