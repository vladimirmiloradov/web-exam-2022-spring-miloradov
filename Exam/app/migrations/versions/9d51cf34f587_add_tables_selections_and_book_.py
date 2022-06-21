"""Add tables selections and book_selections

Revision ID: 9d51cf34f587
Revises: e9bcb8da6ecf
Create Date: 2022-06-21 13:05:34.783395

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9d51cf34f587'
down_revision = 'e9bcb8da6ecf'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('selections',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_selections_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_selections'))
    )
    op.create_table('book_selection',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('selection_id', sa.Integer(), nullable=True),
    sa.Column('book_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['book_id'], ['books.id'], name=op.f('fk_book_selection_book_id_books'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['selection_id'], ['selections.id'], name=op.f('fk_book_selection_selection_id_selections'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_book_selection'))
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('book_selection')
    op.drop_table('selections')
    # ### end Alembic commands ###