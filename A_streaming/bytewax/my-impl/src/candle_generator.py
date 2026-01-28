"""캔들 생성기: CandleAggregator, WindowManager, CandleGenerator"""

from datetime import datetime, timedelta
from typing import Callable, Optional

from .candle import Candle, LateData, Trade
from .window import TumblingWindow


class CandleAggregator:
    """단일 윈도우 내 OHLCV 집계

    윈도우 내의 모든 거래를 받아 OHLCV 캔들을 생성한다.

    Attributes:
        open_time: 윈도우 시작 시간
        close_time: 윈도우 종료 시간
        open: 시가 (첫 번째 거래)
        high: 고가
        low: 저가
        close: 종가 (마지막 거래)
        volume: 총 거래량
        trade_count: 거래 수
    """

    def __init__(self, open_time: datetime, close_time: datetime):
        self.open_time = open_time
        self.close_time = close_time

        # OHLCV
        self.open: Optional[float] = None
        self.high: float = float("-inf")
        self.low: float = float("inf")
        self.close: Optional[float] = None
        self.volume: float = 0.0
        self.trade_count: int = 0

        # 타임스탬프 추적 (open/close 결정용)
        self._first_timestamp: Optional[datetime] = None
        self._last_timestamp: Optional[datetime] = None

    def add_trade(self, trade: Trade) -> None:
        """거래 추가 및 집계 업데이트

        Args:
            trade: 추가할 거래

        Note:
            - open: 가장 이른 타임스탬프의 가격
            - close: 가장 늦은 타임스탬프의 가격
            - 순서가 뒤섞여 도착해도 정확히 계산됨
        """
        price = trade.price
        quantity = trade.quantity
        ts = trade.timestamp

        # Open: 가장 이른 타임스탬프의 가격
        if self._first_timestamp is None or ts < self._first_timestamp:
            self._first_timestamp = ts
            self.open = price

        # High/Low 업데이트
        self.high = max(self.high, price)
        self.low = min(self.low, price)

        # Close: 가장 늦은 타임스탬프의 가격
        if self._last_timestamp is None or ts > self._last_timestamp:
            self._last_timestamp = ts
            self.close = price

        # Volume & Count 누적
        self.volume += quantity
        self.trade_count += 1

    def to_candle(self, symbol: str, interval: str) -> Candle:
        """Candle 객체 생성

        Args:
            symbol: 심볼 (예: "BTCUSDT")
            interval: 윈도우 크기 문자열 (예: "1m")

        Returns:
            완성된 Candle 객체
        """
        return Candle(
            symbol=symbol,
            interval=interval,
            open_time=self.open_time,
            close_time=self.close_time,
            open=self.open or 0.0,
            high=self.high if self.high != float("-inf") else 0.0,
            low=self.low if self.low != float("inf") else 0.0,
            close=self.close or 0.0,
            volume=self.volume,
            trade_count=self.trade_count,
        )

    def is_empty(self) -> bool:
        """거래가 없는 빈 윈도우인지 확인"""
        return self.trade_count == 0


class WindowManager:
    """심볼별 윈도우 상태 관리

    하나의 심볼에 대해:
    - 여러 윈도우의 CandleAggregator 관리
    - Watermark 추적
    - Late 데이터 판별
    - 윈도우 닫기 및 캔들 emit

    Attributes:
        symbol: 관리하는 심볼
        window_size: 윈도우 크기
        watermark_delay: Watermark 지연
        windows: 열린 윈도우들 (시작시간 → CandleAggregator)
        watermark: 현재 Watermark
    """

    def __init__(
        self,
        symbol: str,
        window_size: timedelta,
        watermark_delay: timedelta,
    ):
        self.symbol = symbol
        self.window_size = window_size
        self.watermark_delay = watermark_delay

        # 윈도우 상태 (window_start → aggregator)
        self.windows: dict[datetime, CandleAggregator] = {}

        # Watermark (이 시간 이전 데이터는 Late)
        self.watermark: Optional[datetime] = None

    def add_trade(self, trade: Trade) -> Optional[LateData]:
        """거래 추가

        Args:
            trade: 추가할 거래

        Returns:
            Late 데이터면 LateData 반환, 아니면 None
        """
        # Late 데이터 체크
        if self.watermark and trade.timestamp < self.watermark:
            window_start = TumblingWindow.get_window_start(
                trade.timestamp, self.window_size
            )
            window_end = TumblingWindow.get_window_end(window_start, self.window_size)
            return LateData(
                trade=trade,
                window_start=window_start,
                window_end=window_end,
            )

        # 윈도우 찾기/생성
        window_start = TumblingWindow.get_window_start(
            trade.timestamp, self.window_size
        )

        if window_start not in self.windows:
            window_end = TumblingWindow.get_window_end(window_start, self.window_size)
            self.windows[window_start] = CandleAggregator(
                open_time=window_start,
                close_time=window_end,
            )

        # 집계
        self.windows[window_start].add_trade(trade)
        return None

    def advance_watermark(self, timestamp: datetime) -> list[Candle]:
        """Watermark 진행 및 닫힌 윈도우의 캔들 반환

        Args:
            timestamp: 새로운 watermark 기준 시간 (현재 이벤트 시간)

        Returns:
            닫힌 윈도우들의 캔들 리스트 (시간순 정렬)
        """
        # watermark = 현재 시간 - delay
        new_watermark = timestamp - self.watermark_delay

        # Watermark가 후퇴하면 무시
        if self.watermark and new_watermark <= self.watermark:
            return []

        self.watermark = new_watermark

        # 닫힌 윈도우 찾기
        closed_candles: list[Candle] = []
        closed_windows: list[datetime] = []

        for window_start, aggregator in self.windows.items():
            # 윈도우 종료 시간이 watermark 이전이면 닫기
            if aggregator.close_time < self.watermark:
                if not aggregator.is_empty():
                    interval = self._format_interval()
                    candle = aggregator.to_candle(self.symbol, interval)
                    closed_candles.append(candle)
                closed_windows.append(window_start)

        # 닫힌 윈도우 제거
        for ws in closed_windows:
            del self.windows[ws]

        # 시간순 정렬
        closed_candles.sort(key=lambda c: c.open_time)

        return closed_candles

    def flush(self) -> list[Candle]:
        """모든 열린 윈도우 강제 닫기

        종료 시 호출하여 남은 데이터 처리

        Returns:
            모든 열린 윈도우의 캔들 리스트 (시간순 정렬)
        """
        candles: list[Candle] = []
        interval = self._format_interval()

        for aggregator in self.windows.values():
            if not aggregator.is_empty():
                candle = aggregator.to_candle(self.symbol, interval)
                candles.append(candle)

        self.windows.clear()

        # 시간순 정렬
        candles.sort(key=lambda c: c.open_time)

        return candles

    def _format_interval(self) -> str:
        """윈도우 크기를 interval 문자열로 변환"""
        seconds = int(self.window_size.total_seconds())
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            return f"{seconds // 60}m"
        elif seconds < 86400:
            return f"{seconds // 3600}h"
        else:
            return f"{seconds // 86400}d"


