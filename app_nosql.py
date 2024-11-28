from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
from bson.objectid import ObjectId
from bson import ObjectId
from datetime import datetime
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ILOVEINF2003'
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")  # Replace with your MongoDB URI
db = client['carcraft']

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
        # Check if user_id is a valid ObjectId
        if not ObjectId.is_valid(user_id):
            return None  # Or raise an exception if needed

        user_data = db['user'].find_one({'_id': ObjectId(user_id)})
        if user_data:
            return User(
                user_id=str(user_data['_id']),
                username=user_data['username'],
                email=user_data['email'],
                password_hash=user_data['password_hash'],
                admin=user_data.get('admin', False)
            )
        return None

    @staticmethod
    def get_by_username(username):
        user_data = db['user'].find_one({'username': username})
        if user_data:
            return User(
                user_id=str(user_data['_id']),
                username=user_data['username'],
                email=user_data['email'],
                password_hash=user_data['password_hash'],
                admin=user_data.get('admin', False)
            )
        return None

    @staticmethod
    def get_all_users():
        users_data = db['user'].find()
        users = []
        for user_data in users_data:
            users.append(User(
                user_id=str(user_data['_id']),
                username=user_data['username'],
                email=user_data['email'],
                password_hash=user_data['password_hash'],
                admin=user_data.get('admin', False)
            ))
        return users

    def save(self):
        user_dict = {
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash,
            'admin': self.admin
        }
        if self.id:
            db['user'].update_one({'_id': ObjectId(self.id)}, {'$set': user_dict})
        else:
            result = db['user'].insert_one(user_dict)
            self.id = str(result.inserted_id)

    def delete(self):
        db['user'].delete_one({'_id': ObjectId(self.id)})

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

        # Check if username or email already exists
        existing_user = db['user'].find_one({'$or': [{'username': username}, {'email': email}]})
        if existing_user:
            if existing_user['username'] == username:
                flash('Username already exists. Please choose a different username.')
            else:
                flash('Email already exists. Please use a different email address.')
            return render_template('create_user.html')

        user = User(None, username, email, None, admin)
        user.set_password(password)
        user.save()
        flash('User created successfully')
        return redirect(url_for('home'))
    return render_template('create_user.html')


@app.route('/customize', methods=['GET', 'POST'])
@login_required
def customize():
    if request.method == 'POST':
        if 'delete_id' in request.form:
            # Handle deletion
            delete_id = request.form['delete_id']
            db.customization.delete_one({'_id': ObjectId(delete_id)})
        else:
            # Get form data
            customization_id = request.form.get('customization_id')
            customization_name = request.form.get('customization_name')
            model_id = ObjectId(request.form['model_id'])
            color_id = ObjectId(request.form['color_id'])
            wheel_id = ObjectId(request.form['wheel_id'])

            if not customization_name:
                flash('Customization name is required!', 'error')
                return redirect(url_for('customize'))

            customization_data = {
                'customization_name': customization_name,
                'model_id': model_id,
                'color_id': color_id,
                'wheel_set_id': wheel_id  # Note: Changed from wheel_id to wheel_set_id to match your schema
            }

            if customization_id:
                # Update existing customization
                db.customization.update_one(
                    {'_id': ObjectId(customization_id)},
                    {'$set': customization_data}
                )
            else:
                # Insert new customization
                customization_data['user_id'] = ObjectId(current_user.id)
                db.customization.insert_one(customization_data)

    # Fetch available options for the form
    brands = list(db.brand.find({}, {'_id': 1, 'name': 1}))
    colors = list(db.color.find({}, {'_id': 1, 'name': 1}))
    wheels = list(db.wheel_set.find({}, {'_id': 1, 'name': 1}))

    # Fetch models for the first brand if exists
    models = []
    if brands:
        default_brand_id = brands[0]['_id']
        models = list(db.model.find({'brand_id': default_brand_id}, {'_id': 1, 'name': 1}))

    # Fetch current customizations for the logged-in user with aggregation pipeline
    pipeline = [
        {
            '$match': {
                'user_id': ObjectId(current_user.id)
            }
        },
        {
            '$lookup': {
                'from': 'model',
                'localField': 'model_id',
                'foreignField': '_id',
                'as': 'model'
            }
        },
        {
            '$unwind': '$model'
        },
        {
            '$lookup': {
                'from': 'brand',
                'localField': 'model.brand_id',
                'foreignField': '_id',
                'as': 'brand'
            }
        },
        {
            '$unwind': '$brand'
        },
        {
            '$lookup': {
                'from': 'color',
                'localField': 'color_id',
                'foreignField': '_id',
                'as': 'color'
            }
        },
        {
            '$unwind': '$color'
        },
        {
            '$lookup': {
                'from': 'wheel_set',
                'localField': 'wheel_set_id',
                'foreignField': '_id',
                'as': 'wheel_set'
            }
        },
        {
            '$unwind': '$wheel_set'
        },
        {
            '$project': {
                'customization_id': '$_id',
                'customization_name': 1,
                'brand_name': '$brand.name',
                'model_name': '$model.name',
                'color_name': '$color.name',
                'wheel_name': '$wheel_set.name',
                'created_at': 1
            }
        }
    ]

    customizations = list(db.customization.aggregate(pipeline))

    return render_template('customize.html',
                         brands=brands,
                         colors=colors,
                         wheels=wheels,
                         models=models,
                         customizations=customizations)

