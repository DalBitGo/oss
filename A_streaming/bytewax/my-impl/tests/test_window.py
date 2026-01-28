"""window.py 윈도우 계산 테스트"""

from datetime import datetime, timedelta, timezone

import pytest

from src.window import TumblingWindow


class TestTumblingWindow:
    """TumblingWindow 테스트"""

    def test_get_window_start_1min(self):
        """1분 윈도우 시작 계산"""
        ts = datetime(2026, 1, 26, 10, 30, 45, tzinfo=timezone.utc)
        window_size = timedelta(minutes=1)

        start = TumblingWindow.get_window_start(ts, window_size)

        assert start == datetime(2026, 1, 26, 10, 30, 0, tzinfo=timezone.utc)

    def test_get_window_start_5min(self):
        """5분 윈도우 시작 계산"""
        ts = datetime(2026, 1, 26, 10, 33, 20, tzinfo=timezone.utc)
        window_size = timedelta(minutes=5)

        start = TumblingWindow.get_window_start(ts, window_size)

        assert start == datetime(2026, 1, 26, 10, 30, 0, tzinfo=timezone.utc)

    def test_get_window_start_at_boundary(self):
        """정확히 윈도우 경계에서 시작"""
        ts = datetime(2026, 1, 26, 10, 30, 0, tzinfo=timezone.utc)
        window_size = timedelta(minutes=1)

        start = TumblingWindow.get_window_start(ts, window_size)

        assert start == datetime(2026, 1, 26, 10, 30, 0, tzinfo=timezone.utc)

    def test_get_window_start_15min(self):
        """15분 윈도우 시작 계산"""
        ts = datetime(2026, 1, 26, 10, 47, 30, tzinfo=timezone.utc)
        window_size = timedelta(minutes=15)

        start = TumblingWindow.get_window_start(ts, window_size)

        assert start == datetime(2026, 1, 26, 10, 45, 0, tzinfo=timezone.utc)

    def test_get_window_start_1hour(self):
        """1시간 윈도우 시작 계산"""
        ts = datetime(2026, 1, 26, 10, 45, 30, tzinfo=timezone.utc)
        window_size = timedelta(hours=1)

        start = TumblingWindow.get_window_start(ts, window_size)

        assert start == datetime(2026, 1, 26, 10, 0, 0, tzinfo=timezone.utc)

    def test_get_window_end_1min(self):
        """1분 윈도우 종료 계산"""
        start = datetime(2026, 1, 26, 10, 30, 0, tzinfo=timezone.utc)
        window_size = timedelta(minutes=1)

        end = TumblingWindow.get_window_end(start, window_size)

        # 10:30:59.999
        assert end.minute == 30
        assert end.second == 59
        assert end.microsecond == 999000

    def test_get_window_end_5min(self):
        """5분 윈도우 종료 계산"""
        start = datetime(2026, 1, 26, 10, 30, 0, tzinfo=timezone.utc)
        window_size = timedelta(minutes=5)

        end = TumblingWindow.get_window_end(start, window_size)

        # 10:34:59.999
        assert end.minute == 34
        assert end.second == 59

    def test_consecutive_windows(self):
        """연속 윈도우가 겹치지 않음"""
        window_size = timedelta(minutes=1)

        # 첫 번째 윈도우
        ts1 = datetime(2026, 1, 26, 10, 30, 30, tzinfo=timezone.utc)
        start1 = TumblingWindow.get_window_start(ts1, window_size)
        end1 = TumblingWindow.get_window_end(start1, window_size)

        # 두 번째 윈도우
        ts2 = datetime(2026, 1, 26, 10, 31, 30, tzinfo=timezone.utc)
        start2 = TumblingWindow.get_window_start(ts2, window_size)

        # 첫 번째 종료 < 두 번째 시작
        assert end1 < start2

    def test_preserves_timezone(self):
        """타임존 유지"""
        # UTC+9 시간대
        kst = timezone(timedelta(hours=9))
        ts = datetime(2026, 1, 26, 19, 30, 45, tzinfo=kst)
        window_size = timedelta(minutes=1)

        start = TumblingWindow.get_window_start(ts, window_size)

        assert start.tzinfo == kst
