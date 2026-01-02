"""Workers that work with master data management."""

import base64
import pydantic
from agents import function_tool, RunContextWrapper
from agents.tool import ToolOutputFileContent, ToolOutputText
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
async def get_user_last_attachment(
    w: RunContextWrapper[TallybotContext],
) -> ToolOutputFileContent | ToolOutputText:
    """Return last user attached file."""
    lastf = w.context.get_attachment()
    if lastf is None:
        return ToolOutputText(text="No attached files found.")
    if lastf.media_type in ["text/plain", "text/csv", "application/json"]:
        return ToolOutputText(text=lastf.binary.decode("utf-8"))
    if not lastf.filename:
        return ToolOutputText(text="Last attached file has no filename.")
    if lastf.media_type not in ["application/pdf"]:
        return ToolOutputText(text="Currently only pdf files are supported.")
    return ToolOutputFileContent(
        file_data=f"data:{lastf.media_type};base64,{image_as_base64(lastf.binary)}",
        filename=lastf.filename,
        code="base64",
    )


def image_as_base64(image: bytes):
    """Return image as base64 string."""
    return base64.b64encode(image).decode("utf-8")
