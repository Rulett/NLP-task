import datetime
import uuid
from typing import Annotated

from sqlalchemy import Uuid, text
from sqlalchemy.orm import mapped_column

uuidpk = Annotated[
    uuid.UUID,
    mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
        index=True,
        nullable=False,
    ),
]
created_at = Annotated[datetime.datetime, mapped_column(server_default=text("TIMEZONE('utc', now())"))]
updated_at = Annotated[
    datetime.datetime,
    mapped_column(server_default=text("TIMEZONE('utc', now())"), onupdate=text("TIMEZONE('utc', now())")),
]
