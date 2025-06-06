"""Add lobbies

Revision ID: 88ce61f6a08c
Revises: d5aee1aa8a03
Create Date: 2025-04-12 19:57:53.665187

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '88ce61f6a08c'
down_revision: Union[str, None] = 'd5aee1aa8a03'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('lobbies',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('game_id', sa.String(), nullable=True),
    sa.Column('host_id', sa.Integer(), nullable=True),
    sa.Column('status', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['host_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_lobbies_game_id'), 'lobbies', ['game_id'], unique=True)
    op.create_index(op.f('ix_lobbies_id'), 'lobbies', ['id'], unique=False)
    op.create_table('lobby_players',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('lobby_id', sa.Integer(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('slot', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['lobby_id'], ['lobbies.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('match_results',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('lobby_id', sa.Integer(), nullable=True),
    sa.Column('winner_id', sa.Integer(), nullable=True),
    sa.Column('result', sa.String(), nullable=True),
    sa.Column('ticks', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['lobby_id'], ['lobbies.id'], ),
    sa.ForeignKeyConstraint(['winner_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('match_results')
    op.drop_table('lobby_players')
    op.drop_index(op.f('ix_lobbies_id'), table_name='lobbies')
    op.drop_index(op.f('ix_lobbies_game_id'), table_name='lobbies')
    op.drop_table('lobbies')
    # ### end Alembic commands ###
