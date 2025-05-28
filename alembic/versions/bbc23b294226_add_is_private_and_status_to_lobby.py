"""Add is_private, avg_rating, created_at and convert status to ENUM

Revision ID: bbc23b294226
Revises: e484e96d87ba
Create Date: 2025-05-27 22:14:59.831589
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'bbc23b294226'
down_revision = 'e484e96d87ba'
branch_labels = None
depends_on = None

# 1) Определяем новый ENUM-тип
status_enum = postgresql.ENUM(
    'waiting',
    'in_progress',
    'finished',
    name='lobbystatus'
)

def upgrade() -> None:
    # 2) Создаём ENUM в БД (если ещё нет)
    status_enum.create(op.get_bind(), checkfirst=True)

    # 3) Добавляем новые колонки с server_default для существующих строк
    op.add_column(
        'lobbies',
        sa.Column('created_at', sa.DateTime(), nullable=True)
    )
    op.add_column(
        'lobbies',
        sa.Column(
            'is_private',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('false')
        )
    )
    op.add_column(
        'lobbies',
        sa.Column(
            'avg_rating',
            sa.Float(),
            nullable=False,
            server_default=sa.text('0')
        )
    )

    # 4) Конвертируем существующий VARCHAR-поле status в ENUM
    op.alter_column(
        'lobbies',
        'status',
        existing_type=sa.VARCHAR(),
        type_=status_enum,
        nullable=False,
        server_default=sa.text("'waiting'"),
        postgresql_using="status::text::lobbystatus"
    )

    # 5) Создаём индексы для новых полей
    op.create_index(op.f('ix_lobbies_is_private'), 'lobbies', ['is_private'], unique=False)
    op.create_index(op.f('ix_lobbies_status'),     'lobbies', ['status'],     unique=False)

    # 6) Убираем server_default – дальше приложение контролирует значения
    op.alter_column('lobbies', 'is_private', server_default=None)
    op.alter_column('lobbies', 'avg_rating', server_default=None)
    op.alter_column('lobbies', 'status',     server_default=None)


def downgrade() -> None:
    # Удаляем индексы
    op.drop_index(op.f('ix_lobbies_status'),     table_name='lobbies')
    op.drop_index(op.f('ix_lobbies_is_private'), table_name='lobbies')

    # Откатываем status обратно в VARCHAR
    op.alter_column(
        'lobbies',
        'status',
        existing_type=status_enum,
        type_=sa.VARCHAR(),
        nullable=True,
        postgresql_using="status::text"
    )

    # Удаляем добавленные колонки
    op.drop_column('lobbies', 'avg_rating')
    op.drop_column('lobbies', 'is_private')
    op.drop_column('lobbies', 'created_at')

    # Удаляем ENUM-тип
    status_enum.drop(op.get_bind(), checkfirst=True)
