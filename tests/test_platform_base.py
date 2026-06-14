"""PlatformWindow 抽象基类的契约测试。

覆盖 ROADMAP 阶段 2 的 "platform/base.py 抽象契约测试" 项：

- 抽象基类不可直接实例化
- 缺少任一抽象方法的子类不可实例化
- 完整实现子类可实例化，且具体方法（回调注册器、set_size、
  目录可写检查）行为正确
- 所有回调属性在 __init__ 后即存在（默认 None）
"""

import os

import pytest

from meowdesk.platform.base import PlatformWindow


# ---------- 测试替身 ----------

class FullWindow(PlatformWindow):
    """实现了全部抽象方法的最小子类。"""

    def create(self): ...
    def show(self): ...
    def hide(self): ...
    def set_position(self, x, y): self.x, self.y = x, y
    def get_position(self): return (self.x, self.y)
    def render(self, image): ...
    def set_topmost(self, topmost): ...
    def enable_drag_drop(self): ...
    def run(self): ...
    def quit(self): ...


class PartialWindow(PlatformWindow):
    """缺少 run/quit，故仍是抽象类。"""

    def create(self): ...
    def show(self): ...
    def hide(self): ...
    def set_position(self, x, y): ...
    def get_position(self): return (0, 0)
    def render(self, image): ...
    def set_topmost(self, topmost): ...
    def enable_drag_drop(self): ...


# ---------- 实例化契约 ----------

class TestInstantiationContract:
    def test_base_is_abstract(self):
        with pytest.raises(TypeError):
            PlatformWindow(10, 10)

    def test_partial_subclass_is_abstract(self):
        with pytest.raises(TypeError):
            PartialWindow(10, 10)

    def test_full_subclass_instantiable(self):
        win = FullWindow(120, 80)
        assert win.width == 120
        assert win.height == 80
        assert (win.x, win.y) == (0, 0)


# ---------- 回调注册器 ----------

CALLBACK_REGISTRARS = [
    ("on_drop", "on_drop_callback"),
    ("on_click", "on_click_callback"),
    ("on_right_click", "on_right_click_callback"),
    ("on_mouse_enter", "on_mouse_enter_callback"),
    ("on_mouse_exit", "on_mouse_exit_callback"),
    ("on_drag_start", "on_drag_start_callback"),
    ("on_drag_end", "on_drag_end_callback"),
    ("on_drag_enter", "on_drag_enter_callback"),
    ("on_drag_exit", "on_drag_exit_callback"),
]


class TestCallbackRegistration:
    @pytest.mark.parametrize("method, attr", CALLBACK_REGISTRARS)
    def test_default_is_none(self, method, attr):
        """所有回调属性在 __init__ 后即存在且默认 None。"""
        win = FullWindow(10, 10)
        assert getattr(win, attr) is None

    @pytest.mark.parametrize("method, attr", CALLBACK_REGISTRARS)
    def test_registrar_stores_callback(self, method, attr):
        win = FullWindow(10, 10)
        sentinel = lambda *a, **k: "called"
        getattr(win, method)(sentinel)
        assert getattr(win, attr) is sentinel


# ---------- 具体方法默认行为 ----------

class TestConcreteMethods:
    def test_set_size(self):
        win = FullWindow(10, 10)
        win.set_size(300, 200)
        assert (win.width, win.height) == (300, 200)

    def test_check_directory_writable_creates_and_checks(self, tmp_path):
        target = os.path.join(str(tmp_path), "nested", "dir")
        assert FullWindow.check_directory_writable(target) is True
        assert os.path.isdir(target)

    def test_check_directory_writable_existing(self, tmp_path):
        assert FullWindow.check_directory_writable(str(tmp_path)) is True

    def test_request_directory_access_delegates(self, tmp_path):
        win = FullWindow(10, 10)
        assert win.request_directory_access(str(tmp_path)) is True
