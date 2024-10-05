from flask import Flask, render_template, request, redirect, url_for, flash, g, jsonify
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
    
    conn = get_db_connection()
    
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'create_vehicle_type':
            name = request.form.get('name')
            conn.execute('INSERT INTO vehicle_type (name) VALUES (?)', (name,))
        elif action == 'update_vehicle_type':
            type_id = request.form.get('type_id')
            name = request.form.get('name')
            conn.execute('UPDATE vehicle_type SET name = ? WHERE type_id = ?', (name, type_id))
        elif action == 'delete_vehicle_type':
            type_id = request.form.get('type_id')
            conn.execute('DELETE FROM vehicle_type WHERE type_id = ?', (type_id,))
        
        # Add similar blocks for other entity types (brand, model, color, wheel_set)
        
        conn.commit()
        return redirect(url_for('admin'))
    
    users = User.get_all_users()
    vehicle_types = conn.execute('SELECT * FROM vehicle_type').fetchall()
    brands = conn.execute('SELECT * FROM brand').fetchall()
    models = conn.execute('''
        SELECT model.model_id, model.name as model_name, brand.name as brand_name, vehicle_type.name as type_name
        FROM model
        JOIN brand ON model.brand_id = brand.brand_id
        JOIN vehicle_type ON model.type_id = vehicle_type.type_id
        ORDER BY model.name
    ''').fetchall()
    colors = conn.execute('SELECT * FROM color').fetchall()
    wheel_sets = conn.execute('SELECT * FROM wheel_set').fetchall()
    
    conn.close()
    
    return render_template('admin.html', users=users, vehicle_types=vehicle_types, 
                           brands=brands, models=models, colors=colors, wheel_sets=wheel_sets)



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
        conn.execute('INSERT INTO post (title, description, user_id) VALUES (?, ?, ?)',
                     (title, description, current_user.id))
        conn.commit()
        conn.close()

        # Show success message and redirect to the forum page
        flash('Post created successfully!')
        return redirect(url_for('forum'))  # Redirect to 'forum' page to view posts

    # Render the post creation form
    return render_template('createpost.html')

# Route to create a new comment
@app.route('/create_comment/<int:post_id>', methods=['GET', 'POST'])
@login_required
def create_comment(post_id):
    if request.method == 'POST':
        content = request.form['content']
        user_id = current_user.id

        # Validate input
        if not content:
            flash('Comment cannot be empty.')
            return redirect(url_for('create_comment', post_id=post_id))

        # Insert the new comment into the database
        conn = get_db_connection()
        conn.execute('INSERT INTO comment (content, user_id, post_id) VALUES (?, ?, ?)',
                     (content, user_id, post_id))
        conn.commit()
        conn.close()

        # Redirect to the forum or post page after adding a comment
        flash('Comment added successfully!')
        return redirect(url_for('forum'))

    # Retrieve all comments related to the post
    conn = get_db_connection()
    comments = conn.execute('''
        SELECT c.comment_id, c.content, c.created_at, u.username 
        FROM comment c 
        JOIN user u ON c.user_id = u.user_id
        WHERE c.post_id = ?
        ORDER BY c.created_at DESC
    ''', (post_id,)).fetchall()
    conn.close()

    return render_template('create_comment.html', comments=comments, post_id=post_id)

@app.route('/edit_comment/<int:comment_id>', methods=['GET', 'POST'])
@login_required
def edit_comment(comment_id):
    conn = get_db_connection()
    comment = conn.execute('SELECT * FROM comment WHERE comment_id = ?', (comment_id,)).fetchone()
    if comment is None:
        flash('Comment not found')
        return redirect(url_for('forum'))

    # Add the print statement here to debug
    print(f"Current user ID: {current_user.id}, Comment user ID: {comment['user_id']}")
    
    # Check if the current user is the comment owner or an admin
    if current_user.id != comment['user_id'] and not current_user.admin:
        flash('Access denied.')
        return redirect(url_for('forum'))

    if request.method == 'POST':
        new_content = request.form['content']
        if not new_content:
            flash('Comment cannot be empty.')
        else:
            conn.execute('UPDATE comment SET content = ? WHERE comment_id = ?', (new_content, comment_id))
            conn.commit()
            flash('Comment updated successfully.')
        conn.close()
        return redirect(url_for('forum'))

    conn.close()
    return render_template('edit_comment.html', comment=comment)

