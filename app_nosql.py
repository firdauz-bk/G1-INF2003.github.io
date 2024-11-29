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

@app.route('/edit_customization/<customization_id>', methods=['GET', 'POST'])
@login_required
def edit_customization(customization_id):
    
    # Create aggregation pipeline to fetch customization with related model info
    pipeline = [
        {
            '$match': {
                '_id': ObjectId(customization_id)
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
            '$project': {
                'customization_id': '$_id',
                'customization_name': 1,
                'model_id': 1,
                'color_id': 1,
                'wheel_set_id': 1,  # Note: Changed from wheel_id to match your schema
                'brand_id': '$model.brand_id'
            }
        }
    ]
    
    customization = list(db.customization.aggregate(pipeline))
    if not customization:
        return "Customization not found", 404
        
    customization = customization[0]  # Get the first (and should be only) result

    if request.method == 'POST':
        # Update the customization
        update_data = {
            'customization_name': request.form['customization_name'],
            'model_id': ObjectId(request.form['model_id']),
            'color_id': ObjectId(request.form['color_id']),
            'wheel_set_id': ObjectId(request.form['wheel_id'])  # Note: Form still uses wheel_id
        }
        
        db.customization.update_one(
            {'_id': ObjectId(customization_id)},
            {'$set': update_data}
        )
        
        return redirect(url_for('customize'))

    # Fetch available options for the form
    brands = list(db.brand.find({}, {'_id': 1, 'name': 1}))
    colors = list(db.color.find({}, {'_id': 1, 'name': 1}))
    wheels = list(db.wheel_set.find({}, {'_id': 1, 'name': 1}))
    
    # Fetch models based on the current model's brand_id
    models = list(db.model.find(
        {'brand_id': customization['brand_id']}, 
        {'_id': 1, 'name': 1}
    ))

    return render_template(
        'edit_customization.html',
        customization=customization,
        brands=brands,
        colors=colors,
        wheels=wheels,
        models=models
    )

@app.route('/delete_post/<post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    # Get MongoDB connectio
    try:
        # Convert string ID to MongoDB ObjectId
        post_object_id = ObjectId(post_id)
        
        # Fetch the post to verify ownership or admin rights
        post = db.post.find_one({"_id": post_object_id})
        
        # If the post does not exist, flash an error
        if post is None:
            flash('Post not found.', 'danger')
            return redirect(url_for('forum'))
            
        # Check if user has permission (is owner or admin)
        if current_user.id != post['user_id'] and not current_user.admin:
            flash('You do not have permission to delete this post.', 'danger')
            return redirect(url_for('forum'))
            
        # If the user is authorized, delete the post and its associated comments
        # First delete all comments associated with the post
        db.comment.delete_many({"post_id": post_object_id})
        
        # Then delete the post itself
        db.post.delete_one({"_id": post_object_id})
        
        flash('Post has been deleted successfully.', 'success')
        return redirect(url_for('forum'))
        
    except Exception as e:
        flash(f'An error occurred while deleting the post: {str(e)}', 'danger')
        return redirect(url_for('forum'))

@app.route('/admin')
@login_required
def admin():
    if not current_user.admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('home'))
    # Fetch all collections
    users = User.get_all_users()
    vehicle_types = list(db.vehicle_type.find())
    brands = list(db.brand.find())
    
    # For models, we need to use aggregation pipeline to join collections
    models = list(db.model.aggregate([
        {
            '$lookup': {
                'from': 'brand',
                'localField': 'brand_id',
                'foreignField': '_id',
                'as': 'brand'
            }
        },
        {
            '$lookup': {
                'from': 'vehicle_type',
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
        },
        
        {
            '$sort': {'model_name': 1}
        }
    ]))
    
    colors = list(db.color.find())
    wheel_sets = list(db.wheel_set.find())
    
    return render_template('admin.html', users=users, vehicle_types=vehicle_types,
                         brands=brands, models=models, colors=colors, wheel_sets=wheel_sets)

@app.route('/create_color', methods=["GET", "POST"])
@login_required
def create_color():
    if not current_user.admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('home'))

    if request.method == "POST":
        name = request.form.get('name', '').strip()
        if not name:
            flash("Color name cannot be empty!")
            return redirect(url_for('create_color'))

        try:
            # Insert into the `color` collection
            db.color.insert_one({"name": name})
            flash("Color created successfully!")
        except Exception as e:
            flash(f"Error creating color: {str(e)}")

        return redirect(url_for('admin') + "#colors")

    return render_template("create_color.html")


@app.route('/edit_color/<color_id>', methods=["GET", "POST"])
@login_required
def edit_color(color_id):
    if not current_user.admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('home'))

    try:
        # Retrieve the color document for GET requests
        color = db.color.find_one({"_id": ObjectId(color_id)})
        if not color:
            flash("Color not found!")
            return redirect(url_for('admin') + "#colors")

        if request.method == "POST":
            name = request.form.get('name', '').strip()
            if not name:
                flash("Color name cannot be empty!")
                return redirect(url_for('edit_color', color_id=color_id))

            # Update the color in the database
            db.color.update_one(
                {"_id": ObjectId(color_id)},
                {"$set": {"name": name}}
            )
            flash("Color updated successfully!")
            return redirect(url_for('admin') + "#colors")

        # Pass color data to the template
        color["_id"] = str(color["_id"])  # Convert ObjectId to string for Jinja2
    except Exception as e:
        flash(f"Error updating color: {str(e)}")
        return redirect(url_for('admin') + "#colors")

    return render_template("edit_color.html", color=color)


