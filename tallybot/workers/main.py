"""Tallybot main agent."""

import pydantic
from agents import Agent, function_tool, RunContextWrapper
from .base import TallybotContext
from zoozl.agentgear import BaseAgent, FunctionSchema

from . import invoicing, master


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


TALLYBOT_PROMPT1 = """
# Role and Objective
- Your name is tallybot. Your purpose is to efficiently help users execute tasks, prioritizing speed and brevity.

# Instructions
- Begin with a concise checklist (3-7 bullets) outlining the conceptual steps you will take before proceeding with any substantive task.
- Always respond very briefly.
- As soon as you identify a task to handle, execute it immediately.
- Prefer to delegate execution to other agents whenever possible.
- Before delegating or executing any action, briefly state the purpose in one line.
- After executing or delegating a task, validate the result in 1-2 lines and decide whether to proceed or self-correct based on the outcome.
- If no agent can execute the requested task, apologize that you cannot complete it and wait for new tasks.
# Output Format
- Keep all responses concise and direct.
# Stop Conditions
- Only stop after the task is executed or if it's clear that no agent can fulfill the request."
"""

TALLYBOT_PROMPT2 = (
    "Your name is tallybot. Always be very brief."
    "Your main purpose is to quickly help user to execute any tasks."
    "Tasks can be executed by other agents."
    "If there is no agent that can execute particular task,"
    "apologise that you can't complete it and wait for other tasks."
    "Immediately when you know which task to handle execute it."
    "Prioritise delegation, speed and brevity"
)


class Attachments(pydantic.BaseModel):
    """Data for creating new partner."""

    name: str = pydantic.Field(
        description="Partner name as shown in accounting system"
    )
    other_names: list[str] = pydantic.Field(
        description="Other names or aliases for the partner"
    )


tallybot = Agent(
    name="Tallybot",
    instructions=TALLYBOT_PROMPT2,
    tools=[
        invoicing.accounts_payable_clerk.as_tool(
            tool_name="accounts_payable_clerk",
            tool_description="You can book invoices with this tool.",
        ),
        master.do_register_partner,
    ],
)
