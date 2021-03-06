"""empty message

Revision ID: 0001 add team_metric
Revises: 
Create Date: 2018-12-24 11:56:24.412646

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0001 add team_metric'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('team_metric',
    sa.Column('project_id', sa.String(), nullable=False),
    sa.Column('sprint_id', sa.Integer(), nullable=False),
    sa.Column('started_on', sa.DateTime(), nullable=False),
    sa.Column('ended_on', sa.DateTime(), nullable=False),
    sa.Column('source', sa.String(), nullable=False),
    sa.Column('avg_cycle_time', sa.Integer(), nullable=False),
    sa.Column('process_cycle_efficiency', sa.Float(), nullable=False),
    sa.Column('num_completed', sa.Integer(), nullable=False),
    sa.Column('num_incomplete', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('project_id', 'sprint_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('team_metric')
    # ### end Alembic commands ###