@app.route('/delete_comment/<int:comment_id>', methods=['POST'])
@login_required
def delete_comment(comment_id):
    conn = get_db_connection()
    comment = conn.execute('SELECT * FROM comment WHERE comment_id = ?', (comment_id,)).fetchone()
    if comment is None:
        flash('Comment not found')
        return redirect(url_for('forum'))

    # Add the print statement here to debug
    print(f"Current user ID: {current_user.id}, Comment user ID: {comment['user_id']}")

    # Check if the current user is the comment owner or an admin
    if current_user.id != comment['user_id'] and not current_user.admin:
        flash('Access denied.')
        return redirect(url_for('forum'))

    conn.execute('DELETE FROM comment WHERE comment_id = ?', (comment_id,))
    conn.commit()
    conn.close()
    flash('Comment deleted successfully.')
    return redirect(url_for('forum'))


@app.route('/forum')
def forum():
    conn = get_db_connection()
    # Retrieve posts and join with user table to get username
    posts = conn.execute('''
        SELECT p.post_id, p.title, p.description, p.created_at, u.username 
        FROM post p 
        JOIN user u ON p.user_id = u.user_id
        ORDER BY p.created_at DESC
    ''').fetchall()
    
    # Fetch comments for each post
    posts_with_comments = []
    for post in posts:
        comments = conn.execute('''
            SELECT c.comment_id, c.content, c.created_at, c.user_id, u.username 
            FROM comment c 
            JOIN user u ON c.user_id = u.user_id
            WHERE c.post_id = ?
            ORDER BY c.created_at DESC
        ''', (post['post_id'],)).fetchall()
        
        # Debugging information
        for comment in comments:
            print(f"Current user ID: {current_user.id}, Comment user ID: {comment['user_id']}")
        
        posts_with_comments.append({
            'post': post,
            'comments': comments
        })
        
    conn.close()
    return render_template('forum.html', posts_with_comments=posts_with_comments)

# Route to display all models
@app.route('/models')
@login_required
def models():
    conn = get_db_connection()
    models = conn.execute('''
        SELECT model.model_id, model.name as model_name, brand.name as brand_name, vehicle_type.name as type_name
        FROM model
        JOIN brand ON model.brand_id = brand.brand_id
        JOIN vehicle_type ON model.type_id = vehicle_type.type_id
        ORDER BY model.name
    ''').fetchall()
    conn.close()
    return render_template('model.html', models=models)

# Route to create a new model
@app.route('/create_model', methods=['GET', 'POST'])
@login_required
def create_model():
    if request.method == 'POST':
        name = request.form['name']
        brand_id = request.form['brand_id']
        type_id = request.form['type_id']
        
        if not name or not brand_id or not type_id:
            flash('All fields are required.')
            return redirect(url_for('create_model'))

        conn = get_db_connection()
        conn.execute('''
            INSERT INTO model (name, brand_id, type_id) VALUES (?, ?, ?)
        ''', (name, brand_id, type_id))
        conn.commit()
        conn.close()

        flash('Model added successfully!')
        return redirect(url_for('models'))
    
    # Retrieve brands and vehicle types for the form dropdowns
    conn = get_db_connection()
    brands = conn.execute('SELECT * FROM brand').fetchall()
    vehicle_types = conn.execute('SELECT * FROM vehicle_type').fetchall()
    conn.close()

    return render_template('create_model.html', brands=brands, vehicle_types=vehicle_types)

# Route to update a model
@app.route('/edit_model/<int:model_id>', methods=['GET', 'POST'])
@login_required
def edit_model(model_id):
    conn = get_db_connection()
    model = conn.execute('SELECT * FROM model WHERE model_id = ?', (model_id,)).fetchone()
    
    if not model:
        flash('Model not found.')
        return redirect(url_for('models'))
    
    if request.method == 'POST':
        name = request.form['name']
        brand_id = request.form['brand_id']
        type_id = request.form['type_id']
        
        if not name or not brand_id or not type_id:
            flash('All fields are required.')
        else:
            conn.execute('''
                UPDATE model SET name = ?, brand_id = ?, type_id = ? WHERE model_id = ?
            ''', (name, brand_id, type_id, model_id))
            conn.commit()
            conn.close()
            flash('Model updated successfully!')
            return redirect(url_for('models'))

    # Retrieve brands and vehicle types for the form dropdowns
    brands = conn.execute('SELECT * FROM brand').fetchall()
    vehicle_types = conn.execute('SELECT * FROM vehicle_type').fetchall()
    conn.close()

    return render_template('edit_model.html', model=model, brands=brands, vehicle_types=vehicle_types)

