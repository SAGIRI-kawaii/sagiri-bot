from enum import Enum


class PermissionLevel(Enum):
    BLOCK = -1
    USER = 1
    ADMIN = 2
    SUPERADMIN = 3
    OWNER = 4
    DEFAULT = USER
