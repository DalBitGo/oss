"""윈도우 처리 유틸리티: TumblingWindow"""

from datetime import datetime, timedelta, timezone


class TumblingWindow:
    """Tumbling Window 경계 계산 유틸리티

    Tumbling Window: 고정 크기, 겹치지 않는 윈도우
    예: 1분 윈도우 → 10:00-10:01, 10:01-10:02, ...
    """

    @staticmethod
    def get_window_start(timestamp: datetime, window_size: timedelta) -> datetime:
        """주어진 타임스탬프가 속하는 윈도우의 시작 시간

        Args:
            timestamp: 이벤트 타임스탬프
            window_size: 윈도우 크기

        Returns:
            윈도우 시작 시간 (정각 기준)

        예시:
            window_size=1분, ts=10:30:45 → 10:30:00
            window_size=5분, ts=10:33:20 → 10:30:00
        """
        # Unix timestamp로 변환
        ts_seconds = timestamp.timestamp()
        window_seconds = window_size.total_seconds()

        # 내림 처리로 윈도우 시작 계산
        window_start_seconds = int(ts_seconds // window_seconds) * window_seconds

        # timezone 유지
        tz = timestamp.tzinfo or timezone.utc
        return datetime.fromtimestamp(window_start_seconds, tz=tz)

    @staticmethod
    def get_window_end(window_start: datetime, window_size: timedelta) -> datetime:
        """윈도우 종료 시간 계산

        Args:
            window_start: 윈도우 시작 시간
            window_size: 윈도우 크기

        Returns:
            윈도우 종료 시간 (시작 + 크기 - 1ms)

        예시:
            start=10:30:00, size=1분 → 10:30:59.999
        """
        return window_start + window_size - timedelta(milliseconds=1)
