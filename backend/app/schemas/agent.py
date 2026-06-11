"""
ReAct Agent Loop
================
Implements the Thought → Action → Observation cycle.

Flow:
  1. Build context (email + thread history + RAG chunks)
  2. Call Gemini with ReAct system prompt
  3. Parse response → extract tool calls
  4. Dispatch tool calls one by one
  5. Feed observations back to Gemini for next step
  6. Repeat up to MAX_STEPS
  7. Store full reasoning trace in actions table
  8. Return structured result

Key guarantees:
  - Never auto-replies to Critical / spam / security / legal emails
  - Always escalates if unresolved after MAX_STEPS
  - Full reasoning trace stored even on failure
  - Dry-run mode: plans without executing side-effect tools
"""
import uuid
import json
import logging
from datetime import datetime, timezone
from typing import Optional

import google.generativeai as genai

from app.config import get_settings
from app.agent.prompts import REACT_SYSTEM_PROMPT, REACT_USER_TEMPLATE
from app.agent.tools import AgentTools

logger = logging.getLogger(__name__)
settings = get_settings()

MAX_STEPS = 6

# Tools that have side effects — blocked in dry-run mode
SIDE_EFFECT_TOOLS = {
    "escalate_to_human",
    "flag_for_legal",
    "create_internal_ticket",
    "send_auto_reply",
}

# These email types must NEVER receive an auto-reply — enforced here too
NEVER_AUTO_REPLY_CONDITIONS = {
    "is_spam": True,
    "is_security_threat": True,
}


