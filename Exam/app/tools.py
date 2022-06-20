from models import Image, Review, Book
import hashlib
import uuid
import os
from werkzeug.utils import secure_filename
from app import db, app

class BooksFilter:
    def __init__(self, name):
        self.name = name
        self.query = Book.query
    
    def perform(self):
        self.__filter_by_name()
        return self.query.order_by(Book.created_at.desc())
    
    def __filter_by_name(self):
        if self.name:
            self.query = self.query.filter(Book.name.ilike('%' + self.name + '%'))
    


class ReviewsFilter:
    def __init__(self, book_id):
        self.query = Review.query.filter_by(book_id=book_id)

    def perform_date_desc(self):
        return self.query.order_by(Review.created_at.desc())

    def perform_date_asc(self):
        return self.query.order_by(Review.created_at.asc())

    def perform_rating_desc(self):
        return self.query.order_by(Review.rating.desc())

    def perform_rating_asc(self):
        return self.query.order_by(Review.rating.asc())

class ImageSaver:
    def __init__(self, file):
        self.file = file
    
    def save(self, book_id):
        self.img = self.__find_by_md5_hash()
        if self.img is not None:
            return self.img
        file_name = secure_filename(self.file.filename)
        self.img = Image(
            id=str(uuid.uuid4()), 
            filename=file_name, 
            mime_type=self.file.mimetype, 
            md5_hash=self.md5_hash
        )
        self.file.save(os.path.join(app.config['UPLOAD_FOLDER'], self.img.storage_filename ))
        self.img.book_id = book_id
        db.session.add(self.img)
        db.session.commit()
        return self.img


    def __find_by_md5_hash(self):
        self.md5_hash = hashlib.md5(self.file.read()).hexdigest()
        self.file.seek(0)
        return Image.query.filter(Image.md5_hash == self.md5_hash).first()
