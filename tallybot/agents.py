"""Tallybot agent list.

Main idea around tallybot agents is to utilise simple orchestration,
where there is one main agent that must be aware of all other agents and
their capabilities.

Main agent routes tasks as tools to other agents, however other agents
always might move back to main agent if they can't resolve the task.

Main agent can be also considered as a triage agent.
"""

from zoozl.agentgear import BaseAgent, FunctionSchema

from agents import Agent


TallyBotTransfer = FunctionSchema(
    name="transfer_to_Tallybot", description="Transfer to tallybot."
)


class PrivateIncome(BaseAgent):
    """Agent is responsible for handling private income related tasks."""

    instructions = (
        "You book private income."
        "Always answer in sentence or less."
        "Follow the following routine with user.\n"
        "1. Ask for the data.\n"
        " - unless the user has provided it already.\n"
        "2. Book the data with the tool.\n"
        " - unless user wants to do something else.\n"
        "3. Once you have booked the data with your tool, you can transfer to tallybot."
    )
    functions = (
        FunctionSchema(
            name="do_private_income",
            description="book private income entries",
            parameters=[
                {
                    "type": "string",
                    "name": "date",
                    "description": "ISO date of the entry",
                },
                {
                    "type": "number",
                    "name": "amount",
                    "description": "Amount of the entry",
                },
                {
                    "type": "string",
                    "name": "partner",
                    "description": "Name of the partner",
                },
            ],
        ),
        TallyBotTransfer,
    )


class Tallybot(BaseAgent):
    """Responsible for routing tasks to other agents."""

    instructions = (
        "Your name is tallybot. Always be very brief."
        "Your main purpose is to quickly help user to execute any tasks."
        "Tasks can be executed by other agents."
        "If there is no agent that can execute particular task,"
        "apologise that you can't complete it and wait for other tasks."
        "Immediately when you know which task to handle execute it."
    )
    agents = (PrivateIncome,)


tallybot = Agent(
    name="Tallybot",
    instructions=Tallybot.instructions,
)