@app.route('/admin')
@login_required
def admin():
    if not current_user.admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('home'))

    users = User.get_all_users()
    vehicle_types = list(db['vehicle_types'].find())
    brands = list(db['brand'].find())
    models = list(db['model'].aggregate([
        {
            '$lookup': {
                'from': 'brands',
                'localField': 'brand_id',
                'foreignField': '_id',
                'as': 'brand'
            }
        },
        {
            '$lookup': {
                'from': 'vehicle_types',
                'localField': 'type_id',
                'foreignField': '_id',
                'as': 'vehicle_type'
            }
        },
        {
            '$unwind': '$brand'
        },
        {
            '$unwind': '$vehicle_type'
        },
        {
            '$project': {
                'model_id': '$_id',
                'model_name': '$name',
                'brand_name': '$brand.name',
                'type_name': '$vehicle_type.name'
            }
        }
    ]))
    colors = list(db['color'].find())
    wheel_sets = list(db['wheel_set'].find())

    return render_template('admin.html', users=users, vehicle_types=vehicle_types,
                           brands=brands, models=models, colors=colors, wheel_sets=wheel_sets)

@app.route('/admin/update_user/<string:user_id>', methods=['GET', 'POST'])
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
        username = request.form.get('username')
        email = request.form.get('email')
        admin = request.form.get('admin') == 'on'

        # Check if username or email already exists for other users
        existing_user = db['user'].find_one({
            '$and': [
                {'$or': [{'username': username}, {'email': email}]},
                {'_id': {'$ne': ObjectId(user_id)}}
            ]
        })
        if existing_user:
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
        flash('User updated successfully')
        return redirect(url_for('admin'))

    return render_template('update_user.html', user=user)

@app.route('/admin/delete_user/<string:user_id>', methods=['POST'])
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

@app.route('/profile')
@login_required
def profile():
    user = current_user

    # Fetch the user's posts
    posts = list(db['post'].find({'user_id': ObjectId(user.id)}))

    # Fetch the user's customizations
    customizations = list(db['customization'].aggregate([
        {'$match': {'user_id': ObjectId(user.id)}},
        {'$lookup': {
            'from': 'models',
            'localField': 'model_id',
            'foreignField': '_id',
            'as': 'model'
        }},
        {'$unwind': '$model'},
        {'$lookup': {
            'from': 'brands',
            'localField': 'model.brand_id',
            'foreignField': '_id',
            'as': 'brand'
        }},
        {'$unwind': '$brand'},
        {'$lookup': {
            'from': 'colors',
            'localField': 'color_id',
            'foreignField': '_id',
            'as': 'color'
        }},
        {'$unwind': '$color'},
        {'$lookup': {
            'from': 'wheel_sets',
            'localField': 'wheel_set_id',
            'foreignField': '_id',
            'as': 'wheel_set'
        }},
        {'$unwind': '$wheel_set'},
        {'$project': {
            'customization_id': '$_id',
            'customization_name': 1,
            'brand_name': '$brand.name',
            'model_name': '$model.name',
            'color_name': '$color.name',
            'wheel_name': '$wheel_set.name'
        }}
    ]))

    return render_template('user_profile.html', user=user, posts=posts, customizations=customizations)

