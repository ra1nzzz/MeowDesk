"""
MeowDesk - 智能桌面文件分类归档工具
"""

from .utils import configure_logging

__version__ = "1.5.1"
__author__ = "ra1nzzz"
__description__ = "桌面拖拽文件自动分类归档工具"


def setup_logging(level=None, log_file=None) -> None:
    """Initialise the ``meowdesk`` logger tree.

    Called by :mod:`meowdesk_main` at startup so application code can
    use :func:`meowdesk.utils.get_logger` without worrying about
    handler setup.  Safe to call multiple times; subsequent calls are
    no-ops.
    """

    import logging

    configure_logging(level=level or logging.INFO, log_file=log_file)
