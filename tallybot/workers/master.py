"""Workers that work with master data management."""

import pydantic
from agents import function_tool, RunContextWrapper
from .base import TallybotContext
from ..brain import do_task


class CreatePartnerData(pydantic.BaseModel):
    """Data for creating new partner."""

    name: str = pydantic.Field(
        description="Partner name as shown in accounting system"
    )
    other_names: list[str] = pydantic.Field(
        description="Other names or aliases for the partner"
    )


@function_tool
async def do_register_partner(
    w: RunContextWrapper[TallybotContext], data: CreatePartnerData
) -> str:
    """Create a new partner in the system."""
    partner = data.model_dump()
    partner["other_names"] = ",".join(data.other_names)

    msg, fbytes, fname = do_task(
        w.context.conf,
        w.context.memory,
        "do_create_partner",
        [partner],
    )
    return msg


@function_tool
async def get_user_last_attachments(
    w: RunContextWrapper[TallybotContext],
) -> str:
    """Return a list of filenames attached to the last message."""
    return [
        {
            "file_type": i.media_type,
            "size": len(i.binary),
            "file_name": i.filename,
        }
        for i in w.context.package.last_message.parts
        if i.binary
    ]