@app.route('/post/<string:post_id>', methods=['GET'])
def view_post(post_id):
    post = db['post'].aggregate([
        {'$match': {'_id': ObjectId(post_id)}},
        {'$lookup': {
            'from': 'users',
            'localField': 'user_id',
            'foreignField': '_id',
            'as': 'user'
        }},
        {'$unwind': '$user'},
        {'$lookup': {
            'from': 'customizations',
            'localField': 'customization_id',
            'foreignField': '_id',
            'as': 'customization'
        }},
        {'$unwind': {'path': '$customization', 'preserveNullAndEmptyArrays': True}},
        {'$project': {
            'post_id': '$_id',
            'title': 1,
            'description': 1,
            'created_at': 1,
            'user_id': 1,
            'username': '$user.username',
            'customization_name': '$customization.customization_name',
            'customization_id': '$customization._id'
        }}
    ]).next()

    if not post:
        flash('Post not found.')
        return redirect(url_for('forum'))

    comments = list(db['comment'].aggregate([
        {'$match': {'post_id': ObjectId(post_id)}},
        {'$lookup': {
            'from': 'users',
            'localField': 'user_id',
            'foreignField': '_id',
            'as': 'user'
        }},
        {'$unwind': '$user'},
        {'$sort': {'created_at': -1}},
        {'$project': {
            'comment_id': '$_id',
            'content': 1,
            'created_at': 1,
            'user_id': 1,
            'username': '$user.username'
        }}
    ]))

    customization_data = None
    if post.get('customization_id'):
        customization_data = db['customizations'].aggregate([
            {'$match': {'_id': post['customization_id']}},
            {'$lookup': {
                'from': 'models',
                'localField': 'model_id',
                'foreignField': '_id',
                'as': 'model'
            }},
            {'$unwind': '$model'},
            {'$lookup': {
                'from': 'brands',
                'localField': 'model.brand_id',
                'foreignField': '_id',
                'as': 'brand'
            }},
            {'$unwind': '$brand'},
            {'$lookup': {
                'from': 'colors',
                'localField': 'color_id',
                'foreignField': '_id',
                'as': 'color'
            }},
            {'$unwind': '$color'},
            {'$lookup': {
                'from': 'wheel_sets',
                'localField': 'wheel_set_id',
                'foreignField': '_id',
                'as': 'wheel_set'
            }},
            {'$unwind': '$wheel_set'},
            {'$project': {
                'brand_name': '$brand.name',
                'model_name': '$model.name',
                'color_name': '$color.name',
                'wheel_name': '$wheel_set.name'
            }}
        ]).next()

    return render_template('view_post.html', post=post, comments=comments, customization_data=customization_data)