@app.route('/delete_color', methods=["POST"])
@login_required
def delete_color():
    if not current_user.admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('home'))

    color_id = request.form.get('color_id')
    if not color_id:
        flash("Color ID not provided!")
        return redirect(url_for('admin') + "#colors")

    try:
        result = db.color.delete_one({"_id": ObjectId(color_id)})
        if result.deleted_count > 0:
            flash("Color deleted successfully!")
        else:
            flash("Color not found!")
    except Exception as e:
        flash(f"Error deleting color: {str(e)}")

    return redirect(url_for('admin') + "#colors")


@app.route('/brand_type', methods=["GET", "POST"])
@login_required
def brand_type():
    if not current_user.admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash("Brand name cannot be empty!")
            return redirect(url_for('brand_type'))

        # Check if the brand already exists
        existing_brand = db.brand.find_one({"name": name})
        if existing_brand:
            flash("Brand already exists!")
            return redirect(url_for('brand_type'))

        # Add the new brand
        try:
            db.brand.insert_one({"name": name})
            flash("Brand added successfully!")
        except Exception as e:
            flash(f"Error adding brand: {str(e)}")

        return redirect(url_for('brand_type'))
    
    # Fetch all brands and convert `_id` to string for Jinja2
    try:
        brands = [{"_id": str(brand["_id"]), "name": brand["name"]} for brand in db.brand.find()]
    except Exception as e:
        flash(f"Error retrieving brands: {str(e)}")
        brands = []

    return render_template('brand_type.html', brands=brands)


@app.route('/brand_type/edit/<brand_id>', methods=["GET", 'POST'])
@login_required
def brand_type_edit(brand_id):
    if not current_user.admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('home'))
    if request.method == 'POST':
        name = request.form['name']
        # Check if the name already exists for a different brand
        existing_brand = db.brand.find_one({
            "name": name,
            "_id": {"$ne": ObjectId(brand_id)}
        })
        
        if existing_brand:
            flash("Name already exists!")
            return redirect(url_for('brand_type'))
            
        try:
            # Update the brand
            result = db.brand.update_one(
                {"_id": ObjectId(brand_id)},
                {"$set": {"name": name}}
            )
            
            if result.modified_count > 0:
                flash("Brand updated successfully!")
            else:
                flash("No changes made to brand.")
        except Exception as e:
            flash(f"Error updating brand: {str(e)}")
            
    return redirect(url_for('brand_type'))

@app.route('/brand_type/delete/<brand_id>', methods=["GET", 'POST'])
@login_required
def brand_type_delete(brand_id):
    if not current_user.admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('home'))
    try:
        # Check if this brand is referenced by any models
        model_count = db.model.count_documents({"brand_id": ObjectId(brand_id)})
        if model_count > 0:
            flash('Cannot delete brand: it is being used by existing models!')
            return redirect(url_for('admin') + '#brands')
        
        # Delete the brand
        result = db.brand.delete_one({"_id": ObjectId(brand_id)})
        if result.deleted_count > 0:
            flash('Brand deleted successfully!')
        else:
            flash('Brand not found!')
    except Exception as e:
        flash(f"Error deleting brand: {str(e)}")
        
    return redirect(url_for('admin') + '#brands')

