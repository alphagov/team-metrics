"""empty message

Revision ID: 0005 add team name to git_metric
Revises: 0004 use repo name not url
Create Date: 2019-01-25 15:09:08.178909

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0005 add team name to git_metric'
down_revision = '0004 use repo name not url'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('git_metric', sa.Column('team_name', sa.String(), nullable=True))

    update_team_name = "UPDATE git_metric SET team_name='observe'"
    op.execute(update_team_name)
    op.alter_column('git_metric', 'team_name', nullable=False)

    update_team_id = "UPDATE git_metric SET team_id='1'"
    op.execute(update_team_id)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('git_metric', 'team_name')

    update_team_id = "UPDATE git_metric SET team_id='2613549'"
    op.execute(update_team_id)
    # ### end Alembic commands ###