@app.route('/createpost', methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        customization_id = request.form.get('customization_id')
        category = request.form['category']

        if not title or not description:
            flash('Title and Description are required fields!')
            return redirect(url_for('create_post'))

        if category == 'customization showcase' and not customization_id:
            flash('Customization is required for the Customization Showcase category!')
            return redirect(url_for('create_post'))

        if customization_id == "" or customization_id is None:
            customization_id = None
        else:
            customization_id = ObjectId(customization_id)

        post = {
            'title': title,
            'description': description,
            'user_id': ObjectId(current_user.id),
            'customization_id': customization_id,
            'category': category,
            'created_at': datetime.utcnow()
        }
        db['posts'].insert_one(post)

        flash('Post created successfully!')
        return redirect(url_for('forum'))

    # Fetch customizations for the current user
    customizations = list(db['customizations'].find(
        {'user_id': ObjectId(current_user.id)},
        {'_id': 1, 'customization_name': 1}
    ))

    return render_template('createpost.html', customizations=customizations)

@app.route('/forum/category/<string:category_name>', methods=['GET'])
def posts_by_category(category_name):
    posts = list(db['post'].aggregate([
        {'$match': {'category': category_name}},
        {'$lookup': {
            'from': 'users',
            'localField': 'user_id',
            'foreignField': '_id',
            'as': 'user'
        }},
        {'$unwind': '$user'},
        {'$lookup': {
            'from': 'customizations',
            'localField': 'customization_id',
            'foreignField': '_id',
            'as': 'customization'
        }},
        {'$unwind': {'path': '$customization', 'preserveNullAndEmptyArrays': True}},
        {'$sort': {'created_at': -1}},
        {'$project': {
            'post_id': '$_id',
            'title': 1,
            'description': 1,
            'created_at': 1,
            'user_id': 1,
            'username': '$user.username',
            'customization_name': '$customization.customization_name',
            'customization_id': '$customization._id'
        }}
    ]))

    posts_with_customization = []
    for post in posts:
        customization_data = None
        if post.get('customization_id'):
            customization_data = db['customization'].aggregate([
                {'$match': {'_id': post['customization_id']}},
                {'$lookup': {
                    'from': 'models',
                    'localField': 'model_id',
                    'foreignField': '_id',
                    'as': 'model'
                }},
                {'$unwind': '$model'},
                {'$lookup': {
                    'from': 'brands',
                    'localField': 'model.brand_id',
                    'foreignField': '_id',
                    'as': 'brand'
                }},
                {'$unwind': '$brand'},
                {'$lookup': {
                    'from': 'colors',
                    'localField': 'color_id',
                    'foreignField': '_id',
                    'as': 'color'
                }},
                {'$unwind': '$color'},
                {'$lookup': {
                    'from': 'wheel_sets',
                    'localField': 'wheel_set_id',
                    'foreignField': '_id',
                    'as': 'wheel_set'
                }},
                {'$unwind': '$wheel_set'},
                {'$project': {
                    'brand_name': '$brand.name',
                    'model_name': '$model.name',
                    'color_name': '$color.name',
                    'wheel_name': '$wheel_set.name'
                }}
            ]).next()

        posts_with_customization.append({
            'post': post,
            'customization_data': customization_data
        })

    return render_template('category_posts.html',
                           posts=posts_with_customization,
                           category_name=category_name)

@app.route('/create_comment/<string:post_id>', methods=['POST'])
@login_required
def create_comment(post_id):
    content = request.form['content']
    user_id = ObjectId(current_user.id)

    if not content:
        flash('Comment cannot be empty.')
        return redirect(url_for('view_post', post_id=post_id))

    comment = {
        'content': content,
        'user_id': user_id,
        'post_id': ObjectId(post_id),
        'created_at': datetime.utcnow()
    }
    db['comment'].insert_one(comment)

    flash('Comment added successfully!')
    return redirect(url_for('view_post', post_id=post_id))

@app.route('/edit_comment/<string:comment_id>', methods=['GET', 'POST'])
@login_required
def edit_comment(comment_id):
    comment = db['comment'].find_one({'_id': ObjectId(comment_id)})
    if not comment:
        flash('Comment not found')
        return redirect(url_for('forum'))

    if current_user.id != str(comment['user_id']) and not current_user.admin:
        flash('Access denied.')
        return redirect(url_for('forum'))

    if request.method == 'POST':
        new_content = request.form['content']
        if not new_content:
            flash('Comment cannot be empty.')
        else:
            db['comment'].update_one(
                {'_id': ObjectId(comment_id)},
                {'$set': {'content': new_content}}
            )
            flash('Comment updated successfully.')
        return redirect(url_for('forum'))

    return render_template('edit_comment.html', comment=comment)

@app.route('/delete_comment/<string:comment_id>', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = db['comment'].find_one({'_id': ObjectId(comment_id)})
    if not comment:
        flash('Comment not found')
        return redirect(url_for('forum'))

    if current_user.id != str(comment['user_id']) and not current_user.admin:
        flash('Access denied.')
        return redirect(url_for('forum'))

    db['comment'].delete_one({'_id': ObjectId(comment_id)})
    flash('Comment deleted successfully.')
    return redirect(url_for('forum'))

@app.route('/forum')
def forum():
    # Get filter parameters from request args
    selected_brand_id = request.args.get('brand')
    selected_color_id = request.args.get('color')
    selected_wheel_id = request.args.get('wheel')

    # Pagination settings
    page = request.args.get('page', 1, type=int)
    per_page = 5
    skip = (page - 1) * per_page

    # Build the query
    query = {}
    if selected_brand_id:
        selected_brand_id = ObjectId(selected_brand_id)
        query['customization_id'] = {'$in': list(db['customization'].find(
            {'model_id': {'$in': list(db['models'].find({'brand_id': selected_brand_id}, {'_id': 1}))}},
            {'_id': 1}
        ))}
    if selected_color_id:
        query['customization_id'] = {'$in': list(db['customization'].find(
            {'color_id': ObjectId(selected_color_id)},
            {'_id': 1}
        ))}
    if selected_wheel_id:
        query['customization_id'] = {'$in': list(db['customization'].find(
            {'wheel_set_id': ObjectId(selected_wheel_id)},
            {'_id': 1}
        ))}

    start_time = time.time()

    posts = list(db['posts'].aggregate([
        {'$match': query},
        {'$lookup': {
            'from': 'users',
            'localField': 'user_id',
            'foreignField': '_id',
            'as': 'user'
        }},
        {'$unwind': '$user'},
        {'$lookup': {
            'from': 'customizations',
            'localField': 'customization_id',
            'foreignField': '_id',
            'as': 'customization'
        }},
        {'$unwind': {'path': '$customization', 'preserveNullAndEmptyArrays': True}},
        {'$sort': {'created_at': -1}},
        {'$skip': skip},
        {'$limit': per_page},
        {'$project': {
            'post_id': '$_id',
            'title': 1,
            'description': 1,
            'created_at': 1,
            'user_id': 1,
            'username': '$user.username',
            'customization_name': '$customization.customization_name',
            'customization_id': '$customization._id',
            'category': 1
        }}
    ]))

    posts_with_comments = []
    for post in posts:
        comments = list(db['comment'].aggregate([
            {'$match': {'post_id': post['post_id']}},
            {'$lookup': {
                'from': 'users',
                'localField': 'user_id',
                'foreignField': '_id',
                'as': 'user'
            }},
            {'$unwind': '$user'},
            {'$sort': {'created_at': -1}},
            {'$project': {
                'comment_id': '$_id',
                'content': 1,
                'created_at': 1,
                'user_id': 1,
                'username': '$user.username'
            }}
        ]))

        customization_data = None
        if post.get('customization_id'):
            customization_data = db['customization'].aggregate([
                {'$match': {'_id': post['customization_id']}},
                {'$lookup': {
                    'from': 'models',
                    'localField': 'model_id',
                    'foreignField': '_id',
                    'as': 'model'
                }},
                {'$unwind': '$model'},
                {'$lookup': {
                    'from': 'brands',
                    'localField': 'model.brand_id',
                    'foreignField': '_id',
                    'as': 'brand'
                }},
                {'$unwind': '$brand'},
                {'$lookup': {
                    'from': 'colors',
                    'localField': 'color_id',
                    'foreignField': '_id',
                    'as': 'color'
                }},
                {'$unwind': '$color'},
                {'$lookup': {
                    'from': 'wheel_sets',
                    'localField': 'wheel_set_id',
                    'foreignField': '_id',
                    'as': 'wheel_set'
                }},
                {'$unwind': '$wheel_set'},
                {'$project': {
                    'brand_name': '$brand.name',
                    'model_name': '$model.name',
                    'color_name': '$color.name',
                    'wheel_name': '$wheel_set.name'
                }}
            ]).next()

        posts_with_comments.append({
            'post': post,
            'comments': comments,
            'customization_data': customization_data
        })

    total_posts = db['post'].count_documents(query)
    total_pages = (total_posts + per_page - 1) // per_page

    customizations = []
    if current_user.is_authenticated:
        customizations = list(db['customization'].find(
            {'user_id': ObjectId(current_user.id)},
            {'_id': 1, 'customization_name': 1}
        ))

    brands = list(db['brand'].find())
    colors = list(db['color'].find())
    wheels = list(db['wheel_set'].find())

    end_time = time.time()
    elapsed_time = f"{end_time - start_time:0.6f}"

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
                           total_pages=total_pages,
                           elapsed_time=elapsed_time)

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '')
    page = request.args.get('page', 1, type=int)
    per_page = 5
    skip = (page - 1) * per_page

    start_time = time.time()

    regex_query = {'$regex': query, '$options': 'i'}

    total_posts = db['post'].count_documents({
        '$or': [
            {'title': regex_query},
            {'description': regex_query},
            {'comments.content': regex_query}
        ]
    })

    posts = list(db['post'].aggregate([
        {'$match': {
            '$or': [
                {'title': regex_query},
                {'description': regex_query}
            ]
        }},
        {'$lookup': {
            'from': 'comments',
            'localField': '_id',
            'foreignField': 'post_id',
            'as': 'comments'
        }},
        {'$lookup': {
            'from': 'users',
            'localField': 'user_id',
            'foreignField': '_id',
            'as': 'user'
        }},
        {'$unwind': '$user'},
        {'$skip': skip},
        {'$limit': per_page}
    ]))

    comments = list(db['comment'].aggregate([
        {'$match': {'content': regex_query}},
        {'$lookup': {
            'from': 'users',
            'localField': 'user_id',
            'foreignField': '_id',
            'as': 'user'
        }},
        {'$unwind': '$user'}
    ]))

    end_time = time.time()
    search_time = f"{end_time - start_time:0.6f}"

    return render_template('search_results.html', posts=posts, query=query,
                           comments=comments, page=page, total_pages=(total_posts + per_page - 1) // per_page,
                           search_time=search_time)

# Add more routes below as needed, converting SQLite operations to MongoDB operations

if __name__ == '__main__':
    app.run(debug=True)