@app.route('/vehicle_type', methods=["GET", 'POST'])
@login_required
def vehicle_type():
    if not current_user.admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('home'))
    if request.method == 'POST':
        name = request.form['name']
        # Check if the name already exists in the collection
        existing_type = db.vehicle_type.find_one({"name": name})
        if existing_type:
            flash("Name already exists!")
            return redirect(url_for('vehicle_type'))
            
        # If not, insert the new vehicle type
        try:
            db.vehicle_type.insert_one({"name": name})
            flash("Vehicle type added successfully!")
        except Exception as e:
            flash(f"Error adding vehicle type: {str(e)}")
        return redirect(url_for('vehicle_type'))
    
    # Retrieve all vehicle types
    try:
        vehicle_types = list(db.vehicle_type.find())
        # Convert ObjectId to string for template rendering
        for vtype in vehicle_types:
            vtype['_id'] = str(vtype['_id'])
    except Exception as e:
        flash(f"Error retrieving vehicle types: {str(e)}")
        vehicle_types = []
        
    return render_template('vehicle_type.html', vehicle_types=vehicle_types)

@app.route('/vehicle_type/edit/<type_id>', methods=["GET", 'POST'])
@login_required
def vehicle_type_edit(type_id):
    if not current_user.admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        name = request.form['name']
        # Check if the name already exists for a different vehicle type
        existing_type = db.vehicle_type.find_one({
            "name": name,
            "_id": {"$ne": ObjectId(type_id)}
        })
        
        if existing_type:
            flash("Name already exists!")
            return redirect(url_for('vehicle_type'))
            
        try:
            # Update the vehicle type
            result = db.vehicle_type.update_one(
                {"_id": ObjectId(type_id)},
                {"$set": {"name": name}}
            )
            
            if result.modified_count > 0:
                flash("Vehicle type updated successfully!")
            else:
                flash("No changes made to vehicle type.")
        except Exception as e:
            flash(f"Error updating vehicle type: {str(e)}")
            
    return redirect(url_for('vehicle_type'))

from flask import request

@app.route('/vehicle_type/delete', methods=["POST"])
@login_required
def vehicle_type_delete():
    if not current_user.admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('home'))

    type_id = request.form.get('type_id')
    if not type_id:
        flash("Vehicle Type ID not provided!")
        return redirect(url_for('vehicle_type'))

    try:
        object_type_id = ObjectId(type_id)

        # Check for references in models
        model_count = db.model.count_documents({"type_id": object_type_id})
        if model_count > 0:
            flash('Cannot delete vehicle type: it is referenced by existing models!')
            return redirect(url_for('vehicle_type'))

        # Delete the vehicle type
        result = db.vehicle_type.delete_one({"_id": object_type_id})
        if result.deleted_count > 0:
            flash('Vehicle type deleted successfully!')
        else:
            flash('Vehicle type not found!')

    except Exception as e:
        flash(f"Error deleting vehicle type: {str(e)}")

    # Check if the request originated from the admin page or another page
    referrer = request.referrer or url_for('admin')
    if 'admin' in referrer:
        return redirect(url_for('admin') + '#vehicle_types')
    else:
        return redirect(url_for('vehicle_type'))



@app.route('/admin/update_user/<user_id>', methods=['GET', 'POST'])
@login_required
def update_user(user_id):
    if not current_user.admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('home'))
    try:
        user = User.get(user_id)  # Assuming User.get() works with MongoDB
        if not user:
            flash('User not found')
            return redirect(url_for('admin'))
        
        if request.method == 'POST':
            username = request.form.get('username')
            email = request.form.get('email')
            admin = request.form.get('admin') == 'on'
            
            # Check if username or email already exists for other users
            existing_user = db.user.find_one({
                '$and': [
                    {'$or': [{'username': username}, {'email': email}]},
                    {'_id': {'$ne': ObjectId(user_id)}}
                ]
            })
            
            if existing_user:
                if existing_user.get('username') == username:
                    flash('Username already exists. Please choose a different username.')
                else:
                    flash('Email already exists. Please use a different email address.')
                return render_template('update_user.html', user=user)
            
            # Update user data
            update_data = {
                'username': username,
                'email': email,
                'admin': admin
            }
            
            # If password is provided, update it
            if request.form.get('password'):
                user.set_password(request.form.get('password'))
                update_data['password_hash'] = user.password_hash
            
            db.user.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': update_data}
            )
            
            flash('User updated successfully')
            return redirect(url_for('admin'))
        
        return render_template('update_user.html', user=user)
        
    except Exception as e:
        flash(f'An error occurred: {str(e)}')
        return redirect(url_for('admin'))

