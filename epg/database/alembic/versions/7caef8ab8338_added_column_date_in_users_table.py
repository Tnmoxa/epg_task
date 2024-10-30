"""added column date in users table

Revision ID: 7caef8ab8338
Revises: 1b9cd65dc3a4
Create Date: 2024-10-30 22:11:17.014058

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7caef8ab8338'
down_revision: Union[str, None] = '1b9cd65dc3a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('date', sa.DateTime(), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'date')
    # ### end Alembic commands ###