# Route to delete a model
@app.route('/delete_model/<int:model_id>', methods=['POST'])
@login_required
def delete_model(model_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM model WHERE model_id = ?', (model_id,))
    conn.commit()
    conn.close()
    flash('Model deleted successfully!')
    return redirect(url_for('models'))


@app.route('/customize', methods=['GET', 'POST'])
@login_required
def customize():
    db = get_db_connection()

    if request.method == 'POST':
        if 'delete_id' in request.form:
            # Handle deletion
            delete_id = request.form['delete_id']
            db.execute('DELETE FROM customization WHERE customization_id = ?', (delete_id,))
            db.commit()
        else:
            # Check if we are updating or creating
            customization_id = request.form.get('customization_id')
            customization_name = request.form.get('customization_name')  # Added this to capture customization_name
            brand_id = request.form['brand_id']
            model_id = request.form['model_id']
            color_id = request.form['color_id']
            wheel_id = request.form['wheel_id']

            if not customization_name:
                flash('Customization name is required!', 'error')
                return redirect(url_for('customize'))

            if customization_id:
                # Update existing customization, including customization_name
                db.execute('''
                    UPDATE customization 
                    SET customization_name = ?, model_id = ?, color_id = ?, wheel_id = ? 
                    WHERE customization_id = ?
                ''', (customization_name, model_id, color_id, wheel_id, customization_id))
            else:
                # Insert new customization for the logged-in user, including customization_name
                db.execute(
                    'INSERT INTO customization (customization_name, user_id, model_id, color_id, wheel_id) VALUES (?, ?, ?, ?, ?)',
                    (customization_name, current_user.id, model_id, color_id, wheel_id)
                )

            db.commit()

    # Fetch available options for the form
    brands = db.execute('SELECT brand_id, name FROM brand').fetchall()
    colors = db.execute('SELECT color_id, name FROM color').fetchall()
    wheels = db.execute('SELECT wheel_id, name FROM wheel_set').fetchall()

    # Fetch models for the first brand if exists
    models = []
    if brands:
        default_brand_id = brands[0]['brand_id']
        models = db.execute('SELECT model_id, name FROM model WHERE brand_id = ?', (default_brand_id,)).fetchall()

    # Fetch current customizations for the logged-in user
    customizations = db.execute('''
        SELECT customization.customization_id, customization.customization_name, brand.name AS brand_name, 
               model.name AS model_name, color.name AS color_name, wheel_set.name AS wheel_name, 
               customization.created_at
        FROM customization
        JOIN model ON customization.model_id = model.model_id
        JOIN brand ON model.brand_id = brand.brand_id
        JOIN color ON customization.color_id = color.color_id
        JOIN wheel_set ON customization.wheel_id = wheel_set.wheel_id
        WHERE customization.user_id = ?
    ''', (current_user.id,)).fetchall()

    return render_template('customize.html', brands=brands, colors=colors, wheels=wheels, models=models, customizations=customizations)



@app.route('/edit_customization/<int:customization_id>', methods=['GET', 'POST'])
@login_required
def edit_customization(customization_id):
    db = get_db_connection()

    # Fetch the customization details, including model_id and the associated brand_id
    customization = db.execute('''
        SELECT customization.customization_id, 
               customization.customization_name,
               customization.model_id, 
               customization.color_id, 
               customization.wheel_id,
               model.brand_id
        FROM customization
        JOIN model ON customization.model_id = model.model_id
        WHERE customization.customization_id = ?
    ''', (customization_id,)).fetchone()

    if not customization:
        return "Customization not found", 404

    if request.method == 'POST':
        # Update the customization, including the customization_name
        customization_name = request.form['customization_name']
        db.execute('''
            UPDATE customization 
            SET customization_name = ?, model_id = ?, color_id = ?, wheel_id = ? 
            WHERE customization_id = ?
        ''', (customization_name, request.form['model_id'], request.form['color_id'], request.form['wheel_id'], customization_id))
        db.commit()

        return redirect(url_for('customize'))  # Redirect to the main customization page

    # Fetch available options for the form
    brands = db.execute('SELECT brand_id, name FROM brand').fetchall()
    colors = db.execute('SELECT color_id, name FROM color').fetchall()
    wheels = db.execute('SELECT wheel_id, name FROM wheel_set').fetchall()

    # Fetch models based on the current model's brand_id
    models = db.execute('SELECT model_id, name FROM model WHERE brand_id = ?', (customization['brand_id'],)).fetchall()

    return render_template('edit_customization.html', customization=customization, brands=brands, colors=colors, wheels=wheels, models=models)



@app.route('/get_models/<int:brand_id>')
def get_models(brand_id):
    conn = sqlite3.connect('carcraft.db')
    cursor = conn.cursor()

    # Fetch models for the selected brand
    cursor.execute('SELECT model_id, name FROM model WHERE brand_id = ?', (brand_id,))
    models = cursor.fetchall()

    conn.close()

    # Debugging information
    print("Fetched models for brand_id {}: {}".format(brand_id, models))

    return jsonify(models)


@app.route('/vehicle_type', methods=["GET", 'POST'])
@login_required
def vehicle_type():
    if not current_user.admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        conn = get_db_connection()

        name = request.form['name']
        # Check if the name already exists in the table
        result = conn.execute('SELECT COUNT(1) FROM vehicle_type WHERE name = ?', (name,)).fetchone()
        if result[0] > 0:
            flash("Name already exists!")
            return redirect(url_for('vehicle_type')) 

        # If not, add the new vehicle type to the table
        conn.execute('INSERT INTO vehicle_type (name) VALUES (?)', (name, ))
        conn.commit()
        conn.close()

        return redirect(url_for('vehicle_type'))
    
    # Retrieve all comments related to the post
    conn = get_db_connection()
    vehicle_types = conn.execute('SELECT * FROM vehicle_type').fetchall()
    conn.close()

    return render_template('vehicle_type.html', vehicle_types=vehicle_types)

@app.route('/vehicle_type/edit/<int:type_id>', methods=["GET", 'POST'])
@login_required
def vehicle_type_edit(type_id):
    if not current_user.admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        conn = get_db_connection()
        name = request.form['name']

        # Check if the name already exists in the table
        result = conn.execute('SELECT COUNT(1) FROM vehicle_type WHERE name = ?', (name,)).fetchone()
        if result[0] > 0:
            flash("Name already exists!")
            return redirect(url_for('vehicle_type')) 

        # If not, add new vehicle_type to database
        name = request.form['name']
        conn.execute('UPDATE vehicle_type SET name = ? WHERE type_id = ?', (name, type_id))
        conn.commit()
        conn.close()

    return redirect(url_for('vehicle_type'))

@app.route('/vehicle_type/delete/<int:type_id>', methods=["GET", 'POST'])
@login_required
def vehicle_type_delete(type_id):
    if not current_user.admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('home'))
    
    conn = get_db_connection()
    conn.execute('DELETE FROM vehicle_type WHERE type_id=?', (type_id,))
    conn.commit()
    conn.close()

    return redirect(url_for('vehicle_type'))


