"""empty message

Revision ID: 9821b7fe58a4
Revises: 
Create Date: 2018-11-17 19:47:57.979610

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9821b7fe58a4'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('aircrafts',
    sa.Column('aircraft', sa.String(length=15), nullable=False),
    sa.Column('seatcount', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('aircraft'),
    sa.UniqueConstraint('aircraft')
    )
    op.create_table('flights',
    sa.Column('number', sa.String(length=10), nullable=False),
    sa.Column('start', sa.String(length=3), nullable=False),
    sa.Column('end', sa.String(length=3), nullable=False),
    sa.Column('departure', sa.DateTime(), nullable=False),
    sa.Column('aircrafttype', sa.String(length=15), nullable=False),
    sa.ForeignKeyConstraint(['aircrafttype'], ['aircrafts.aircraft'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('number'),
    sa.UniqueConstraint('number'),
    sa.UniqueConstraint('start', 'end', 'departure', name='check_deptstartend_unique')
    )
    op.create_table('tickets',
    sa.Column('number', sa.String(length=10), nullable=False),
    sa.Column('flightnumber', sa.String(length=10), nullable=False),
    sa.Column('passengername', sa.String(length=25), nullable=False),
    sa.Column('passportnumber', sa.String(length=10), nullable=False),
    sa.ForeignKeyConstraint(['flightnumber'], ['flights.number'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('number'),
    sa.UniqueConstraint('number')
    )
    op.create_table('seats',
    sa.Column('ticketnumber', sa.String(length=15), nullable=False),
    sa.Column('seatlabel', sa.Enum('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', name='seatlabelenum'), nullable=False),
    sa.Column('seatrow', sa.Integer(), nullable=False),
    sa.Column('flightnumber', sa.String(length=10), nullable=False),
    sa.CheckConstraint('seatrow >= 1', name='check_seatrow_minimumone'),
    sa.ForeignKeyConstraint(['flightnumber'], ['flights.number'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['ticketnumber'], ['tickets.number'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('seatlabel', 'seatrow'),
    sa.UniqueConstraint('seatlabel', 'seatrow', name='check_seatlabelrow_unique')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('seats')
    op.drop_table('tickets')
    op.drop_table('flights')
    op.drop_table('aircrafts')
    # ### end Alembic commands ###
