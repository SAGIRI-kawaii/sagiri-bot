from dataclasses import dataclass
from sqlalchemy.types import INTEGER, String
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.orm import mapped_column as col
from sqlalchemy import UniqueConstraint, ForeignKey

from shared.database.model import Base
from shared.models.permission import PermissionLevel


@dataclass
class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = col(INTEGER(), nullable=False, primary_key=True, autoincrement=True, unique=True)
    data_json: Mapped[str] = col(String(), nullable=False, unique=True)
    # land: Mapped[str] = col(String(), nullable=False)
    # org: Mapped[int] = col(INTEGER(), nullable=False)       # 若为 -1 则代表没有所属组织
    # sub_org: Mapped[int] = col(INTEGER(), nullable=False)   # 若为 -1 则代表没有所属子组织
    # uid: Mapped[int] = col(INTEGER(), nullable=False)

    # 级联删除项
    user_info = relationship("UserInfo", back_populates="user", uselist=False, cascade="all, delete", primaryjoin="User.id == UserInfo.id")
    user_permission = relationship("UserPermission", back_populates="user", uselist=False, cascade="all, delete", primaryjoin="User.id == UserPermission.id")

    # 唯一约束
    # __table_args__ = (UniqueConstraint("land", "org", "sub_org", "uid"),)


@dataclass
class UserInfo(Base):
    __tablename__ = "user_info"

    id: Mapped[int] = col(INTEGER(), ForeignKey('user.id'), nullable=False, primary_key=True, autoincrement=True, unique=True)
    
    user = relationship("User", back_populates="user_info", foreign_keys=[id])


@dataclass
class UserPermission(Base):
    __tablename__ = "user_permission"

    id: Mapped[int] = col(INTEGER(), ForeignKey('user.id'), nullable=False, primary_key=True, unique=True)
    level: Mapped[int] = col(INTEGER(), nullable=False, default=PermissionLevel.DEFAULT.value)
    
    user = relationship("User", back_populates="user_permission", foreign_keys=[id])