@app.route('/brand_type', methods=["GET", 'POST'])
@login_required
def brand_type():
    if not current_user.admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        name = request.form['name']
        conn = get_db_connection()

        # Check if the name already exists in the table
        result = conn.execute('SELECT COUNT(1) FROM brand WHERE name = ?', (name,)).fetchone()
        if result[0] > 0:
            flash("Name already exists!")
            return redirect(url_for('brand_type')) 

        # If not, add it to the 
        conn.execute('INSERT INTO brand (name) VALUES (?)', (name, ))
        conn.commit()
        conn.close()

        return redirect(url_for('brand_type'))
    
    # Retrieve all comments related to the post
    conn = get_db_connection()
    brands = conn.execute('SELECT * FROM brand').fetchall()
    return render_template('brand_type.html', brands=brands)

@app.route('/brand_type/edit/<int:brand_id>', methods=["GET", 'POST'])
@login_required
def brand_type_edit(brand_id):
    if not current_user.admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        conn = get_db_connection()
        name = request.form['name']

        # Check if the name already exists in the table
        result = conn.execute('SELECT COUNT(1) FROM brand WHERE name = ?', (name,)).fetchone()
        if result[0] > 0:
            flash("Name already exists!")
            return redirect(url_for('brand_type'))

        # If not add it to the brand table
        conn.execute('UPDATE brand SET name = ? WHERE brand_id=?', (name, brand_id))
        conn.commit()
        conn.close()

    return redirect(url_for('brand_type'))

@app.route('/brand_type/delete/<int:brand_id>', methods=["GET", 'POST'])
@login_required
def brand_type_delete(brand_id):
    if not current_user.admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('home'))

    conn = get_db_connection()
    conn.execute('DELETE FROM brand WHERE brand_id=?', (brand_id,))
    conn.commit()
    conn.close()

    return redirect(url_for('brand_type'))


if __name__ == '__main__':
    app.run(debug=True)