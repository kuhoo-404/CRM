"""
Agent Tools
===========
Each tool is a plain Python function. The agent loop calls them by name.
Tools interact with the DB and RAG service — they have side effects.

All tools return a string (the "Observation" the agent sees).
"""
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


class AgentTools:
    """
    Bundles all tool implementations.
    Injected with db session and services at construction time.
    """

    def __init__(self, db, rag_service, groq_client=None):
        self.db = db
        self.rag = rag_service
        self.groq = groq_client

    # ── Tool registry ─────────────────────────────────────────────────────────

    def get_tool(self, name: str):
        """Return the tool function by name."""
        registry = {
            "search_knowledge_base": self.search_knowledge_base,
            "get_thread_history": self.get_thread_history,
            "get_contact_profile": self.get_contact_profile,
            "check_account_status": self.check_account_status,
            "draft_reply": self.draft_reply,
            "escalate_to_human": self.escalate_to_human,
            "flag_for_legal": self.flag_for_legal,
            "create_internal_ticket": self.create_internal_ticket,
            "send_auto_reply": self.send_auto_reply,
        }
        return registry.get(name)

    # ── Tool 1: search_knowledge_base ─────────────────────────────────────────

    def search_knowledge_base(self, query: str) -> str:
        try:
            results = self.rag.retrieve(query, top_k=3)
            if not results:
                return "No relevant knowledge base entries found."
            parts = []
            for i, r in enumerate(results, 1):
                # Handle both key naming conventions
                source = r.get("source_doc", r.get("source", "unknown"))
                score = r.get("similarity_score", r.get("score", 0.0))
                text = r.get("chunk_text", r.get("text", ""))
                parts.append(
                    f"[{i}] Source: {source} (similarity: {score:.2f})\n{text}"
                )
            return "\n\n".join(parts)
        except Exception as e:
             logger.error(f"search_knowledge_base failed: {e}")
        return f"Knowledge base search failed: {str(e)}"

    # ── Tool 2: get_thread_history ────────────────────────────────────────────

    def get_thread_history(self, sender_email: str) -> str:
        """Retrieve all emails from this sender, ordered by time."""
        try:
            from app.models.email import Email
            emails = (
                self.db.query(Email)
                .filter(Email.sender == sender_email)
                .order_by(Email.timestamp.asc())
                .all()
            )
            if not emails:
                return f"No email history found for {sender_email}."
            parts = []
            for e in emails:
                ts = e.timestamp.strftime("%Y-%m-%d %H:%M UTC") if e.timestamp else "unknown time"
                sentiment_info = f" | sentiment: {e.sentiment_score:.2f}" if e.sentiment_score is not None else ""
                parts.append(
                    f"[{ts}] {e.message_id} — Subject: {e.subject}\n"
                    f"  Category: {e.category.value if e.category else 'unclassified'}"
                    f"{sentiment_info}\n"
                    f"  Body: {(e.body or '')[:200]}{'...' if len(e.body or '') > 200 else ''}"
                )
            return f"Thread history for {sender_email} ({len(emails)} emails):\n\n" + "\n\n".join(parts)
        except Exception as e:
            logger.error(f"get_thread_history failed: {e}")
            return f"Failed to retrieve thread history: {str(e)}"

    # ── Tool 3: get_contact_profile ───────────────────────────────────────────

    def get_contact_profile(self, email: str) -> str:
        """Fetch CRM profile: VIP status, account value, churn risk score."""
        try:
            from app.models.contact import Contact
            from app.models.thread import Thread
            contact = self.db.query(Contact).filter(Contact.email == email).first()
            if not contact:
                return f"No CRM profile found for {email}. This may be a new contact."
            thread_count = (
                self.db.query(Thread).filter(Thread.sender_email == email).count()
            )
            return (
                f"Contact Profile: {email}\n"
                f"  Name: {contact.name or 'Unknown'}\n"
                f"  Company: {contact.company or 'Unknown'}\n"
                f"  Status: {contact.status.value}\n"
                f"  Account Value: ${contact.account_value:,.2f}\n"
                f"  Churn Risk Score: {contact.churn_risk_score:.2f} / 1.0\n"
                f"  Active Threads: {thread_count}\n"
                f"  Last Contact: {contact.last_contact_at.strftime('%Y-%m-%d') if contact.last_contact_at else 'Never'}"
            )
        except Exception as e:
            logger.error(f"get_contact_profile failed: {e}")
            return f"Failed to retrieve contact profile: {str(e)}"

    # ── Tool 4: check_account_status ──────────────────────────────────────────

    def check_account_status(self, email: str) -> str:
        """Check billing status, subscription tier. Stub — extend with real billing data."""
        try:
            from app.models.contact import Contact
            contact = self.db.query(Contact).filter(Contact.email == email).first()
            if not contact:
                return f"No account found for {email}."

            # In a real system this would hit your billing DB/Stripe
            # For this project we infer tier from account_value as a reasonable heuristic
            value = contact.account_value
            if value >= 50000:
                tier = "Enterprise"
                rate_limit = "5,000 req/min"
            elif value >= 10000:
                tier = "Pro"
                rate_limit = "2,000 req/min"
            elif value >= 1000:
                tier = "Standard"
                rate_limit = "1,000 req/min"
            else:
                tier = "Starter"
                rate_limit = "100 req/min"

            churn_flag = ""
            if contact.churn_risk_score > 0.7:
                churn_flag = " ⚠️ HIGH CHURN RISK"

            return (
                f"Account Status: {email}\n"
                f"  Subscription Tier: {tier}{churn_flag}\n"
                f"  API Rate Limit: {rate_limit}\n"
                f"  Account Value: ${value:,.2f}\n"
                f"  Status: {contact.status.value}\n"
                f"  Churn Risk: {contact.churn_risk_score:.2f}"
            )
        except Exception as e:
            logger.error(f"check_account_status failed: {e}")
            return f"Failed to check account status: {str(e)}"

    # ── Tool 5: draft_reply ───────────────────────────────────────────────────

    def draft_reply(self, context: str, tone: str = "professional", policy_refs: list = None) -> str:
        """Generate a contextual reply citing specific policies."""
        try:
            from app.agent.prompts import DRAFT_REPLY_PROMPT
            if policy_refs is None:
                policy_refs = []

            prompt = DRAFT_REPLY_PROMPT.format(
                tone=tone,
                policy_refs=", ".join(policy_refs) if policy_refs else "general best practices",
                context=context,
            )

            if self.groq:
                        response = self.groq.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[{"role": "user", "content": prompt}],
                            max_tokens=512,
                        )
                        draft = response.choices[0].message.content.strip()

            return f"Draft reply generated:\n\n{draft}"
        except Exception as e:
            logger.error(f"draft_reply failed: {e}")
            return f"Failed to generate draft reply: {str(e)}"

    # ── Tool 6: escalate_to_human ─────────────────────────────────────────────

    def escalate_to_human(
        self,
        email_id: str,
        reason: str,
        priority: str = "High",
    ) -> str:
        """Route email to human with a pre-filled brief. Updates DB status."""
        try:
            from app.models.email import Email, EmailStatus, UrgencyLevel
            from app.models.thread import Thread, ThreadStatus
            from app.models.audit_log import AuditLog

            email = self.db.query(Email).filter(Email.id == email_id).first()
            if not email:
                # Try by message_id as fallback
                email = self.db.query(Email).filter(Email.message_id == email_id).first()
            if not email:
                return f"Email {email_id} not found — escalation recorded in reasoning log only."

            email.status = EmailStatus.escalated
            email.requires_human = True
            email.escalation_reason = reason

            # Update thread status
            thread = self.db.query(Thread).filter(Thread.thread_id == email.thread_id).first()
            if thread:
                thread.status = ThreadStatus.escalated

            # Audit
            audit = AuditLog(
                id=str(uuid.uuid4()),
                entity_type="email",
                entity_id=email.id,
                action="escalated_to_human",
                performed_by="agent",
                diff={"reason": reason, "priority": priority},
            )
            self.db.add(audit)
            self.db.commit()

            return (
                f"✅ Escalated to human team.\n"
                f"  Email: {email_id}\n"
                f"  Priority: {priority}\n"
                f"  Reason: {reason}\n"
                f"  Status updated to: Escalated"
            )
        except Exception as e:
            self.db.rollback()
            logger.error(f"escalate_to_human failed: {e}")
            return f"Escalation recorded but DB update failed: {str(e)}"

    # ── Tool 7: flag_for_legal ────────────────────────────────────────────────

    def flag_for_legal(self, email_id: str, issue_type: str) -> str:
        """Route legal threats, GDPR requests, and security threats to legal team."""
        try:
            from app.models.email import Email, EmailStatus
            from app.models.audit_log import AuditLog

            email = self.db.query(Email).filter(
                (Email.id == email_id) | (Email.message_id == email_id)
            ).first()

            if email:
                email.status = EmailStatus.escalated
                email.requires_human = True
                email.escalation_reason = f"LEGAL FLAG: {issue_type}"

                audit = AuditLog(
                    id=str(uuid.uuid4()),
                    entity_type="email",
                    entity_id=email.id,
                    action="flagged_for_legal",
                    performed_by="agent",
                    diff={"issue_type": issue_type},
                )
                self.db.add(audit)
                self.db.commit()

            return (
                f"🚨 Flagged for Legal team.\n"
                f"  Email: {email_id}\n"
                f"  Issue type: {issue_type}\n"
                f"  Routed to: legal@ourplatform.com\n"
                f"  Auto-reply: BLOCKED — legal review required first"
            )
        except Exception as e:
            self.db.rollback()
            logger.error(f"flag_for_legal failed: {e}")
            return f"Legal flag recorded in reasoning log. DB update failed: {str(e)}"

    # ── Tool 8: create_internal_ticket ────────────────────────────────────────

    def create_internal_ticket(self, title: str, body: str, assignee: str) -> str:
        """Create a support/engineering ticket. Stub — wire to Jira/Linear in production."""
        ticket_id = f"TKT-{str(uuid.uuid4())[:8].upper()}"
        try:
            from app.models.audit_log import AuditLog
            audit = AuditLog(
                id=str(uuid.uuid4()),
                entity_type="ticket",
                entity_id=ticket_id,
                action="ticket_created",
                performed_by="agent",
                diff={"title": title, "assignee": assignee, "body": body[:500]},
            )
            self.db.add(audit)
            self.db.commit()
        except Exception as e:
            logger.warning(f"Ticket audit log failed: {e}")

        return (
            f"✅ Internal ticket created.\n"
            f"  Ticket ID: {ticket_id}\n"
            f"  Title: {title}\n"
            f"  Assigned to: {assignee}\n"
            f"  Body preview: {body[:100]}..."
        )

    # ── Tool 9: send_auto_reply ───────────────────────────────────────────────

    def send_auto_reply(self, email_id: str, draft_text: str) -> str:
        """
        Approve and send an auto-reply.
        GUARD: will refuse if email is Critical, spam, security, or legal threat.
        """
        try:
            from app.models.email import Email, EmailStatus, UrgencyLevel
            from app.models.action import Action, ActionType
            from app.models.audit_log import AuditLog

            email = self.db.query(Email).filter(
                (Email.id == email_id) | (Email.message_id == email_id)
            ).first()

            if email:
                # Safety guard — never auto-reply to these
                if email.urgency == UrgencyLevel.critical:
                    return "❌ BLOCKED: Cannot auto-reply to Critical urgency email. Escalate to human."
                if email.is_spam:
                    return "❌ BLOCKED: Cannot auto-reply to spam email."
                if email.is_security_threat:
                    return "❌ BLOCKED: Cannot auto-reply to security threat."
                if email.escalation_reason and "LEGAL FLAG" in email.escalation_reason:
                    return "❌ BLOCKED: Cannot auto-reply to legally flagged email."

                email.status = EmailStatus.replied

                action = Action(
                    id=str(uuid.uuid4()),
                    email_id=email.id,
                    action_type=ActionType.auto_reply,
                    proposed_content=draft_text,
                    is_approved=True,
                    approved_by="agent",
                    executed_at=datetime.now(timezone.utc),
                )
                self.db.add(action)

                audit = AuditLog(
                    id=str(uuid.uuid4()),
                    entity_type="email",
                    entity_id=email.id,
                    action="auto_reply_sent",
                    performed_by="agent",
                    diff={"reply_preview": draft_text[:200]},
                )
                self.db.add(audit)
                self.db.commit()

            return (
                f"✅ Auto-reply sent.\n"
                f"  Email: {email_id}\n"
                f"  Reply preview: {draft_text[:150]}..."
            )
        except Exception as e:
            self.db.rollback()
            logger.error(f"send_auto_reply failed: {e}")
            return f"Auto-reply failed: {str(e)}"