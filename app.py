from . import create_app
from .extensions import db
from flask_migrate import Migrate
from flask import render_template

app = create_app()
migrate = Migrate(app, db)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True)
