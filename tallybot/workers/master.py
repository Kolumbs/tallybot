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
    files = [i for i in w.context.package.last_message.parts if i.binary]
    if not files:
        return None
    last_file = files[-1]
    if last_file.media_type in ["text/plain", "text/csv", "application/json"]:
        return ToolOutputText(text=last_file.binary.decode("utf-8"))
    return ToolOutputFileContent(
        file_data=image_as_base64(last_file.binary),
        file_name=last_file.filename,
    )


def image_as_base64(image: bytes):
    """Return image as base64 string."""
    return base64.b64encode(image).decode("utf-8")
