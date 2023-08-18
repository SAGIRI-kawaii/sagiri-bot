from datetime import datetime
from dataclasses import dataclass
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.orm import mapped_column as col
from sqlalchemy.types import INTEGER, String, DateTime, BOOLEAN

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
    user_info = relationship("UserInfo", back_populates="user", uselist=False, cascade="all, delete-orphan", primaryjoin="User.id == UserInfo.id")
    user_permission = relationship("UserPermission", back_populates="user", uselist=False, cascade="all, delete-orphan", primaryjoin="User.id == UserPermission.id")
    chat_record = relationship("ChatRecord", back_populates="user", uselist=False, cascade="all, delete-orphan", primaryjoin="User.id == ChatRecord.uid")
    user_function_calls = relationship("UserFunctionCalls", back_populates="user", uselist=False, cascade="all, delete-orphan", primaryjoin="User.id == UserFunctionCalls.uid")

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


@dataclass
class ChatRecord(Base):
    __tablename__ = "chat_record"

    id: Mapped[int] = col(INTEGER(), nullable=False, primary_key=True, unique=True, autoincrement=True)
    uid: Mapped[int] = col(INTEGER(), ForeignKey('user.id'), nullable=False)
    time: Mapped[datetime] = col(DateTime(), nullable=False)
    persistent_string: Mapped[str] = col(String(), nullable=False)
    seg: Mapped[str] = col(String(), nullable=True)
    
    user = relationship("User", back_populates="chat_record", foreign_keys=[uid])


@dataclass
class UserFunctionCalls(Base):
    __tablename__ = "user_function_calls"

    id: Mapped[int] = col(INTEGER(), nullable=False, primary_key=True, unique=True, autoincrement=True)
    uid: Mapped[int] = col(INTEGER(), ForeignKey('user.id'), nullable=False)
    time: Mapped[datetime] = col(DateTime(), nullable=False)
    func_name: Mapped[str] = col(String(), nullable=False)
    
    user = relationship("User", back_populates="user_function_calls", foreign_keys=[uid])


@dataclass
class Scene(Base):
    __tablename__ = "scene"

    id: Mapped[int] = col(INTEGER(), nullable=False, primary_key=True, autoincrement=True, unique=True)
    data_json: Mapped[str] = col(String(), nullable=False, unique=True)

    scene_setting = relationship("SceneSetting", back_populates="scene", uselist=False, cascade="all, delete-orphan", primaryjoin="Scene.id == SceneSetting.id")


@dataclass
class SceneSetting(Base):
    __tablename__ = "scene_setting"

    id: Mapped[int] = col(INTEGER(), ForeignKey('scene.id'), nullable=False, primary_key=True, unique=True)
    switch: Mapped[bool] = col(BOOLEAN(), nullable=False, default=True)
    online_notice: Mapped[bool] = col(BOOLEAN(), nullable=False,  default=True)
    
    scene = relationship("Scene", back_populates="scene_setting", foreign_keys=[id])
