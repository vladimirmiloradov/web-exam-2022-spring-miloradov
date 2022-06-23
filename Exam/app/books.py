from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import current_user, login_required
from app import db
from models import Book, User, Review, Genre, Join, Image, Selection, BookSelection
from tools import BooksFilter, ImageSaver, ReviewsFilter
from auth import check_rights
import os
import markdown
import bleach
from sqlalchemy import exc
import hashlib


bp = Blueprint('books', __name__, url_prefix='/books')

PER_PAGE = 1
PER_PAGE_REVIEWS = 10

BOOK_PARAMS = ['name', 'short_desc', 'publication_year', 'publishing_house', 'author', 'volume']
REVIEW_PARAMS = ['book_id', 'user_id', 'rating', 'text']
SELECTION_PARAMS = ['name','user_id']

def params():
    return { p: request.form.get(p) for p in BOOK_PARAMS }

def selection_params():
    return { p: request.form.get(p) for p in SELECTION_PARAMS }

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
    try:
        db.session.add(book)
        db.session.commit()
    except exc.SQLAlchemyError:
        db.session.rollback()
        flash('При сохранении данных возникла ошибка. Проверьте корректность введённых данных.', 'danger')
        return redirect(url_for('books.new'))
    book = Book.query.order_by(Book.id.desc()).first()
    f = request.files.get('background_img')
    if f and f.filename:
        img = ImageSaver(f).save(book.id)
        if img == None:
            db.session.delete(book)
            db.session.commit()
            flash('При сохранении данных возникла ошибка. Проверьте корректность введённых данных.', 'danger')
            return redirect(url_for('books.new'))
    array_genres = request.form.getlist('genre')
    if len(array_genres) == 0:
        flash('При сохранении данных возникла ошибка. Выберите жанры для книги.', 'danger')
        return redirect(url_for('books.new'))
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
    return render_template('books/edit.html', genres=genres, selected=selected, book=book)

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
        if user_review:
            user_review.text = markdown.markdown(user_review.text)
    users = User.query.all()
    book_genres = Join.query.filter_by(book_id=book_id).all()
    genres=[]
    for genre in book_genres:
        genres.append(genre.genre.name)
    genres = ', '.join(genres)
    img = Image.query.filter_by(book_id=book_id).first()
    img = img.url
    selections = Selection.query.filter_by(user_id=current_user.id).all()
    return render_template('books/show.html', book=books, review=reviews, users=users, user_review=user_review, genres=genres, image=img, selections=selections)

@bp.route('/<int:book_id>', methods=['POST'])
@login_required
def apply_review(book_id):
    books = Book.query.filter_by(id=book_id).first()
    review = Review(**review_params())
    review.text = bleach.clean(review.text)
    if not review.text:
        review.text = None
    books.rating_sum += int(review.rating)
    books.rating_num += 1
    try:
        db.session.add(review)
        db.session.commit()
        flash('Ваш отзыв успешно записан!', 'success')
        return redirect(url_for('books.show', book_id=books.id))
    except exc.SQLAlchemyError:
        db.session.rollback()
        flash('Ошибка записи отзыва! Отзыв не может быть пустым!', 'danger')
        return redirect(url_for('books.apply_review', book_id=books.id))



@bp.route('/<int:book_id>/reviews')
@login_required
def reviews(book_id):
    param = request.args.get('param')
    page = request.args.get('page', 1, type=int)
    reviews = ReviewsFilter(book_id).sorting(param)
    books = Book.query.filter_by(id=book_id).first()
    pagination = reviews.paginate(page, PER_PAGE_REVIEWS)
    reviews = pagination.items
    return render_template('books/reviews.html', reviews=reviews, books=books, pagination=pagination, search_params=search_params_review(book_id), param=param)

@bp.route('/user_selections')
@login_required
@check_rights('create_selection')
def user_selections():
    endpoint = '/books/user_selections'
    selections = Selection.query.filter_by(user_id=current_user.id).all()
    array_counts = []
    for selection in selections:
        sel_id = selection.id
        count = len(BookSelection.query.filter_by(selection_id=sel_id).all())
        array_counts.append(count)
    return render_template('books/selections.html', endpoint=endpoint, selections=selections, array_counts=array_counts)

@bp.route('/user_selections/<int:selection_id>/show_user_selection')
@login_required
@check_rights('create_selection')
def show_user_selection(selection_id):
    array_books_ids = []
    rows = BookSelection.query.filter_by(selection_id=selection_id).all()
    for row in rows:
        array_books_ids.append(row.book_id)
    books = []
    for id in array_books_ids:
        book = Book.query.filter_by(id=id).first()
        books.append(book)
    print(books)
    images_for_books = []
    book_genres = []
    for book in books:
        image = Image.query.filter_by(book_id=book.id).first()
        images_for_books.append(image.url)
        genres_rows = Join.query.filter_by(book_id=book.id).all()
        genres = []
        for genre in genres_rows:
            genres.append(genre.genre.name)
        genres_str =', '.join(genres)
        book_genres.append(genres_str)
    return render_template('books/user_selection.html', books=books, search_params=search_params(), images=images_for_books, genres=book_genres)

@bp.route('/<int:user_id>/create_selection', methods=['POST'])
@login_required
@check_rights('create_selection')
def create_selection(user_id):
    selection = Selection(**selection_params())
    selection.user_id = user_id
    db.session.add(selection)
    db.session.commit()
    flash(f'Подборка {selection.name} была успешно добавлена!', 'success')
    return redirect(url_for('books.user_selections'))

@bp.route('/<int:book_id>/add_book_to_selection', methods=['POST'])
@login_required
@check_rights('create_selection')
def add_book_to_selection(book_id):
    selection = request.form.get('selection')
    row = BookSelection()
    row.book_id = book_id
    row.selection_id = selection
    try:
        db.session.add(row)
        db.session.commit()
        flash(f'Книга была успешно добавлена в подборку!', 'success')
        return redirect(url_for('books.show', book_id=book_id))
    except exc.SQLAlchemyError:
        flash('Ошибка при добавлении книги в подборку! Выберите подборку.', 'danger')
        return redirect(url_for('books.show', book_id=row.book_id))