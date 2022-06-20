import os
from flask import Flask, render_template, send_file, abort, send_from_directory, request
from sqlalchemy import MetaData
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
application = app

app.config.from_pyfile('config.py')

convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)
db = SQLAlchemy(app, metadata=metadata)
migrate = Migrate(app, db)

from auth import bp as auth_bp, init_login_manager, check_rights
from books import bp as books_bp

app.register_blueprint(auth_bp)
app.register_blueprint(books_bp)

init_login_manager(app)

from tools import BooksFilter
from models import Image, Join

def search_params():
    return {'name': request.args.get('name')}
    
PER_PAGE = 10

@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    books = BooksFilter(**search_params()).perform()
    pagination = books.paginate(page, PER_PAGE)
    books = pagination.items
    images = []
    genres_arr = []
    for book in books:
        image = Image.query.filter_by(book_id=book.id).first()
        images.append(image.url)
        genres_rows = Join.query.filter_by(book_id=book.id).all()
        genres = []
        for genre in genres_rows:
            genres.append(genre.genre.name)
        genres_str =', '.join(genres)
        genres_arr.append(genres_str)
    return render_template('books/index.html', books=books, pagination=pagination, search_params=search_params(), images=images, genres=genres_arr)

@app.route('/media/images/<image_id>')
def image(image_id):
    image = Image.query.get(image_id)
    if image is None:
        abort(404)
    return send_from_directory(app.config['UPLOAD_FOLDER'], image.storage_filename)