class AgentLoop:

    def __init__(self, db, rag_service):
        self.db = db
        self.rag = rag_service
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel("gemini-2.0-flash")
        self.tools = AgentTools(db=db, rag_service=rag_service, gemini_model=self.model)

    # ── Public entrypoint ─────────────────────────────────────────────────────

    def run(self, email_id: str, dry_run: bool = False) -> dict:
        """
        Run the agent on a single email.
        dry_run=True → plans only, no DB writes, no sends.

        Returns a structured result dict with the full reasoning trace.
        """
        from app.models.email import Email
        from app.models.action import Action, ActionType
        from app.models.audit_log import AuditLog

        email = self.db.query(Email).filter(
            (Email.id == email_id) | (Email.message_id == email_id)
        ).first()

        if not email:
            return {
                "success": False,
                "error": f"Email not found: {email_id}",
                "reasoning_trace": [],
            }

        # ── Pre-flight safety checks ──────────────────────────────────────────
        # These are absolute — no LLM call needed, just route immediately
        if email.is_spam:
            return self._safe_exit(
                email, dry_run,
                reason="Email flagged as spam — no agent action taken",
                action_type=ActionType.ignored,
            )

        if email.is_security_threat:
            return self._handle_security_threat(email, dry_run)

        # ── Build context ─────────────────────────────────────────────────────
        thread_history = self.tools.get_thread_history(email.sender)

        rag_query = f"{email.subject or ''} {(email.body or '')[:300]}"
        rag_results = self.rag.retrieve(rag_query, top_k=3)
        rag_context = self._format_rag_context(rag_results)

        # ── Build initial prompt ──────────────────────────────────────────────
        user_message = REACT_USER_TEMPLATE.format(
            message_id=email.message_id,
            sender=email.sender,
            subject=email.subject or "(no subject)",
            timestamp=email.timestamp.strftime("%Y-%m-%d %H:%M UTC") if email.timestamp else "unknown",
            body=email.body or "(empty body)",
            thread_history=thread_history,
            rag_context=rag_context,
            category=email.category.value if email.category else "unclassified",
            urgency=email.urgency.value if email.urgency else "unknown",
            sentiment=email.sentiment.value if email.sentiment else "unknown",
            sentiment_score=email.sentiment_score if email.sentiment_score is not None else 0.0,
            requires_human=email.requires_human if email.requires_human is not None else False,
            confidence=email.confidence if email.confidence is not None else 0.0,
            is_spam=email.is_spam,
            is_security_threat=email.is_security_threat,
            is_legal=bool(email.escalation_reason and "LEGAL" in (email.escalation_reason or "")),
        )

        # ── ReAct loop ────────────────────────────────────────────────────────
        reasoning_trace = []
        conversation_history = [
            {"role": "user", "parts": [user_message]},
        ]

        final_answer = None
        action_taken = "Ignored"
        draft_reply = None
        steps_used = 0

        for step in range(MAX_STEPS):
            steps_used += 1
            logger.info(f"Agent step {step + 1}/{MAX_STEPS} for {email.message_id}")

            # Call Gemini
            try:
                raw_response = self._call_gemini(conversation_history)
            except Exception as e:
                logger.error(f"Gemini call failed on step {step + 1}: {e}")
                reasoning_trace.append({
                    "step": step + 1,
                    "thought": f"LLM call failed: {str(e)}",
                    "action": None,
                    "observation": None,
                    "error": str(e),
                })
                break

            # Parse the response
            parsed = self._parse_response(raw_response)

            if parsed is None:
                # Gemini returned unparseable output — add to trace and break
                reasoning_trace.append({
                    "step": step + 1,
                    "thought": "Failed to parse LLM response",
                    "raw_response": raw_response[:500],
                    "action": None,
                    "observation": None,
                })
                break

            # Extract steps from parsed response
            steps = parsed.get("steps", [])
            final_answer = parsed.get("final_answer")
            action_taken = parsed.get("action_taken", "Ignored")
            draft_reply = parsed.get("draft_reply")

            # Process each step in the response
            for step_data in steps:
                thought = step_data.get("thought", "")
                action_name = step_data.get("action")
                args = step_data.get("args", {})

                step_record = {
                    "step": steps_used,
                    "thought": thought,
                    "action": action_name,
                    "args": args,
                    "observation": None,
                }

                if action_name:
                    # Execute the tool (or simulate in dry-run)
                    observation = self._dispatch_tool(
                        action_name, args, email, dry_run
                    )
                    step_record["observation"] = observation

                    # Feed observation back for next iteration
                    observation_message = (
                        f"Observation from {action_name}: {observation}"
                    )
                    conversation_history.append(
                        {"role": "model", "parts": [json.dumps(parsed)]}
                    )
                    conversation_history.append(
                        {"role": "user", "parts": [
                            f"The tool returned this observation:\n{observation}\n\n"
                            f"Continue reasoning. If you have completed your task, "
                            f"provide your final_answer."
                        ]}
                    )

                reasoning_trace.append(step_record)

            # If Gemini returned a final_answer, we're done
            if final_answer:
                logger.info(f"Agent completed in {steps_used} steps for {email.message_id}")
                break

        else:
            # Exhausted MAX_STEPS without resolution — force escalation
            logger.warning(f"Agent hit MAX_STEPS ({MAX_STEPS}) for {email.message_id} — forcing escalation")
            final_answer = (
                f"Agent exhausted {MAX_STEPS} steps without full resolution. "
                f"Escalating to human with reasoning summary."
            )
            if not dry_run:
                self.tools.escalate_to_human(
                    email_id=email.id,
                    reason=f"Agent unresolved after {MAX_STEPS} steps. Last action: {action_taken}",
                    priority="High",
                )
            reasoning_trace.append({
                "step": MAX_STEPS + 1,
                "thought": "MAX_STEPS reached — forced escalation",
                "action": "escalate_to_human",
                "observation": "Escalated due to step limit",
            })
            action_taken = "Escalate"

        # ── Persist reasoning trace ───────────────────────────────────────────
        action_type_map = {
            "Auto-Reply": ActionType.auto_reply,
            "Escalate": ActionType.escalate,
            "Legal-Flag": ActionType.legal_flag,
            "Ticket-Created": ActionType.ticket_created,
            "Ignored": ActionType.ignored,
        }

        if not dry_run:
            try:
                action_record = Action(
                    id=str(uuid.uuid4()),
                    email_id=email.id,
                    agent_reasoning_log=reasoning_trace,
                    action_type=action_type_map.get(action_taken, ActionType.ignored),
                    proposed_content=draft_reply,
                    is_approved=False,
                    approved_by=None,
                )
                self.db.add(action_record)

                audit = AuditLog(
                    id=str(uuid.uuid4()),
                    entity_type="email",
                    entity_id=email.id,
                    action=f"agent_run_{'dry_run' if dry_run else 'executed'}",
                    performed_by="agent",
                    diff={
                        "steps_used": steps_used,
                        "action_taken": action_taken,
                        "final_answer": final_answer,
                        "dry_run": dry_run,
                    },
                )
                self.db.add(audit)
                self.db.commit()
            except Exception as e:
                self.db.rollback()
                logger.error(f"Failed to persist reasoning trace: {e}")

        return {
            "success": True,
            "email_id": email.id,
            "message_id": email.message_id,
            "dry_run": dry_run,
            "steps_used": steps_used,
            "action_taken": action_taken,
            "final_answer": final_answer,
            "draft_reply": draft_reply,
            "reasoning_trace": reasoning_trace,
            "rag_chunks_used": [
                {"source": r["source_doc"], "score": r["score"]}
                for r in rag_results
            ],
        }

    # ── Private helpers ───────────────────────────────────────────────────────

    def _call_gemini(self, conversation_history: list) -> str:
        """Call Gemini with the full conversation history."""
        chat = self.model.start_chat(history=conversation_history[:-1])
        last_message = conversation_history[-1]["parts"][0]

        # Prepend system prompt to first call
        if len(conversation_history) == 1:
            full_message = f"{REACT_SYSTEM_PROMPT}\n\n{last_message}"
        else:
            full_message = last_message

        response = chat.send_message(full_message)
        return response.text

    def _parse_response(self, raw: str) -> Optional[dict]:
        """
        Parse Gemini's JSON response.
        Handles markdown code fences and minor formatting issues.
        """
        try:
            # Strip markdown fences if present
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                # Remove first line (```json or ```) and last line (```)
                cleaned = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
            return json.loads(cleaned)
        except json.JSONDecodeError:
            # Try extracting JSON from within the text
            try:
                start = raw.find("{")
                end = raw.rfind("}") + 1
                if start >= 0 and end > start:
                    return json.loads(raw[start:end])
            except Exception:
                pass
            logger.warning(f"Could not parse agent response: {raw[:300]}")
            return None

    def _dispatch_tool(
        self,
        tool_name: str,
        args: dict,
        email,
        dry_run: bool,
    ) -> str:
        """
        Call the named tool with the given args.
        In dry-run mode, side-effect tools are simulated.
        """
        # Safety: block send_auto_reply on protected email types
        if tool_name == "send_auto_reply":
            if email.is_spam:
                return "BLOCKED: Cannot auto-reply to spam"
            if email.is_security_threat:
                return "BLOCKED: Cannot auto-reply to security threat"
            if email.urgency and email.urgency.value == "Critical":
                return "BLOCKED: Cannot auto-reply to Critical urgency email"
            if email.escalation_reason and "LEGAL" in (email.escalation_reason or ""):
                return "BLOCKED: Cannot auto-reply to legally flagged email"

        if dry_run and tool_name in SIDE_EFFECT_TOOLS:
            return f"[DRY RUN] Would call {tool_name}({args}) — not executed"

        tool_fn = self.tools.get_tool(tool_name)
        if not tool_fn:
            return f"Unknown tool: {tool_name}"

        try:
            # Call the tool with unpacked args
            return tool_fn(**args)
        except TypeError as e:
            return f"Tool {tool_name} called with wrong args: {e}"
        except Exception as e:
            logger.error(f"Tool {tool_name} failed: {e}")
            return f"Tool {tool_name} failed: {str(e)}"

    def _format_rag_context(self, results: list) -> str:
        if not results:
            return "No relevant policy context found."
        parts = []
        for r in results:
            parts.append(f"[{r['source_doc']} | similarity: {r['score']:.2f}]\n{r['text']}")
        return "\n\n---\n\n".join(parts)

    def _safe_exit(self, email, dry_run: bool, reason: str, action_type) -> dict:
        """Quick exit for emails that need no agent action."""
        from app.models.action import Action
        if not dry_run:
            try:
                action = Action(
                    id=str(uuid.uuid4()),
                    email_id=email.id,
                    agent_reasoning_log=[{"thought": reason, "action": "none", "observation": "skipped"}],
                    action_type=action_type,
                    is_approved=True,
                    approved_by="agent",
                    executed_at=datetime.now(timezone.utc),
                )
                self.db.add(action)
                self.db.commit()
            except Exception as e:
                self.db.rollback()
        return {
            "success": True,
            "email_id": email.id,
            "message_id": email.message_id,
            "dry_run": dry_run,
            "steps_used": 0,
            "action_taken": "Ignored",
            "final_answer": reason,
            "draft_reply": None,
            "reasoning_trace": [{"thought": reason, "action": "none", "observation": "skipped"}],
            "rag_chunks_used": [],
        }

    def _handle_security_threat(self, email, dry_run: bool) -> dict:
        """
        Hard-coded handler for ransomware / security threats.
        No LLM involved — route immediately to security queue.
        NEVER auto-reply.
        """
        from app.models.action import Action, ActionType
        from app.models.audit_log import AuditLog

        reasoning_trace = [
            {
                "step": 1,
                "thought": (
                    "This email is flagged as a security threat (ransomware/extortion/suspicious login). "
                    "Per absolute rules: route to security queue immediately, NEVER auto-reply, "
                    "flag_for_legal, notify CISO. No LLM reasoning needed — this is deterministic."
                ),
                "action": "flag_for_legal",
                "args": {"email_id": email.message_id, "issue_type": "Security threat / ransomware / extortion"},
                "observation": None,
            },
            {
                "step": 2,
                "thought": "Escalate to security team with Critical priority.",
                "action": "escalate_to_human",
                "args": {
                    "email_id": email.message_id,
                    "reason": "SECURITY THREAT: Ransomware/extortion email. CISO notified. DO NOT REPLY.",
                    "priority": "Critical",
                },
                "observation": None,
            },
        ]

        if not dry_run:
            obs1 = self.tools.flag_for_legal(
                email_id=email.id,
                issue_type="Security threat / ransomware / extortion",
            )
            reasoning_trace[0]["observation"] = obs1

            obs2 = self.tools.escalate_to_human(
                email_id=email.id,
                reason="SECURITY THREAT: Ransomware/extortion. CISO notified. DO NOT REPLY.",
                priority="Critical",
            )
            reasoning_trace[1]["observation"] = obs2

            try:
                action = Action(
                    id=str(uuid.uuid4()),
                    email_id=email.id,
                    agent_reasoning_log=reasoning_trace,
                    action_type=ActionType.legal_flag,
                    proposed_content=None,   # NEVER generate a reply
                    is_approved=True,
                    approved_by="agent",
                    executed_at=datetime.now(timezone.utc),
                )
                self.db.add(action)
                self.db.commit()
            except Exception as e:
                self.db.rollback()
                logger.error(f"Failed to save security threat action: {e}")

        return {
            "success": True,
            "email_id": email.id,
            "message_id": email.message_id,
            "dry_run": dry_run,
            "steps_used": 2,
            "action_taken": "Legal-Flag",
            "final_answer": (
                "Security threat detected. Flagged for legal, escalated to security team "
                "with Critical priority. Auto-reply BLOCKED. CISO notification sent."
            ),
            "draft_reply": None,  # Absolute: never draft a reply to attackers
            "reasoning_trace": reasoning_trace,
            "rag_chunks_used": [],
        }