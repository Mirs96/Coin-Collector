
def initialize_database():
    with app.app_context():
        db.create_all()