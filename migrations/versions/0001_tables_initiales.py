"""Tables initiales : catégories, extractions, livres.

Revision ID: 0001
Revises:
"""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nom", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_categories")),
        sa.UniqueConstraint("nom", name=op.f("uq_categories_nom")),
    )
    op.create_table(
        "extractions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("statut", sa.String(length=20), nullable=False),
        sa.Column("debut", sa.DateTime(timezone=True), server_default=sa.text("now()"),
                  nullable=False),
        sa.Column("fin", sa.DateTime(timezone=True), nullable=True),
        sa.Column("nb_livres", sa.Integer(), nullable=True),
        sa.Column("erreur", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_extractions")),
    )
    op.create_index("uq_extractions_en_cours", "extractions", ["statut"], unique=True,
                    postgresql_where=sa.text("statut = 'en_cours'"))
    op.create_table(
        "livres",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("categorie_id", sa.Integer(), nullable=False),
        sa.Column("titre", sa.Text(), nullable=False),
        sa.Column("prix_gbp", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("note", sa.SmallInteger(), nullable=True),
        sa.Column("en_stock", sa.Boolean(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("extraction_id", sa.Integer(), nullable=True),
        sa.Column("maj_le", sa.DateTime(timezone=True), server_default=sa.text("now()"),
                  nullable=False),
        sa.ForeignKeyConstraint(["categorie_id"], ["categories.id"],
                                name=op.f("fk_livres_categorie_id_categories")),
        sa.ForeignKeyConstraint(["extraction_id"], ["extractions.id"],
                                name=op.f("fk_livres_extraction_id_extractions"),
                                ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_livres")),
        sa.UniqueConstraint("url", name=op.f("uq_livres_url")),
    )
    op.create_index(op.f("ix_livres_categorie_id"), "livres", ["categorie_id"])


def downgrade() -> None:
    op.drop_table("livres")
    op.drop_table("extractions")
    op.drop_table("categories")
