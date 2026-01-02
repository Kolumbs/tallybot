"""Tallybot workers.

Main idea around tallybot agents is to utilise simple orchestration,
where there is one main agent that must be aware of all other agents and
their capabilities.

Main agent can be also considered as a triage agent.

Usage of agent:
    >>> import asyncio
    >>> from agents import Runner
    >>> import tallybot.agents
    >>> run = await Runner.run(tallybot.agents.tallybot, "Help me with my accounting")
    >>> print(run.final_output)


Module structure is organised similar to accounting domains.

+-------------+----------------------------------------------------------+
| Module      | Responsibility                                           |
+-------------+----------------------------------------------------------+
| banking     | Bank facts and imports: statement parsing                |
+-------------+----------------------------------------------------------+
| base        | Shared primitives and helpers (common agent tooling)     |
+-------------+----------------------------------------------------------+
| financials  | Financial reporting: P&L, discrepancy reports            |
+-------------+----------------------------------------------------------+
| journal     | General Journal: access to GL for direct transactions    |
+-------------+----------------------------------------------------------+
| main        | High-level orchestration and entry point for interaction |
|             | with agents                                              |
+-------------+----------------------------------------------------------+
| master      | Handling of master data: partners, documents             |
+-------------+----------------------------------------------------------+
| payables    | Accounts Payable (AP): supplier invoices                 |
+-------------+----------------------------------------------------------+
| receivables | Accounts Receivable (AR): customer invoices              |
+-------------+----------------------------------------------------------+

"""

from .base import TallybotContext
from .main import tallybot


__all__ = ["tallybot", "TallybotContext"]
