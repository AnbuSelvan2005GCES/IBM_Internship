"""
memory.py
The Memory component. Wraps the database's conversation_history table so
the agent can (a) recall recent turns of a session and (b) record new ones,
without needing to know about SQLite directly.

Memory is keyed by session_id — each student/conversation gets their own
independent history. A frontend or client is expected to generate and
persist a session_id (e.g. a UUID stored in the browser) and send it with
every request.
"""

from database import add_message, get_conversation_history, clear_session


class ConversationMemory:
    def __init__(self, max_turns: int = 6):
        # max_turns = number of *exchanges* (user+assistant pairs) to recall,
        # so we pull twice as many raw messages.
        self.max_messages = max_turns * 2

    def remember_user_message(self, session_id: str, content: str):
        add_message(session_id, "user", content)

    def remember_assistant_message(self, session_id: str, content: str):
        add_message(session_id, "assistant", content)

    def get_recent_history(self, session_id: str):
        """Return recent messages as a list of {role, content} dicts."""
        rows = get_conversation_history(session_id, limit=self.max_messages)
        return [{"role": r["role"], "content": r["content"]} for r in rows]

    def format_history_for_prompt(self, session_id: str) -> str:
        """Render recent history as plain text to inject into the LLM prompt."""
        history = self.get_recent_history(session_id)
        if not history:
            return "No prior conversation in this session."

        lines = []
        for turn in history:
            speaker = "Student" if turn["role"] == "user" else "Assistant"
            lines.append(f"{speaker}: {turn['content']}")
        return "\n".join(lines)

    def clear(self, session_id: str):
        clear_session(session_id)