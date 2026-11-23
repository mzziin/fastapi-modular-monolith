from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, Index, String, Text, false, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.modules.users.models import User


class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (Index("ix_tasks_owner_id_id", "owner_id", "id"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    is_completed: Mapped[bool] = mapped_column(server_default=false())
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(server_default=func.timezone("UTC", func.now()))

    owner: Mapped[User] = relationship()
