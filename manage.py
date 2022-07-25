from flask.cli import FlaskGroup
from project.server.extensions import db

from project.server import create_app


app = create_app()
db.session.commit()
db.drop_all()
db.create_all()

cli = FlaskGroup(create_app=create_app)


if __name__ == "__main__":
    cli()
