def regenerate_collections(db):
    """
    Drops all collections in the database to reset the data.
    """
    collections = [
        "vehicle_types",
        "brands",
        "models",
        "colors",
        "wheel_sets",
        "users",
        "customizations",
        "posts",
        "comments"
    ]
    for collection in collections:
        db[collection].drop()
    print("All collections dropped.")