@app.route('/admin/delete_user/<user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('home'))
    try:
        # Delete user's posts and comments first
        user_object_id = ObjectId(user_id)
        
        # Delete all comments by the user
        db.comment.delete_many({'user_id': user_object_id})
        
        # Get all posts by the user
        user_posts = db.post.find({'user_id': user_object_id})
        for post in user_posts:
            # Delete comments on each post
            db.comment.delete_many({'post_id': post['_id']})
        
        # Delete all posts by the user
        db.post.delete_many({'user_id': user_object_id})
        
        # Delete all customizations by the user
        db.customization.delete_many({'user_id': user_object_id})
        
        # Finally delete the user
        result = db.user.delete_one({'_id': user_object_id})
        
        if result.deleted_count > 0:
            flash('User deleted successfully')
        else:
            flash('User not found')
            
    except Exception as e:
        flash(f'An error occurred while deleting the user: {str(e)}')
        
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

@app.route('/edit_post/<post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    
    # Find the post by ID
    try:
        post = db.post.find_one({'_id': ObjectId(post_id)})
    except:
        flash('Post not found.', 'danger')
        return redirect(url_for('forum'))
        
    # Check if the post exists and the current user has the right permissions
    if not post:
        flash('Post not found.', 'danger')
        return redirect(url_for('forum'))
        
    # Convert ObjectId to string for comparison with current_user.id
    post_user_id = str(post['user_id'])
    if post_user_id != current_user.id and not current_user.admin:
        flash('You do not have permission to edit this post.', 'danger')
        return redirect(url_for('forum'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        customization_id = request.form.get('customization_id')

        if customization_id:
            try:
                update_data['customization_id'] = ObjectId(customization_id)
            except:
                flash('Invalid customization selected.', 'danger')
                return redirect(url_for('edit_post', post_id=post_id))

        else:
            # Update the post
            update_data = {
                'title': title,
                'description': description
            }
            
            # Only include customization_id if it was provided
            if customization_id:
                update_data['customization_id'] = ObjectId(customization_id)
            
            db.post.update_one(
                {'_id': ObjectId(post_id)},
                {'$set': update_data}
            )
            
            flash('Post updated successfully.', 'success')
            return redirect(url_for('forum'))

    # Fetch customizations for the current user
    customizations = list(db.customization.find(
        {'user_id': ObjectId(current_user.id)},
        {'_id': 1, 'customization_name': 1}
    ))
    
    return render_template('editpost.html', 
                         post=post, 
                         customizations=customizations)

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

@app.route('/model/create', methods=["GET", "POST"])
@login_required
def create_model():
    if not current_user.admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('home'))

    if request.method == "POST":
        model_name = request.form.get('model_name', '').strip()
        brand_id = request.form.get('brand_id')
        type_id = request.form.get('type_id')

        if not model_name or not brand_id or not type_id:
            flash("All fields are required!")
            return redirect(url_for('create_model'))

        try:
            # Convert type_id and brand_id to ObjectId
            object_brand_id = ObjectId(brand_id)
            object_type_id = ObjectId(type_id)

            # Insert the model into the database
            db.model.insert_one({
                "model_name": model_name,
                "brand_id": object_brand_id,
                "type_id": object_type_id
            })

            flash("Model created successfully!")
            return redirect(url_for('admin') + "#models")

        except Exception as e:
            flash(f"Error creating model: {str(e)}")
            return redirect(url_for('create_model'))

    # Fetch brands and vehicle types for the form
    try:
        brands = [{"_id": str(brand["_id"]), "name": brand["name"]} for brand in db.brand.find()]
        vehicle_types = [{"_id": str(vt["_id"]), "name": vt["name"]} for vt in db.vehicle_type.find()]
    except Exception as e:
        flash(f"Error retrieving data: {str(e)}")
        brands = []
        vehicle_types = []

    return render_template('model.html', brands=brands, vehicle_types=vehicle_types)


@app.route('/edit_model/<model_id>', methods=["GET", "POST"])
@login_required
def edit_model(model_id):
    if not current_user.admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('home'))

    try:
        # Fetch the model details from the database
        model = db.model.find_one({"_id": ObjectId(model_id)})
        if not model:
            flash("Model not found!")
            return redirect(url_for('admin') + "#models")

        # Fetch brands and vehicle types for dropdowns
        brands = [{"_id": str(brand["_id"]), "name": brand["name"]} for brand in db.brand.find()]
        vehicle_types = [{"_id": str(vt["_id"]), "name": vt["name"]} for vt in db.vehicle_type.find()]

        if request.method == "POST":
            model_name = request.form.get('model_name', '').strip()
            brand_id = request.form.get('brand_id')
            type_id = request.form.get('type_id')

            if not model_name or not brand_id or not type_id:
                flash("All fields are required!")
                return redirect(url_for('edit_model', model_id=model_id))

            # Update the model in the database
            db.model.update_one(
                {"_id": ObjectId(model_id)},
                {"$set": {
                    "model_name": model_name,
                    "brand_id": ObjectId(brand_id),
                    "type_id": ObjectId(type_id)
                }}
            )
            flash("Model updated successfully!")
            return redirect(url_for('admin') + "#models")

        # Convert ObjectId fields for the template
        model["_id"] = str(model["_id"])
        model["brand_id"] = str(model["brand_id"])
        model["type_id"] = str(model["type_id"])

    except Exception as e:
        flash(f"Error loading model: {str(e)}")
        return redirect(url_for('admin') + "#models")

    return render_template(
        'edit_model.html',
        model=model,
        brands=brands,
        vehicle_types=vehicle_types
    )

@app.route('/delete_model/<string:model_id>', methods=['POST'])
@login_required
def delete_model(model_id):
    if not current_user.admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('home'))

    # Delete the model from MongoDB
    db['model'].delete_one({'_id': ObjectId(model_id)})
    flash('Model deleted successfully!')
    return redirect(url_for('admin') + '#models')

@app.route('/get_models/<string:brand_id>', methods=['GET'])
def get_models(brand_id):
    try:
        # Fetch models for the selected brand from MongoDB
        models = list(db['model'].find(
            {'brand_id': ObjectId(brand_id)},  # Match brand_id with ObjectId
            {'_id': 1, 'name': 1}  # Project only _id and name fields
        ))

        # Transform the models into a JSON-serializable format
        models_response = [{'model_id': str(model['_id']), 'name': model['name']} for model in models]

        # Debugging information
        print(f"Fetched models for brand_id {brand_id}: {models_response}")

        return jsonify(models_response)

    except Exception as e:
        # Log the error for debugging
        print(f"Error fetching models for brand_id {brand_id}: {e}")
        return jsonify({'error': 'Failed to fetch models'}), 500

@app.route('/create_wheel_set', methods=["GET", "POST"])
@login_required
def create_wheel_set():
    if not current_user.admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('home'))

    if request.method == "POST":
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()

        if not name:
            flash("Wheel set name cannot be empty!")
            return redirect(url_for('create_wheel_set'))

        try:
            db.wheel_set.insert_one({"name": name, "description": description})
            flash("Wheel set created successfully!")
        except Exception as e:
            flash(f"Error creating wheel set: {str(e)}")

        return redirect(url_for('admin') + "#wheel_sets")

    return render_template("create_wheel_set.html")


