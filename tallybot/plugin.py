"""Tallybot plugin to zoozl server."""

import datetime
import json

from agents import (
    set_default_openai_key,
    Runner,
    SQLiteSession,
    RunContextWrapper,
    RunConfig,
    TResponseInputItem,
)
from zoozl.chatbot import (
    Interface,
    Package,
    InterfaceRoot,
    Message,
    MessagePart,
)

from . import workers
import logging

log = logging.getLogger(__name__)


class TallybotSession(SQLiteSession):
    """Tallybot session that limits message history."""

    window_size = 10

    def __init__(self, session_id, db_path):
        super().__init__(session_id=session_id, db_path=db_path)

    async def get_items(self, limit: int | None = None):
        """Override to only return the last N messages."""
        if limit is None:
            limit = self.window_size
        return await super().get_items(limit=limit)


class TallyBot(Interface):
    """Tallybot interface to zoozl chatbot."""

    aliases = {"tallybot", "help", "greet"}

    def load(self, root: InterfaceRoot):
        """Load OpenAI agents."""
        try:
            api_key = root.conf["tallybot"]["openai_api_key"]
            set_default_openai_key(api_key)
        except KeyError:
            raise RuntimeError(
                "Tallybot requires openAI api key to work!"
            ) from None
        self.assistant_map = {"tallybot": workers.tallybot}
        self.conf = root.conf
        self.db_path = self.conf["tallybot"]["database"]
        self.memory = root.memory

    async def consume(self, package: Package):
        """Handle incoming message."""
        attachments = len(package.get_attachments(5, False))
        context = RunContextWrapper(
            workers.TallybotContext(
                conf=self.conf["tallybot"],
                memory=self.memory,
                package=package,
                message_parts=[],
            )
        )
        run = await Runner.run(
            self.assistant_map["tallybot"],
            [
                {"role": "user", "content": package.last_message.text},
                {
                    "role": "system",
                    "content": f"Time: {datetime.datetime.now().isoformat()}\n"
                    f"Attachments:{attachments}.",
                },
            ],
            run_config=RunConfig(session_input_callback=input_callable),
            session=TallybotSession(package.talker, self.db_path),
            context=context.context,
        )
        msg = Message(author="agent")
        if context.context.message_parts:
            for f in context.context.message_parts:
                msg.parts.append(f)
        msg.parts.append(MessagePart(text=run.final_output))
        package.callback(msg)


def input_callable(
    history: list[TResponseInputItem], new: list[TResponseInputItem]
) -> list[TResponseInputItem]:
    """Input callable to pass context."""
    log.warning("HISTORY %s", json.dumps(history, indent=2))
    log.warning("NEW %s", json.dumps(new, indent=2))
    return history + new
