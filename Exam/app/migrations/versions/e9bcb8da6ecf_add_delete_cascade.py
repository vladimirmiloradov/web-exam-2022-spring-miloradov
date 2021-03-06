"""Add delete cascade

Revision ID: e9bcb8da6ecf
Revises: 241cf8273ce0
Create Date: 2022-06-15 12:23:06.146270

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'e9bcb8da6ecf'
down_revision = '241cf8273ce0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('fk_books_background_image_id_images', 'books', type_='foreignkey')
    op.drop_column('books', 'background_image_id')
    op.drop_constraint('fk_images_book_id_books', 'images', type_='foreignkey')
    op.create_foreign_key(op.f('fk_images_book_id_books'), 'images', 'books', ['book_id'], ['id'], ondelete='CASCADE')
    op.drop_constraint('fk_join_genre_id_genres', 'join', type_='foreignkey')
    op.drop_constraint('fk_join_book_id_books', 'join', type_='foreignkey')
    op.create_foreign_key(op.f('fk_join_genre_id_genres'), 'join', 'genres', ['genre_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(op.f('fk_join_book_id_books'), 'join', 'books', ['book_id'], ['id'], ondelete='CASCADE')
    op.drop_constraint('fk_reviews_user_id_users', 'reviews', type_='foreignkey')
    op.drop_constraint('fk_reviews_book_id_books', 'reviews', type_='foreignkey')
    op.create_foreign_key(op.f('fk_reviews_user_id_users'), 'reviews', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(op.f('fk_reviews_book_id_books'), 'reviews', 'books', ['book_id'], ['id'], ondelete='CASCADE')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(op.f('fk_reviews_book_id_books'), 'reviews', type_='foreignkey')
    op.drop_constraint(op.f('fk_reviews_user_id_users'), 'reviews', type_='foreignkey')
    op.create_foreign_key('fk_reviews_book_id_books', 'reviews', 'books', ['book_id'], ['id'])
    op.create_foreign_key('fk_reviews_user_id_users', 'reviews', 'users', ['user_id'], ['id'])
    op.drop_constraint(op.f('fk_join_book_id_books'), 'join', type_='foreignkey')
    op.drop_constraint(op.f('fk_join_genre_id_genres'), 'join', type_='foreignkey')
    op.create_foreign_key('fk_join_book_id_books', 'join', 'books', ['book_id'], ['id'])
    op.create_foreign_key('fk_join_genre_id_genres', 'join', 'genres', ['genre_id'], ['id'])
    op.drop_constraint(op.f('fk_images_book_id_books'), 'images', type_='foreignkey')
    op.create_foreign_key('fk_images_book_id_books', 'images', 'books', ['book_id'], ['id'])
    op.add_column('books', sa.Column('background_image_id', mysql.VARCHAR(length=100), nullable=True))
    op.create_foreign_key('fk_books_background_image_id_images', 'books', 'images', ['background_image_id'], ['id'])
    # ### end Alembic commands ###
