"""Split results into model_metadata, test_results, and train_resultss

Revision ID: 89a8ce240bae
Revises: 7d57d1cf3429
Create Date: 2018-03-27 15:12:45.249609

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "89a8ce240bae"
down_revision = "7d57d1cf3429"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute("CREATE SCHEMA IF NOT EXISTS model_metadata")
    op.execute("CREATE SCHEMA IF NOT EXISTS test_results")
    op.execute("CREATE SCHEMA IF NOT EXISTS train_results")
    op.execute(
        "ALTER TABLE results.models SET SCHEMA model_metadata;"
        + " ALTER TABLE results.model_groups SET SCHEMA model_metadata;"
        + " ALTER TABLE results.experiments SET SCHEMA model_metadata;"
        + " ALTER TABLE results.list_predictions SET SCHEMA model_metadata;"
        + " ALTER TABLE results.predictions RENAME TO test_predictions;"
        + " ALTER TABLE results.test_predictions SET SCHEMA test_results;"
        + " ALTER TABLE results.evaluations RENAME TO test_evaluations;"
        + " ALTER TABLE results.test_evaluations SET SCHEMA test_results;"
        + " ALTER TABLE results.individual_importances SET SCHEMA test_results;"
        + " ALTER TABLE results.feature_importances SET SCHEMA train_results;"
    )

    op.execute("ALTER TABLE model_metadata.models ADD COLUMN model_size real")
    op.create_table(
        "matrices",
        sa.Column("matrix_id", sa.String(), nullable=True),
        sa.Column("matrix_uuid", sa.String(), nullable=False),
        sa.Column("matrix_type", sa.String(), nullable=True),
        sa.Column("labeling_window", sa.Interval(), nullable=True),
        sa.Column("n_examples", sa.Integer(), nullable=True),
        sa.Column(
            "creation_time",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("lookback_duration", sa.Interval(), nullable=True),
        sa.Column("feature_start_time", sa.DateTime(), nullable=True),
        sa.Column(
            "matrix_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.PrimaryKeyConstraint("matrix_uuid"),
        schema="model_metadata",
    )
    op.create_index(
        op.f("ix_model_metadata_matrices_matrix_uuid"),
        "matrices",
        ["matrix_uuid"],
        unique=True,
        schema="model_metadata",
    )

    # Create train_predictions and train_evaluations
    op.create_table(
        "train_evaluations",
        sa.Column("model_id", sa.Integer(), nullable=False),
        sa.Column("evaluation_start_time", sa.DateTime(), nullable=False),
        sa.Column("evaluation_end_time", sa.DateTime(), nullable=False),
        sa.Column("as_of_date_frequency", sa.Interval(), nullable=False),
        sa.Column("metric", sa.String(), nullable=False),
        sa.Column("parameter", sa.String(), nullable=False),
        sa.Column("value", sa.Numeric(), nullable=True),
        sa.Column("num_labeled_examples", sa.Integer(), nullable=True),
        sa.Column("num_labeled_above_threshold", sa.Integer(), nullable=True),
        sa.Column("num_positive_labels", sa.Integer(), nullable=True),
        sa.Column("sort_seed", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["model_id"], ["model_metadata.models.model_id"]),
        sa.PrimaryKeyConstraint(
            "model_id",
            "evaluation_start_time",
            "evaluation_end_time",
            "as_of_date_frequency",
            "metric",
            "parameter",
        ),
        schema="train_results",
    )
    op.create_table(
        "train_predictions",
        sa.Column("model_id", sa.Integer(), nullable=False),
        sa.Column("entity_id", sa.BigInteger(), nullable=False),
        sa.Column("as_of_date", sa.DateTime(), nullable=False),
        sa.Column("score", sa.Numeric(), nullable=True),
        sa.Column("label_value", sa.Integer(), nullable=True),
        sa.Column("rank_abs", sa.Integer(), nullable=True),
        sa.Column("rank_pct", sa.Float(), nullable=True),
        sa.Column("matrix_uuid", sa.Text(), nullable=True),
        sa.Column("test_label_timespan", sa.Interval(), nullable=True),
        sa.ForeignKeyConstraint(
            ["matrix_uuid"], ["model_metadata.matrices.matrix_uuid"]
        ),
        sa.ForeignKeyConstraint(["model_id"], ["model_metadata.models.model_id"]),
        sa.PrimaryKeyConstraint("model_id", "entity_id", "as_of_date"),
        schema="train_results",
    )

    # Foreign Keys for the models, test_predictions, and train_predictions tables
    op.execute(
        """ALTER TABLE model_metadata.models
                  ADD CONSTRAINT matrix_uuid_for_models
                  FOREIGN KEY (train_matrix_uuid)
                  REFERENCES model_metadata.matrices(matrix_uuid); """
    )

    op.execute(
        """ALTER TABLE test_results.test_predictions
                  ADD CONSTRAINT matrix_uuid_for_testpred
                  FOREIGN KEY (matrix_uuid)
                  REFERENCES model_metadata.matrices(matrix_uuid); """
    )

    op.execute(
        """ALTER TABLE train_results.train_predictions
                  ADD CONSTRAINT matrix_uuid_for_trainpred
                  FOREIGN KEY (matrix_uuid)
                  REFERENCES model_metadata.matrices(matrix_uuid); """
    )

    op.execute("DROP SCHEMA IF EXISTS results")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute("CREATE SCHEMA IF NOT EXISTS results")

    op.execute(
        """ALTER TABLE model_metadata.models DROP CONSTRAINT "matrix_uuid_for_models";
        ALTER TABLE test_results.test_predictions DROP CONSTRAINT "matrix_uuid_for_testpred";
        ALTER TABLE train_results.train_predictions DROP CONSTRAINT "matrix_uuid_for_trainpred"; """
    )

    op.execute(
        "ALTER TABLE model_metadata.models SET SCHEMA results;"
        + " ALTER TABLE model_metadata.model_groups SET SCHEMA results;"
        + " ALTER TABLE model_metadata.experiments SET SCHEMA results;"
        + " ALTER TABLE model_metadata.list_predictions SET SCHEMA results;"
        + " ALTER TABLE test_results.test_predictions RENAME TO predictions;"
        + " ALTER TABLE test_results.predictions SET SCHEMA results;"
        + " ALTER TABLE test_results.test_evaluations RENAME TO evaluations;"
        + " ALTER TABLE test_results.evaluations SET SCHEMA results;"
        + " ALTER TABLE test_results.individual_importances SET SCHEMA results;"
        + " ALTER TABLE train_results.feature_importances SET SCHEMA results;"
    )

    op.drop_index(
        op.f("ix_model_metadata_matrices_matrix_uuid"),
        table_name="matrices",
        schema="model_metadata",
    )
    op.execute("ALTER TABLE results.models DROP COLUMN IF EXISTS model_size")
    op.execute("DROP TABLE model_metadata.matrices CASCADE")
    op.execute("DROP TABLE train_results.train_predictions CASCADE")
    op.execute("DROP TABLE train_results.train_evaluations CASCADE")

    op.execute("DROP SCHEMA IF EXISTS model_metadata")
    op.execute("DROP SCHEMA IF EXISTS train_results")
    op.execute("DROP SCHEMA IF EXISTS test_results")
    # ### end Alembic commands ###
