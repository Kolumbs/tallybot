"""Tallybot plugin to zoozl server."""

from agents import set_default_openai_key, Runner, SQLiteSession
from zoozl.chatbot import Interface, Package, InterfaceRoot

from . import agents


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
        self.assistant_map = {"tallybot": agents.tallybot}
        self.db_path = root.conf["tallybot"]["database"]

    async def consume(self, package: Package):
        """Handle incoming message."""
        run = await Runner.run(
            self.assistant_map["tallybot"],
            package.last_message.text,
            session=SQLiteSession(package.talker, self.db_path),
        )
        package.callback(run.final_output)
