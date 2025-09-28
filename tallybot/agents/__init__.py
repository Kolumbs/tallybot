"""Tallybot agent list.

Main idea around tallybot agents is to utilise simple orchestration,
where there is one main agent that must be aware of all other agents and
their capabilities.

Main agent routes tasks as tools to other agents, however other agents
always might move back to main agent if they can't resolve the task.

Main agent can be also considered as a triage agent.

Usage of agent:
    >>> import asyncio
    >>> from agents import Runner
    >>> import tallybot.agents
    >>> run = await Runner.run(tallybot.agents.tallybot, "Help me with my accounting")
    >>> print(run.final_output)
"""

from .main import tallybot


__all__ = ["tallybot"]