class CandleGenerator:
    """캔들 생성기 최상위 인터페이스

    사용 예시:
        generator = CandleGenerator(
            window_size=timedelta(minutes=1),
            watermark_delay=timedelta(seconds=5),
            on_candle=lambda candle: print(candle),
            on_late=lambda late: print(f"Late: {late}"),
        )

        # Trade 처리
        for trade in trades:
            generator.process(trade)

        # 종료 시 남은 윈도우 flush
        generator.flush()

    Attributes:
        window_size: 윈도우 크기 (기본 1분)
        watermark_delay: Watermark 지연 (기본 5초)
        on_candle: 캔들 생성 시 콜백
        on_late: Late 데이터 발생 시 콜백
        window_managers: 심볼별 WindowManager
    """

    def __init__(
        self,
        window_size: timedelta = timedelta(minutes=1),
        watermark_delay: timedelta = timedelta(seconds=5),
        on_candle: Optional[Callable[[Candle], None]] = None,
        on_late: Optional[Callable[[LateData], None]] = None,
    ):
        self.window_size = window_size
        self.watermark_delay = watermark_delay
        self.on_candle = on_candle or (lambda c: None)
        self.on_late = on_late

        # 심볼별 WindowManager
        self.window_managers: dict[str, WindowManager] = {}

    def _get_manager(self, symbol: str) -> WindowManager:
        """심볼별 WindowManager 조회/생성"""
        if symbol not in self.window_managers:
            self.window_managers[symbol] = WindowManager(
                symbol=symbol,
                window_size=self.window_size,
                watermark_delay=self.watermark_delay,
            )
        return self.window_managers[symbol]

    def process(self, trade: Trade) -> None:
        """Trade 처리

        1. 해당 심볼의 WindowManager로 전달
        2. Late 데이터 처리
        3. Watermark 진행 및 캔들 emit

        Args:
            trade: 처리할 Trade
        """
        manager = self._get_manager(trade.symbol)

        # 거래 추가
        late_data = manager.add_trade(trade)

        # Late 데이터 처리
        if late_data:
            if self.on_late:
                self.on_late(late_data)
            return

        # Watermark 진행 및 캔들 emit
        candles = manager.advance_watermark(trade.timestamp)
        for candle in candles:
            self.on_candle(candle)

    def process_dict(self, data: dict) -> None:
        """dict 형식 Trade 처리

        JSON에서 파싱된 dict를 바로 처리

        Args:
            data: Trade dict
        """
        trade = Trade.from_dict(data)
        self.process(trade)

    def advance_watermark(self, timestamp: datetime) -> None:
        """수동 watermark 진행

        외부 시간 소스 사용 시 호출

        Args:
            timestamp: 새로운 watermark 기준 시간
        """
        for manager in self.window_managers.values():
            candles = manager.advance_watermark(timestamp)
            for candle in candles:
                self.on_candle(candle)

    def flush(self) -> None:
        """모든 열린 윈도우 강제 닫기

        종료 시 호출하여 남은 데이터 처리
        """
        for manager in self.window_managers.values():
            candles = manager.flush()
            for candle in candles:
                self.on_candle(candle)
