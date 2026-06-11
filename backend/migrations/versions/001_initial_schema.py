"""Initial schema — all 7 tables

Revision ID: 001
Revises: 
Create Date: 2024-01-01
"""
from alembic import op
import sqlalchemy as sa

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # contacts
    op.create_table(
        'contacts',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('company', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='Active'),
        sa.Column('account_value', sa.Float(), server_default='0.0'),
        sa.Column('churn_risk_score', sa.Float(), server_default='0.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('last_contact_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )
    op.create_index('ix_contacts_email', 'contacts', ['email'])

    # threads
    op.create_table(
        'threads',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('thread_id', sa.String(), nullable=False),
        sa.Column('subject', sa.String(), nullable=True),
        sa.Column('sender_email', sa.String(), nullable=False),
        sa.Column('first_seen_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('status', sa.String(), nullable=False, server_default='Open'),
        sa.Column('assigned_to', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['sender_email'], ['contacts.email']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('thread_id'),
    )
    op.create_index('ix_threads_thread_id', 'threads', ['thread_id'])
    op.create_index('ix_threads_sender_email', 'threads', ['sender_email'])

    # emails
    op.create_table(
        'emails',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('message_id', sa.String(), nullable=False),
        sa.Column('thread_id', sa.String(), nullable=False),
        sa.Column('sender', sa.String(), nullable=False),
        sa.Column('subject', sa.String(), nullable=True),
        sa.Column('body', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=True),
        sa.Column('received_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('sentiment', sa.String(), nullable=True),
        sa.Column('sentiment_score', sa.Float(), nullable=True),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('urgency', sa.String(), nullable=True),
        sa.Column('requires_human', sa.Boolean(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('escalation_reason', sa.Text(), nullable=True),
        sa.Column('suggested_reply', sa.Text(), nullable=True),
        sa.Column('raw_entities', sa.JSON(), nullable=True),
        sa.Column('is_spam', sa.Boolean(), server_default='false'),
        sa.Column('is_internal', sa.Boolean(), server_default='false'),
        sa.Column('is_security_threat', sa.Boolean(), server_default='false'),
        sa.Column('priority_score', sa.Float(), server_default='0.0'),
        sa.Column('status', sa.String(), nullable=False, server_default='Received'),
        sa.ForeignKeyConstraint(['thread_id'], ['threads.thread_id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('message_id'),
    )
    op.create_index('ix_emails_message_id', 'emails', ['message_id'])
    op.create_index('ix_emails_sender', 'emails', ['sender'])
    op.create_index('ix_emails_thread_id', 'emails', ['thread_id'])
    op.create_index('ix_emails_timestamp', 'emails', ['timestamp'])

    # actions
    op.create_table(
        'actions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('email_id', sa.String(), nullable=False),
        sa.Column('agent_reasoning_log', sa.JSON(), nullable=True),
        sa.Column('action_type', sa.String(), nullable=True),
        sa.Column('proposed_content', sa.Text(), nullable=True),
        sa.Column('is_approved', sa.Boolean(), server_default='false'),
        sa.Column('approved_by', sa.String(), nullable=True),
        sa.Column('executed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['email_id'], ['emails.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_actions_email_id', 'actions', ['email_id'])

    # knowledge_chunks
    op.create_table(
        'knowledge_chunks',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('source_doc', sa.String(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('chunk_text', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_knowledge_chunks_source_doc', 'knowledge_chunks', ['source_doc'])

    # web_intelligence_cache
    op.create_table(
        'web_intelligence_cache',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('source_url', sa.String(), nullable=False),
        sa.Column('target_entity', sa.String(), nullable=False),
        sa.Column('scraped_data', sa.JSON(), nullable=True),
        sa.Column('scraped_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_web_cache_target_entity', 'web_intelligence_cache', ['target_entity'])
    op.create_index('ix_web_cache_expires_at', 'web_intelligence_cache', ['expires_at'])

    # audit_log
    op.create_table(
        'audit_log',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('entity_type', sa.String(), nullable=False),
        sa.Column('entity_id', sa.String(), nullable=False),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('performed_by', sa.String(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('diff', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_audit_entity_type', 'audit_log', ['entity_type'])
    op.create_index('ix_audit_entity_id', 'audit_log', ['entity_id'])
    op.create_index('ix_audit_timestamp', 'audit_log', ['timestamp'])


def downgrade() -> None:
    op.drop_table('audit_log')
    op.drop_table('web_intelligence_cache')
    op.drop_table('knowledge_chunks')
    op.drop_table('actions')
    op.drop_table('emails')
    op.drop_table('threads')
    op.drop_table('contacts')