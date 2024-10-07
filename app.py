from flask import Flask, render_template, request, redirect, url_for, flash, g, jsonify
import sqlite3
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

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
        
        conn = get_db_connection()
        
        # Check if username or email already exists
        existing_user = conn.execute('SELECT * FROM user WHERE username = ? OR email = ?', (username, email)).fetchone()
        if existing_user:
            conn.close()
            if existing_user['username'] == username:
                flash('Username already exists. Please choose a different username.')
            else:
                flash('Email already exists. Please use a different email address.')
            return render_template('create_user.html')
        
        user = User(None, username, email, None, admin)
        user.set_password(password)
        user.save()
        conn.close()
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

@app.route('/admin/update_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def update_user(user_id):
    if not current_user.admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('home'))
    
    conn = get_db_connection()
    user = User.get(user_id)
    if not user:
        flash('User not found')
        return redirect(url_for('admin'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        admin = request.form.get('admin') == 'on'
        
        # Check if username or email already exists for other users
        existing_user = conn.execute('SELECT * FROM user WHERE (username = ? OR email = ?) AND user_id != ?', 
                                     (username, email, user_id)).fetchone()
        if existing_user:
            conn.close()
            if existing_user['username'] == username:
                flash('Username already exists. Please choose a different username.')
            else:
                flash('Email already exists. Please use a different email address.')
            return render_template('update_user.html', user=user)
        
        user.username = username
        user.email = email
        user.admin = admin
        if request.form.get('password'):
            user.set_password(request.form.get('password'))
        user.save()
        conn.close()
        flash('User updated successfully')
        return redirect(url_for('admin'))
    
    conn.close()
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

@app.route('/post/<int:post_id>', methods=['GET'])
def view_post(post_id):
    conn = get_db_connection()
    
    # Fetch the post
    post = conn.execute('''
        SELECT p.post_id, p.title, p.description, p.created_at, p.user_id, u.username, c.customization_name AS customization_name, c.customization_id
        FROM post p
        JOIN user u ON p.user_id = u.user_id
        LEFT JOIN customization c ON p.customization_id = c.customization_id
        WHERE p.post_id = ?
    ''', (post_id,)).fetchone()

    if post is None:
        flash('Post not found.')
        return redirect(url_for('forum'))

    # Fetch comments for this post
    comments = conn.execute('''
        SELECT c.comment_id, c.content, c.created_at, c.user_id, u.username 
        FROM comment c 
        JOIN user u ON c.user_id = u.user_id
        WHERE c.post_id = ?
        ORDER BY c.created_at DESC
    ''', (post_id,)).fetchall()

        # Fetch customization details if customization_id exists
    customization_data = None
    if post['customization_id']:
        customization_data = conn.execute('''
            SELECT brand.name AS brand_name, model.name AS model_name, 
                   color.name AS color_name, wheel_set.name AS wheel_name
            FROM customization
            JOIN model ON customization.model_id = model.model_id
            JOIN brand ON model.brand_id = brand.brand_id
            JOIN color ON customization.color_id = color.color_id
            JOIN wheel_set ON customization.wheel_id = wheel_set.wheel_id
            WHERE customization.customization_id = ?
        ''', (post['customization_id'],)).fetchone()

    conn.close()
    
    return render_template('view_post.html', post=post, comments=comments, customization_data=customization_data)


@app.route('/createpost', methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == 'POST':
        # Retrieve form data
        title = request.form['title']
        description = request.form['description']
        customization_id = request.form.get('customization_id')
        category = request.form['category']  # Get the selected category

        # Validate inputs
        if not title or not description:
            flash('Title and Description are required fields!')
            return redirect(url_for('create_post'))

        # Ensure customization_id is provided only for "customization showcase" category
        if category == 'customization showcase' and not customization_id:
            flash('Customization is required for the Customization Showcase category!')
            return redirect(url_for('create_post'))
        
        # Set customization_id to None if not provided or empty
        if customization_id == "" or customization_id is None:
            customization_id = None

        # Insert the new post into the database
        conn = get_db_connection()
        conn.execute('INSERT INTO post (title, description, user_id, customization_id, category) VALUES (?, ?, ?, ?, ?)',
                     (title, description, current_user.id, customization_id, category))


        # if category == "customization showcase":
        #     conn.execute('INSERT INTO post (title, description, user_id, customization_id, category) VALUES (?, ?, ?, ?, ?)',
        #                  (title, description, current_user.id, customization_id, category))
        # else:
        #     conn.execute('INSERT INTO post (title, description, user_id, category) VALUES (?, ?, ?, ?)',
        #                  (title, description, current_user.id, category))

        conn.commit()
        conn.close()

        # Show success message and redirect to the forum page
        flash('Post created successfully!')
        print(f"Customization ID: {customization_id}")
        return redirect(url_for('forum'))

    # Fetch all available customizations for the dropdown that belong to the current user
    conn = get_db_connection()
    customizations = conn.execute('SELECT customization_id, customization_name FROM customization WHERE user_id = ?', (current_user.id,)).fetchall()
    conn.close()

    return render_template('createpost.html', customizations=customizations)

@app.route('/forum/category/<string:category_name>', methods=['GET'])
def posts_by_category(category_name):
    # Fetch posts by category, including username and customization details
    conn = get_db_connection()
    
    query = '''
        SELECT p.post_id, p.title, p.description, p.created_at, p.user_id, u.username, 
               c.customization_name, c.customization_id
        FROM post p
        JOIN user u ON p.user_id = u.user_id
        LEFT JOIN customization c ON p.customization_id = c.customization_id
        WHERE p.category = ?
        ORDER BY p.created_at DESC
    '''
    
    posts = conn.execute(query, (category_name,)).fetchall()
    conn.close()

    return render_template('category_posts.html', posts=posts, category_name=category_name)



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
            return redirect(url_for('view_post', post_id=post_id))  # Redirect to the same post page
        
        # Insert the new comment into the database
        conn = get_db_connection()
        conn.execute('INSERT INTO comment (content, user_id, post_id) VALUES (?, ?, ?)',
                     (content, user_id, post_id))
        conn.commit()
        conn.close()

        # Fetch the newly created comment to return it
        new_comment = {
            'content': content,
            'created_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),  # Adjust format as needed
            'username': current_user.username  # Assuming username is available in the user model
        }

       # Flash a success message and stay on the same page
        flash('Comment added successfully!')
        return redirect(url_for('view_post', post_id=post_id))  # Redirect back to the post page


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
    print(current_user.__dict__)
    print(current_user.is_authenticated)
    print(current_user.admin)
    conn = get_db_connection()

    # Get filter parameters from request args
    selected_brand_id = request.args.get('brand')
    selected_color_id = request.args.get('color')
    selected_wheel_id = request.args.get('wheel')
    
    # Pagination settings
    page = request.args.get('page', 1, type=int)
    per_page = 5
    offset = (page - 1) * per_page

    # Construct the base query for posts, including category
    query = '''
        SELECT p.post_id, p.title, p.description, p.created_at, p.user_id, u.username, 
               c.customization_name AS customization_name, c.customization_id,
               p.category
        FROM post p
        JOIN user u ON p.user_id = u.user_id
        LEFT JOIN customization c ON p.customization_id = c.customization_id
        WHERE 1=1
    '''
    
    # Add filters to the query if selected
    params = []
    if selected_brand_id:
        query += ' AND c.model_id IN (SELECT model_id FROM model WHERE brand_id = ?)'
        params.append(selected_brand_id)
    if selected_color_id:
        query += ' AND c.color_id = ?'
        params.append(selected_color_id)
    if selected_wheel_id:
        query += ' AND c.wheel_id = ?'
        params.append(selected_wheel_id)

    # Add pagination
    query += ' ORDER BY p.created_at DESC LIMIT ? OFFSET ?'
    params.append(per_page)
    params.append(offset)

    # Execute the query
    posts = conn.execute(query, params).fetchall()

    # Fetch comments and customization details for each post
    posts_with_comments = []
    for post in posts:
        comments = conn.execute('''
            SELECT c.comment_id, c.content, c.created_at, c.user_id, u.username 
            FROM comment c 
            JOIN user u ON c.user_id = u.user_id
            WHERE c.post_id = ?
            ORDER BY c.created_at DESC
        ''', (post['post_id'],)).fetchall()

        # Fetch customization details if customization_id exists
        customization_data = None
        if post['customization_id']:
            customization_data = conn.execute('''
                SELECT brand.name AS brand_name, model.name AS model_name, 
                       color.name AS color_name, wheel_set.name AS wheel_name
                FROM customization
                JOIN model ON customization.model_id = model.model_id
                JOIN brand ON model.brand_id = brand.brand_id
                JOIN color ON customization.color_id = color.color_id
                JOIN wheel_set ON customization.wheel_id = wheel_set.wheel_id
                WHERE customization.customization_id = ?
            ''', (post['customization_id'],)).fetchone()

        # Append post with its comments and customization data (if any)
        posts_with_comments.append({
            'post': post,
            'comments': comments,
            'customization_data': customization_data
        })

    

    # Fetch total posts for pagination
    total_posts_query = '''
        SELECT COUNT(*) AS total FROM post p
        LEFT JOIN customization c ON p.customization_id = c.customization_id
        WHERE 1=1
    '''
    total_params = []
    if selected_brand_id:
        total_posts_query += ' AND c.model_id IN (SELECT model_id FROM model WHERE brand_id = ?)'
        total_params.append(selected_brand_id)
    if selected_color_id:
        total_posts_query += ' AND c.color_id = ?'
        total_params.append(selected_color_id)
    if selected_wheel_id:
        total_posts_query += ' AND c.wheel_id = ?'
        total_params.append(selected_wheel_id)

    total_posts = conn.execute(total_posts_query, total_params).fetchone()['total']
    total_pages = (total_posts + per_page - 1) // per_page  # Calculate total pages

    # Fetch all available customizations for the dropdown only if user is authenticated
    customizations = []
    if current_user.is_authenticated:
        customizations = conn.execute('SELECT customization_id, customization_name FROM customization WHERE user_id = ?', (current_user.id,)).fetchall()

    # Fetch dropdown options: brands, colors, and wheels
    brands = conn.execute('SELECT * FROM brand').fetchall()
    colors = conn.execute('SELECT * FROM color').fetchall()
    wheels = conn.execute('SELECT * FROM wheel_set').fetchall()

    conn.close()

    # Convert rows to dictionaries for easy use in Jinja2 templates
    brands = [dict(row) for row in brands]
    colors = [dict(row) for row in colors]
    wheels = [dict(row) for row in wheels]

    # Pass the selected filter IDs and pagination info to the template
    return render_template('forum.html', 
                           posts_with_comments=posts_with_comments, 
                           customizations=customizations,
                           brands=brands, 
                           colors=colors, 
                           wheels=wheels,
                           selected_brand_id=selected_brand_id,
                           selected_color_id=selected_color_id,
                           selected_wheel_id=selected_wheel_id,
                           page=page,
                           total_pages=total_pages)


@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '')
    page = request.args.get('page', 1, type=int)  # Get the current page number from the request
    per_page = 5  # Set the number of posts per page

    conn = get_db_connection()

    # Retrieve total number of posts that match the search query
    total_posts_query = conn.execute('''
        SELECT COUNT(DISTINCT p.post_id)
        FROM post p
        JOIN user u ON p.user_id = u.user_id
        LEFT JOIN comment c ON p.post_id = c.post_id
        WHERE p.title LIKE ? OR p.description LIKE ? OR c.content LIKE ?
    ''', (f'%{query}%', f'%{query}%', f'%{query}%')).fetchone()
    
    total_posts = total_posts_query[0]
    total_pages = (total_posts + per_page - 1) // per_page  # Calculate total pages

    # Retrieve posts that match the search query for the current page
    posts = conn.execute('''
        SELECT DISTINCT p.post_id, p.title, p.description, p.created_at, u.username
        FROM post p
        JOIN user u ON p.user_id = u.user_id
        LEFT JOIN comment c ON p.post_id = c.post_id
        WHERE p.title LIKE ? OR p.description LIKE ? OR c.content LIKE ?
        LIMIT ? OFFSET ?
    ''', (f'%{query}%', f'%{query}%', f'%{query}%', per_page, (page - 1) * per_page)).fetchall()

    # Retrieve comments related to the posts found
    comments = conn.execute('''
        SELECT c.content, c.created_at, c.post_id, u.username
        FROM comment c
        JOIN user u ON c.user_id = u.user_id
        WHERE c.content LIKE ?
    ''', (f'%{query}%',)).fetchall()

    conn.close()

    return render_template('search_results.html', posts=posts, query=query, comments=comments, page=page, total_pages=total_pages)



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
    if not current_user.admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('home'))

    conn = get_db_connection()
    conn.execute('DELETE FROM model WHERE model_id = ?', (model_id,))
    conn.commit()
    conn.close()
    flash('Model deleted successfully!')
    return redirect(url_for('admin') + '#models')


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
        SELECT customization.customization_id, customization.customization_name, 
               brand.name AS brand_name, model.name AS model_name, 
               color.name AS color_name, wheel_set.name AS wheel_name, 
               customization.created_at
        FROM customization
        JOIN model ON customization.model_id = model.model_id
        JOIN brand ON model.brand_id = brand.brand_id
        JOIN color ON customization.color_id = color.color_id
        JOIN wheel_set ON customization.wheel_id = wheel_set.wheel_id
        WHERE customization.user_id = ?
    ''', (current_user.id,)).fetchall()
    

    return render_template('customize.html', brands=brands, colors=colors, 
                           wheels=wheels, models=models, customizations=customizations)

@app.route('/edit_post/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    conn = get_db_connection()
    post = conn.execute('SELECT * FROM post WHERE post_id = ? AND user_id = ?', (post_id, current_user.id)).fetchone()

    if not post:
        flash('Post not found or you do not have permission to edit this post.')
        return redirect(url_for('forum'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        customization_id = request.form.get('customization_id')

        if not title or not description:
            flash('Title and description are required fields!')
        else:
            conn.execute('''
                UPDATE post SET title = ?, description = ?, customization_id = ? WHERE post_id = ?
            ''', (title, description, customization_id, post_id))
            conn.commit()
            conn.close()
            flash('Post updated successfully.')
            return redirect(url_for('forum'))

    customizations = conn.execute('SELECT customization_id, customization_name FROM customization WHERE user_id = ?', (current_user.id,)).fetchall()
    conn.close()
    return render_template('editpost.html', post=post, customizations=customizations)

@app.route('/delete_post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    conn = get_db_connection()
    post = conn.execute('SELECT * FROM post WHERE post_id = ? AND user_id = ?', (post_id, current_user.id)).fetchone()

    if not post:
        flash('Post not found or you do not have permission to delete this post.')
        return redirect(url_for('forum'))

    conn.execute('DELETE FROM post WHERE post_id = ?', (post_id,))
    conn.commit()
    conn.close()
    flash('Post deleted successfully.')
    return redirect(url_for('forum'))


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
    flash('Vehicle type deleted successfully!')
    return redirect(url_for('admin') + '#vehicle_types')

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
    flash('Brand deleted successfully!')
    return redirect(url_for('admin') + '#brands')

    return redirect(url_for('brand_type'))

@app.route('/create_wheel_set', methods=['GET', 'POST'])
@login_required
def create_wheel_set():
    if not current_user.admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('admin'))
    
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        conn = get_db_connection()
        conn.execute('INSERT INTO wheel_set (name, description) VALUES (?, ?)', (name, description))
        conn.commit()
        conn.close()
        flash('Wheel set created successfully.')
        return redirect(url_for('admin') + '#wheel_sets')
    
    return render_template('create_wheel_set.html')

@app.route('/edit_wheel_set/<int:wheel_id>', methods=['GET', 'POST'])
@login_required
def edit_wheel_set(wheel_id):
    if not current_user.admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('admin'))
    
    conn = get_db_connection()
    wheel_set = conn.execute('SELECT * FROM wheel_set WHERE wheel_id = ?', (wheel_id,)).fetchone()
    
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        conn.execute('UPDATE wheel_set SET name = ?, description = ? WHERE wheel_id = ?', (name, description, wheel_id))
        conn.commit()
        conn.close()
        flash('Wheel set updated successfully.')
        return redirect(url_for('admin') + '#wheel_sets')
    
    conn.close()
    return render_template('edit_wheel_set.html', wheel_set=wheel_set)

@app.route('/delete_wheel_set/<int:wheel_id>', methods=['POST'])
@login_required
def delete_wheel_set(wheel_id):
    if not current_user.admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('admin'))
    
    conn = get_db_connection()
    conn.execute('DELETE FROM wheel_set WHERE wheel_id = ?', (wheel_id,))
    conn.commit()
    conn.close()
    flash('Wheel set deleted successfully.')
    return redirect(url_for('admin') + '#wheel_sets')

if __name__ == '__main__':
    app.run(debug=True)