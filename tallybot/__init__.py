"""Tallybot."""

import os

import membank
from rapidfuzz.fuzz import token_set_ratio
from rapidfuzz import process


os.environ["OPENAI_DEFAULT_MODEL"] = "gpt-5-nano"


__all__ = ["membank", "token_set_ratio", "process"]
