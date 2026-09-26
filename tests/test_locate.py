"""Tests for navigation-page file locating."""

import base64
import os
from urllib.parse import quote

from meowdesk import locate
from meowdesk.index_gen import generate_html
from meowdesk.ui import menu_actions


def test_protocol_url_roundtrip_preserves_case_and_unicode():
    path = r"C:\Users\O'Brien\文档\a+b\c d.txt"
    url = locate.locate_protocol_url(path)
    token = url.rsplit("/", 1)[-1]

    assert url.startswith("meow-locate://locate/")
    assert "+" not in token and "/" not in token and "=" not in token
    assert decode_same(url, path)
    assert decode_same(f'"{url}/"', path)
    assert decode_same("meow-locate://locate/" + quote(token, safe=""), path)


def decode_same(url, path):
    return locate.decode_locate_url(url) == os.path.normpath(os.path.abspath(path))


def test_decode_rejects_garbage_and_relative_payloads():
    assert locate.decode_locate_url("") is None
    assert locate.decode_locate_url("meow-locate://locate/!!!") is None
    assert locate.decode_locate_url("https://example.com") is None
    token = base64.urlsafe_b64encode(b"notes/relative.txt").decode("ascii").rstrip("=")
    assert locate.decode_locate_url(f"meow-locate://locate/{token}") is None


def test_decode_legacy_scheme_with_path_token():
    path = os.path.abspath(r"D:\archive\文档\note.txt")
    token = locate.encode_locate_token(path)
    assert locate.decode_locate_url(f"lingxi-locate://locate/{token}") == os.path.normpath(path)


def test_resolve_existing_file_selects_it(tmp_path):
    target = tmp_path / "shot.png"
    target.write_text("x", encoding="utf-8")

    action, resolved = locate.resolve_reveal_target(str(target))

    assert action == "select"
    assert os.path.normcase(resolved) == os.path.normcase(os.path.abspath(str(target)))


def test_resolve_missing_file_opens_parent(tmp_path):
    missing = tmp_path / "gone.txt"

    action, resolved = locate.resolve_reveal_target(str(missing))

    assert action == "open"
    assert os.path.normcase(resolved) == os.path.normcase(os.path.abspath(str(tmp_path)))


def test_resolve_missing_parent_is_none():
    assert locate.resolve_reveal_target(r"Z:\no\such\dir\file.txt") is None


def test_handle_locate_does_not_start_for_normal_args(monkeypatch):
    called = []
    monkeypatch.setattr(locate, "reveal_in_file_manager", lambda path: called.append(path) or True)

    assert locate.handle_locate_invocation([]) is False
    assert locate.handle_locate_invocation(["--help"]) is False
    assert called == []


def test_handle_locate_reveals_and_swallows_gui(monkeypatch, tmp_path):
    target = tmp_path / "a.txt"
    target.write_text("x", encoding="utf-8")
    seen = []
    monkeypatch.setattr(locate, "reveal_in_file_manager", lambda path: seen.append(path) or True)

    assert locate.handle_locate_invocation(["--locate", locate.locate_protocol_url(str(target))]) is True
    assert seen == [os.path.normpath(os.path.abspath(str(target)))]


def test_handle_locate_bad_url_does_not_raise():
    assert locate.handle_locate_invocation(["--locate", "meow-locate://locate/!!!"]) is True


def test_build_locate_command_quotes_handler():
    command = locate.build_locate_command()
    assert command.startswith('"')
    assert '--locate "%1"' in command


def test_build_locate_command_frozen(monkeypatch):
    monkeypatch.setattr(locate.sys, "frozen", True, raising=False)
    monkeypatch.setattr(locate.sys, "executable", r"C:\Program Files\MeowDesk\MeowDesk.exe")

    assert locate.build_locate_command() == r'"C:\Program Files\MeowDesk\MeowDesk.exe" --locate "%1"'


def test_handler_prefers_pythonw(monkeypatch, tmp_path):
    python = tmp_path / "python.exe"
    pythonw = tmp_path / "pythonw.exe"
    python.write_text("", encoding="utf-8")
    pythonw.write_text("", encoding="utf-8")
    monkeypatch.setattr(locate.sys, "frozen", False, raising=False)
    monkeypatch.setattr(locate.sys, "executable", str(python))

    assert locate._handler_executable() == str(pythonw)


def test_register_skipped_off_windows(monkeypatch):
    monkeypatch.setattr(locate.sys, "platform", "linux")
    assert locate.register_locate_protocol() is False


def test_generated_locate_link_decodes_to_destination():
    dest = os.path.abspath(os.path.join("archive", "文档", "note.txt"))
    html = generate_html(
        [
            {
                "category": "文档",
                "original_name": "note.txt",
                "date": "2026-06-03",
                "action": "archive",
                "destination": dest,
                "file_size": 12,
                "timestamp": "2026-06-03T10:00:00",
            }
        ],
        os.path.dirname(dest),
        os.path.dirname(dest),
    )

    assert "meow-locate://locate/" in html
    assert "meow-locate://" + locate.encode_locate_token(dest) not in html
    start = html.index('href="meow-locate://') + len('href="')
    url = html[start:html.index('"', start)]
    assert locate.decode_locate_url(url) == os.path.normpath(dest)


def test_recycled_rows_have_no_locate_link():
    html = generate_html(
        [
            {
                "category": "截图",
                "original_name": "shot.png",
                "date": "2026-06-03",
                "action": "recycle",
                "destination": "(已回收)",
                "file_size": 1,
                "timestamp": "2026-06-03T10:00:00",
            }
        ],
        r"C:\archive",
        r"C:\archive",
    )
    assert 'class="btn-locate"' not in html


def test_open_html_refreshes_index_and_registers_protocol(monkeypatch, tmp_path):
    archive = tmp_path / "archive"
    archive.mkdir()
    html = archive / "index.html"
    html.write_text("old", encoding="utf-8")
    calls = []

    class Window:
        config = type("Config", (), {"archive_dir": str(archive)})()
        state = type("State", (), {"show_bubble": staticmethod(lambda *args: calls.append(args))})()

        def _update_html(self):
            calls.append("update")
            html.write_text("<html>new</html>", encoding="utf-8")

    monkeypatch.setattr(menu_actions, "ensure_archive_dir_writable", lambda *args: True)
    monkeypatch.setattr(menu_actions, "_open_local_html", lambda path: calls.append(path))
    monkeypatch.setattr("meowdesk.locate.register_locate_protocol", lambda: True)

    menu_actions.action_open_html(Window())

    assert "update" in calls
    assert str(html) in calls
