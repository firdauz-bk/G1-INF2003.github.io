from flask import Flask, render_template, request, redirect, url_for, flash, g
import sqlite3
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

DATABASE = 'carcraft.db'

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ILOVEINF2003'
login_manager = LoginManager(app)
login_manager.login_view = 'login'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # This enables column access by name: row['column_name']
    return conn

def init_db():
    with app.app_context():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                admin BOOLEAN DEFAULT FALSE
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                post_id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE CASCADE
            )
        ''')
        conn.commit()
        conn.close()

class User(UserMixin):
    def __init__(self, user_id, username, email, password_hash, admin):
        self.id = user_id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.admin = admin

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def get(user_id):
        conn = get_db_connection()
        user_data = conn.execute('SELECT * FROM user WHERE user_id = ?', (user_id,)).fetchone()
        conn.close()
        if user_data:
            return User(
                user_id=user_data['user_id'],
                username=user_data['username'],
                email=user_data['email'],
                password_hash=user_data['password_hash'],
                admin=bool(user_data['admin'])
            )
        return None

    @staticmethod
    def get_by_username(username):
        conn = get_db_connection()
        user_data = conn.execute('SELECT * FROM user WHERE username = ?', (username,)).fetchone()
        conn.close()
        if user_data:
            return User(
                user_id=user_data['user_id'],
                username=user_data['username'],
                email=user_data['email'],
                password_hash=user_data['password_hash'],
                admin=bool(user_data['admin'])
            )
        return None

    @staticmethod
    def get_all_users():
        conn = get_db_connection()
        users_data = conn.execute('SELECT * FROM user').fetchall()
        conn.close()
        users = []
        for user_data in users_data:
            users.append(User(
                user_id=user_data['user_id'],
                username=user_data['username'],
                email=user_data['email'],
                password_hash=user_data['password_hash'],
                admin=bool(user_data['admin'])
            ))
        return users

    def save(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        if self.id:  # Update existing user
            cursor.execute('''
                UPDATE user SET username = ?, email = ?, password_hash = ?, admin = ?
                WHERE user_id = ?
            ''', (self.username, self.email, self.password_hash, int(self.admin), self.id))
        else:  # Create new user
            cursor.execute('''
                INSERT INTO user (username, email, password_hash, admin)
                VALUES (?, ?, ?, ?)
            ''', (self.username, self.email, self.password_hash, int(self.admin)))
            self.id = cursor.lastrowid
        conn.commit()
        conn.close()

    def delete(self):
        conn = get_db_connection()
        conn.execute('DELETE FROM user WHERE user_id = ?', (self.id,))
        conn.commit()
        conn.close()

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.get_by_username(username)
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('home'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/create_user', methods=['GET', 'POST'])
def create_user():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        admin = request.form.get('admin') == 'on'
        
        user = User(None, username, email, None, admin)
        user.set_password(password)
        user.save()
        flash('User created successfully')
        return redirect(url_for('home'))
    return render_template('create_user.html')

@app.route('/admin')
@login_required
def admin():
    if not current_user.admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('home'))
    users = User.get_all_users()
    return render_template('admin.html', users=users)

@app.route('/admin/update_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def update_user(user_id):
    if not current_user.admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('home'))
    
    user = User.get(user_id)
    if not user:
        flash('User not found')
        return redirect(url_for('admin'))
    if request.method == 'POST':
        user.username = request.form.get('username')
        user.email = request.form.get('email')
        user.admin = request.form.get('admin') == 'on'
        if request.form.get('password'):
            user.set_password(request.form.get('password'))
        user.save()
        flash('User updated successfully')
        return redirect(url_for('admin'))
    return render_template('update_user.html', user=user)

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('home'))
    
    user = User.get(user_id)
    if user:
        user.delete()
        flash('User deleted successfully')
    else:
        flash('User not found')
    return redirect(url_for('admin'))

# Route to create a new post
@app.route('/createpost', methods=['GET', 'POST'])
@login_required
def create_post():  # Updated function name to 'create_post'
    if request.method == 'POST':
        # Retrieve form data
        title = request.form['title']
        description = request.form['description']

        # Validate inputs
        if not title or not description:
            flash('Title and Description are required fields!')
            return redirect(url_for('create_post'))  # Use 'create_post' to match function name

        # Insert the new post into the database
        conn = get_db_connection()
        conn.execute('INSERT INTO posts (title, description, user_id) VALUES (?, ?, ?)',
                     (title, description, current_user.id))
        conn.commit()
        conn.close()

        # Show success message and redirect to the forum page
        flash('Post created successfully!')
        return redirect(url_for('forum'))  # Redirect to 'forum' page to view posts

    # Render the post creation form
    return render_template('createpost.html')

@app.route('/forum')
def forum():
    conn = get_db_connection()
    # Retrieve posts and join with user table to get username
    posts = conn.execute('''
        SELECT p.post_id, p.title, p.description, p.created_at, u.username 
        FROM posts p 
        JOIN user u ON p.user_id = u.user_id
        ORDER BY p.created_at DESC
    ''').fetchall()
    conn.close()
    return render_template('forum.html', posts=posts)
if __name__ == '__main__':
    init_db()
    app.run(debug=True)