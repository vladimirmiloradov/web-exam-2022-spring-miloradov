from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import current_user, login_required
from app import db
from models import Book, User, Review, Genre, Join, Image
from tools import BooksFilter, ImageSaver, ReviewsFilter
from auth import check_rights
import os
import markdown
import bleach


bp = Blueprint('books', __name__, url_prefix='/books')

PER_PAGE = 1
PER_PAGE_REVIEWS = 10

BOOK_PARAMS = ['name', 'short_desc', 'publication_year', 'publishing_house', 'author', 'volume']
REVIEW_PARAMS = ['book_id', 'user_id', 'rating', 'text']

def params():
    return { p: request.form.get(p) for p in BOOK_PARAMS }

def review_params():
    return { p: request.form.get(p) for p in REVIEW_PARAMS }
    
def search_params():
    return {'name': request.args.get('name')}

def search_params_review(book_id):
    return {
        'name': request.args.get('name'),
        'book_id': book_id
    }


@bp.route('/<int:book_id>/delete', methods=['POST'])
@login_required
@check_rights('delete')
def delete(book_id):
    book = Book.query.filter_by(id=book_id).one()
    img = Image.query.filter_by(book_id=book.id).one()
    img = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'media', 'images') + '\\' + img.storage_filename
    db.session.delete(book)
    db.session.commit()
    os.remove(img)
    flash('Книга была успешно удалена!', 'success')
    return redirect(url_for('index'))

@bp.route('/new')
@login_required
@check_rights('create')
def new():
    genres = Genre.query.all()
    return render_template('books/new.html', genres=genres)

@bp.route('/create', methods=['POST'])
@login_required
@check_rights('create')
def create():
    book = Book(**params())
    book.short_desc = bleach.clean(book.short_desc)
    db.session.add(book)
    db.session.commit()
    book = Book.query.order_by(Book.id.desc()).first()
    f = request.files.get('background_img')
    if f and f.filename:
        img = ImageSaver(f).save(book.id)
    array_genres = request.form.getlist('genre')
    for genre in array_genres:
        book_genre = Join()
        book_genre.book_id = book.id
        book_genre.genre_id = genre
        db.session.add(book_genre)
    db.session.commit()
    flash(f'Книга {book.name} была успешно добавлена!', 'success')
    return redirect(url_for('index'))

@bp.route('/<int:book_id>/edit')
@login_required
@check_rights('update')
def edit(book_id):
    genres = Genre.query.all()
    genres_arr = Join.query.filter_by(book_id=book_id).all()
    selected = []
    for genre in genres_arr:
        selected.append(genre.genre.id)
    book = Book.query.filter_by(id=book_id).one()
    return render_template('books/edit.html', book=book, genres=genres, selected=selected)

@bp.route('/<int:book_id>/update', methods=['POST'])
@login_required
@check_rights('update')
def update(book_id):
    book = Book.query.filter_by(id=book_id).one()
    parameters = params()
    # for key in BOOK_PARAMS: <------------  Не работает
    #     book.key = parameters[key]
    book.name = parameters['name']
    book.short_desc = parameters['short_desc']
    book.short_desc = bleach.clean(book.short_desc)
    book.publiation_year = parameters['publication_year']
    book.publishing_house = parameters['publishing_house']
    book.author = parameters['author']
    book.volume = parameters['volume']
    db.session.commit()
    flash(f'Книга {book.name} была успешно обновлена!', 'success')
    return redirect(url_for('index'))  

@bp.route('/<int:book_id>')
@login_required
def show(book_id):
    books = Book.query.get(book_id)
    books.short_desc = markdown.markdown(books.short_desc)
    reviews = Review.query.filter_by(book_id=book_id).limit(5)
    user_review = None
    if current_user.is_authenticated is True:
        user_review = Review.query.filter_by(book_id=book_id, user_id=current_user.id).first()    
    users = User.query.all()
    genres_quer = Join.query.filter_by(book_id=book_id).all()
    genres=[]
    for genre in genres_quer:
        genres.append(genre.genre.name)
    genres = ', '.join(genres)
    img = Image.query.filter_by(book_id=book_id).first()
    img = img.url
    return render_template('books/show.html', book=books, review=reviews, users=users, user_review=user_review, genres=genres, image=img)

@bp.route('/<int:book_id>', methods=['POST'])
@login_required
def apply_review(book_id):
    books = Book.query.filter_by(id=book_id).first()
    review = Review(**review_params())
    review.text = bleach.clean(review.text)
    books.rating_sum += int(review.rating)
    books.rating_num += 1
    db.session.add(review)
    db.session.commit()
    flash('Ваш отзыв успешно записан!', 'success')
    return redirect(url_for('books.show', book_id=books.id))

@bp.route('/<int:book_id>/reviews')
@login_required
def reviews(book_id):
    page = request.args.get('page', 1, type=int)
    reviews = ReviewsFilter(book_id).perform_date_desc()
    books = Book.query.filter_by(id=book_id).first()
    pagination = reviews.paginate(page, PER_PAGE_REVIEWS)
    reviews = pagination.items
    return render_template('books/reviews.html', reviews=reviews, books=books, pagination=pagination, search_params=search_params_review(book_id))

@bp.route('/<int:book_id>/reviews', methods=['POST'])
@login_required
def reviews_sort(book_id):
    page = request.args.get('page', 1, type=int)
    reviews = ReviewsFilter(book_id).perform_date_desc()
    if request.form.get('sort') == 'new':
        reviews = ReviewsFilter(book_id).perform_date_desc()
    if request.form.get('sort') == 'old':
        reviews = ReviewsFilter(book_id).perform_date_asc()
    if request.form.get('sort') == 'good':
        reviews = ReviewsFilter(book_id).perform_rating_desc()
    if request.form.get('sort') == 'bad':
        reviews = ReviewsFilter(book_id).perform_rating_asc()
    req_form = request.form.get('sort')
    books = Book.query.filter_by(id=book_id).first()
    pagination = reviews.paginate(page, PER_PAGE_REVIEWS)
    reviews = pagination.items
    return render_template('books/reviews.html', reviews=reviews, books=books, req_form=req_form, pagination=pagination, search_params=search_params_review(book_id))