@app.route('/edit_wheel_set/<wheel_id>', methods=["GET", "POST"])
@login_required
def edit_wheel_set(wheel_id):
    if not current_user.admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('home'))

    try:
        # Retrieve the wheel set for GET requests
        wheel_set = db.wheel_set.find_one({"_id": ObjectId(wheel_id)})
        if not wheel_set:
            flash("Wheel set not found!")
            return redirect(url_for('admin') + "#wheel_sets")

        if request.method == "POST":
            # Get updated values from the form
            name = request.form.get('name', '').strip()
            description = request.form.get('description', '').strip()

            if not name:
                flash("Wheel set name cannot be empty!")
                return redirect(url_for('edit_wheel_set', wheel_id=wheel_id))

            # Update the wheel set in the database
            db.wheel_set.update_one(
                {"_id": ObjectId(wheel_id)},
                {"$set": {"name": name, "description": description}}
            )
            flash("Wheel set updated successfully!")
            return redirect(url_for('admin') + "#wheel_sets")

        # Pass the wheel set data to the template
        wheel_set["_id"] = str(wheel_set["_id"])
    except Exception as e:
        flash(f"Error loading wheel set: {str(e)}")
        return redirect(url_for('admin') + "#wheel_sets")

    return render_template("edit_wheel_set.html", wheel_set=wheel_set)


@app.route('/delete_wheel_set', methods=["POST"])
@login_required
def delete_wheel_set():
    if not current_user.admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('home'))

    wheel_id = request.form.get('wheel_id')
    if not wheel_id:
        flash("Wheel ID not provided!")
        return redirect(url_for('admin') + "#wheel_sets")

    try:
        result = db.wheel_set.delete_one({"_id": ObjectId(wheel_id)})
        if result.deleted_count > 0:
            flash("Wheel set deleted successfully!")
        else:
            flash("Wheel set not found!")
    except Exception as e:
        flash(f"Error deleting wheel set: {str(e)}")

    return redirect(url_for('admin') + "#wheel_sets")


if __name__ == '__main__':
    app.run(debug=True)
