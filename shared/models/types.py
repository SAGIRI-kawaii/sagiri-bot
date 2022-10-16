from enum import Enum


class ModuleOperationType(Enum):
    INSTALL = "install"
    UNINSTALL = "uninstall"
    RELOAD = "reload"
