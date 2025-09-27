"""Tallybot plugin to zoozl server."""

import time

from agents import set_default_openai_key, Runner, SQLiteSession
from zoozl import agentgear, utils
from zoozl.chatbot import Interface, Package, InterfaceRoot

from . import agents, brain



class Handler(agentgear.StreamHandler):
    """Handler of the single stream."""

    def handle_event(self, event):
        """Handle event."""
        print("Event:", event.event)

    def on_requires_action(self, action):
        """Handle action."""
        print("Action:", action)
        self.client.beta.threads.runs.submit_tool_outputs(
            self.current_run.id,
            thread_id=self.current_run.thread_id,
            tool_outputs=[
                {
                    "tool_call_id": tool_call.id,
                    "output": output,
                }
            ],
        )


    def on_tool_call_created(self, tool_call):
        """Handle tool call."""
        if tool_call.type == "function":
            if tool_call.function.name.startswith("transfer_to_"):
                assistant_id = self.assistant_map[tool_call.function.name[12:]]
                thread = self.client.beta.threads.create()
                self.client.beta.threads.messages.create(
                    thread.id,
                    role="user",
                    content=self.package.last_message.text,
                )
                make_a_run(
                    self.client,
                    thread.id,
                    assistant_id,
                    self.assistant_map,
                    self.package,
                    self.context
                )
                self.package.conversation.data["openai_thread_id"] = thread.id
                self.package.conversation.data["openai_assistant_id"] = assistant_id
                output = "Transfer complete"
            else:
                msg, attach, fname = brain.do_task(
                    self.context.conf["tallybot"],
                    self.context.memory,
                    tool_call.function.name,
                    tool_call.function.arguments,
                    None
                )
                output = msg

def make_a_run(
    assistant_id: str,
    assistant_map: dict,
    package: Package,
    context: InterfaceRoot
) -> None:
    """Make a single run."""
    with client.beta.threads.runs.stream(
        thread_id=thread_id,
        assistant_id=assistant_id,
        timeout=10,
        event_handler=Handler(client, thread_id, assistant_map, package, context),
    ) as stream:
        stream.until_done()
        run = stream.get_final_run()
        while run.completed_at is None:
            if run.created_at < int(time.time()) - 10:
                stream.on_timeout()
                run = client.beta.threads.runs.cancel(run.id, thread_id=thread_id)
                checks = 0
                while run.cancelled_at is None and checks < 10:
                    time.sleep(3)
                    run = client.beta.threads.runs.poll(run.id, thread_id=thread_id)
                    checks += 1
                break
            else:
                time.sleep(3)
                run = client.beta.threads.runs.poll(run.id, thread_id=thread_id)


class TallyBot(Interface):
    """Tallybot interface to zoozl chatbot."""

    aliases = {"tallybot", "help", "greet", "cancel"}

    def load(self, root: InterfaceRoot):
        """Load OpenAI agents."""
        set_default_openai_key(root.conf["tallybot"]["openai_api_key"])
        try:
            api_key = root.conf["tallybot"]["openai_api_key"]
        except KeyError:
            raise RuntimeError(
                "Tallybot requires openAI api key to work!"
            ) from None
        self.assistant_map = {"Tallybot": agents.tallybot}
        self.db_path = root.conf["tallybot"]["database"]

    def consume(self, package: Package):
        """Handle incoming message."""
        session = SQLiteSession(package.talker, self.db_path)
        run = Runner.run_sync(self.assistant_map["Tallybot"], package.last_message.text, session=session)
        package.callback(run.final_output)
