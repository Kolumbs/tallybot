"""Tallybot plugin to zoozl server."""

import datetime

from agents import (
    set_default_openai_key,
    Runner,
    SQLiteSession,
    RunContextWrapper,
    RunConfig,
    TResponseInputItem,
)
from zoozl.chatbot import Interface, Package, InterfaceRoot

from . import workers
import logging

log = logging.getLogger(__name__)


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
        attachments = [
            workers.FileContext(
                binary=i.binary,
                media_type=i.media_type,
                filename=i.filename,
            )
            for i in package.last_message.parts
            if i.binary
        ]
        context = RunContextWrapper(
            workers.TallybotContext(
                conf=self.conf["tallybot"],
                memory=self.memory,
                conversation=package.conversation,
                attachments=attachments,
            )
        )
        run = await Runner.run(
            self.assistant_map["tallybot"],
            [
                {"role": "user", "content": package.last_message.text},
                {
                    "role": "system",
                    "content": f"Time: {datetime.datetime.now().isoformat()}\n"
                    f"Attachments:{len(attachments)}.",
                },
            ],
            run_config=RunConfig(session_input_callback=input_callable),
            session=SQLiteSession(package.talker, self.db_path),
            context=context.context,
        )
        package.callback(run.final_output)


def input_callable(
    history: list[TResponseInputItem], new: list[TResponseInputItem]
) -> list[TResponseInputItem]:
    """Input callable to pass context."""
    log.warning("HISTORY %s", history)
    return history + new
