import os
from sqlalchemy import text
from app import create_app
from app.extensions import db

print("Dropping alembic_version...")
app = create_app()
with app.app_context():
    try:
        db.session.execute(text("DROP TABLE IF EXISTS alembic_version;"))
        db.session.commit()
        print("Dropped alembic_version")
    except Exception as e:
        print("Error: ", e)
