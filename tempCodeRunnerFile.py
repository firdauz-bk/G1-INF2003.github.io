    {'$match': query},
        {'$lookup': {
            'from': 'user',  # Corrected from 'users'
            'localField': 'user_id',
            'foreignField': '_id',
            'as': 'user'
        }},
        {'$unwind': '$user'},
        {'$lookup': {
            'from': 'customization',  # Corrected from 'customizations'
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
    ]
