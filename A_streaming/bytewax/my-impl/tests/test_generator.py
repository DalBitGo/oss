"""candle_generator.py 통합 테스트

요구사항.md의 테스트 시나리오 구현:
- TC-001: 기본 캔들 생성
- TC-002: 여러 윈도우
- TC-003: Late 데이터
- TC-004: 여러 심볼
- TC-005: 빈 윈도우
"""

from datetime import datetime, timedelta, timezone

import pytest

from src.candle import Candle, LateData, Trade
from src.candle_generator import CandleAggregator, CandleGenerator, WindowManager


class TestCandleAggregator:
    """CandleAggregator 단위 테스트"""

    def test_single_trade(self):
        """단일 거래로 캔들 생성"""
        agg = CandleAggregator(
            open_time=datetime(2026, 1, 26, 10, 30, 0, tzinfo=timezone.utc),
            close_time=datetime(2026, 1, 26, 10, 30, 59, 999000, tzinfo=timezone.utc),
        )

        trade = Trade(
            symbol="BTCUSDT",
            price=50000.0,
            quantity=0.1,
            timestamp=datetime(2026, 1, 26, 10, 30, 15, tzinfo=timezone.utc),
        )
        agg.add_trade(trade)

        candle = agg.to_candle("BTCUSDT", "1m")

        assert candle.open == 50000.0
        assert candle.high == 50000.0
        assert candle.low == 50000.0
        assert candle.close == 50000.0
        assert candle.volume == 0.1
        assert candle.trade_count == 1

    def test_multiple_trades_ohlcv(self):
        """여러 거래로 OHLCV 집계"""
        agg = CandleAggregator(
            open_time=datetime(2026, 1, 26, 10, 30, 0, tzinfo=timezone.utc),
            close_time=datetime(2026, 1, 26, 10, 30, 59, 999000, tzinfo=timezone.utc),
        )

        # 시간순으로 거래 추가
        trades = [
            Trade("BTCUSDT", 50000.0, 0.1, datetime(2026, 1, 26, 10, 30, 10, tzinfo=timezone.utc)),  # open
            Trade("BTCUSDT", 50200.0, 0.2, datetime(2026, 1, 26, 10, 30, 20, tzinfo=timezone.utc)),  # high
            Trade("BTCUSDT", 49800.0, 0.3, datetime(2026, 1, 26, 10, 30, 30, tzinfo=timezone.utc)),  # low
            Trade("BTCUSDT", 50100.0, 0.4, datetime(2026, 1, 26, 10, 30, 50, tzinfo=timezone.utc)),  # close
        ]

        for t in trades:
            agg.add_trade(t)

        candle = agg.to_candle("BTCUSDT", "1m")

        assert candle.open == 50000.0  # 첫 거래
        assert candle.high == 50200.0  # 최고가
        assert candle.low == 49800.0  # 최저가
        assert candle.close == 50100.0  # 마지막 거래
        assert candle.volume == 1.0  # 0.1 + 0.2 + 0.3 + 0.4
        assert candle.trade_count == 4

    def test_out_of_order_trades(self):
        """순서가 뒤섞인 거래도 올바르게 처리"""
        agg = CandleAggregator(
            open_time=datetime(2026, 1, 26, 10, 30, 0, tzinfo=timezone.utc),
            close_time=datetime(2026, 1, 26, 10, 30, 59, 999000, tzinfo=timezone.utc),
        )

        # 순서 섞어서 추가 (30초 → 10초 → 50초)
        trades = [
            Trade("BTCUSDT", 49800.0, 0.1, datetime(2026, 1, 26, 10, 30, 30, tzinfo=timezone.utc)),
            Trade("BTCUSDT", 50000.0, 0.2, datetime(2026, 1, 26, 10, 30, 10, tzinfo=timezone.utc)),  # 실제 첫 번째
            Trade("BTCUSDT", 50100.0, 0.3, datetime(2026, 1, 26, 10, 30, 50, tzinfo=timezone.utc)),  # 실제 마지막
        ]

        for t in trades:
            agg.add_trade(t)

        candle = agg.to_candle("BTCUSDT", "1m")

        # 타임스탬프 기준으로 open/close 결정
        assert candle.open == 50000.0  # 10초의 가격
        assert candle.close == 50100.0  # 50초의 가격

    def test_is_empty(self):
        """빈 윈도우 확인"""
        agg = CandleAggregator(
            open_time=datetime(2026, 1, 26, 10, 30, 0, tzinfo=timezone.utc),
            close_time=datetime(2026, 1, 26, 10, 30, 59, 999000, tzinfo=timezone.utc),
        )

        assert agg.is_empty()

        trade = Trade("BTCUSDT", 50000.0, 0.1, datetime(2026, 1, 26, 10, 30, 15, tzinfo=timezone.utc))
        agg.add_trade(trade)

        assert not agg.is_empty()


class TestWindowManager:
    """WindowManager 단위 테스트"""

    def test_format_interval(self):
        """interval 문자열 포맷팅"""
        manager_1m = WindowManager("BTCUSDT", timedelta(minutes=1), timedelta(seconds=5))
        manager_5m = WindowManager("BTCUSDT", timedelta(minutes=5), timedelta(seconds=5))
        manager_1h = WindowManager("BTCUSDT", timedelta(hours=1), timedelta(seconds=5))

        assert manager_1m._format_interval() == "1m"
        assert manager_5m._format_interval() == "5m"
        assert manager_1h._format_interval() == "1h"


class TestCandleGeneratorTC001:
    """TC-001: 기본 캔들 생성

    Given: 10:00:10, 10:00:30, 10:00:50에 거래 3건
    When: watermark가 10:01:00을 넘음
    Then: 10:00 ~ 10:01 캔들 1개 생성
    """

    def test_basic_candle_generation(self):
        candles = []
        generator = CandleGenerator(
            window_size=timedelta(minutes=1),
            watermark_delay=timedelta(seconds=5),
            on_candle=lambda c: candles.append(c),
        )

        # 10:00 윈도우에 3건의 거래
        trades = [
            Trade("BTCUSDT", 50000.0, 0.1, datetime(2026, 1, 26, 10, 0, 10, tzinfo=timezone.utc)),
            Trade("BTCUSDT", 50100.0, 0.2, datetime(2026, 1, 26, 10, 0, 30, tzinfo=timezone.utc)),
            Trade("BTCUSDT", 50050.0, 0.3, datetime(2026, 1, 26, 10, 0, 50, tzinfo=timezone.utc)),
        ]

        for t in trades:
            generator.process(t)

        # 아직 캔들 없음 (watermark가 윈도우 종료 전)
        assert len(candles) == 0

        # watermark를 10:01:06으로 진행 (delay=5초이므로 실제 watermark=10:01:01)
        # 이제 10:00 윈도우 닫힘
        late_trade = Trade("BTCUSDT", 50200.0, 0.1, datetime(2026, 1, 26, 10, 1, 6, tzinfo=timezone.utc))
        generator.process(late_trade)

        # 캔들 1개 생성됨
        assert len(candles) == 1
        candle = candles[0]
        assert candle.symbol == "BTCUSDT"
        assert candle.interval == "1m"
        assert candle.open == 50000.0
        assert candle.high == 50100.0
        assert candle.low == 50000.0
        assert candle.close == 50050.0
        assert candle.trade_count == 3


class TestCandleGeneratorTC002:
    """TC-002: 여러 윈도우

    Given: 10:00:30, 10:01:30, 10:02:30에 거래 3건
    When: watermark가 10:03:00을 넘음
    Then: 각 분별 캔들 3개 생성
    """

    def test_multiple_windows(self):
        candles = []
        generator = CandleGenerator(
            window_size=timedelta(minutes=1),
            watermark_delay=timedelta(seconds=5),
            on_candle=lambda c: candles.append(c),
        )

        # 각 분에 1건씩 거래
        trades = [
            Trade("BTCUSDT", 50000.0, 0.1, datetime(2026, 1, 26, 10, 0, 30, tzinfo=timezone.utc)),
            Trade("BTCUSDT", 50100.0, 0.2, datetime(2026, 1, 26, 10, 1, 30, tzinfo=timezone.utc)),
            Trade("BTCUSDT", 50200.0, 0.3, datetime(2026, 1, 26, 10, 2, 30, tzinfo=timezone.utc)),
        ]

        for t in trades:
            generator.process(t)

        # 10:03:06 거래로 watermark 진행
        trigger_trade = Trade("BTCUSDT", 50300.0, 0.1, datetime(2026, 1, 26, 10, 3, 6, tzinfo=timezone.utc))
        generator.process(trigger_trade)

        # 3개 윈도우 모두 닫힘
        assert len(candles) == 3

        # 시간순 정렬 확인
        assert candles[0].open_time.minute == 0
        assert candles[1].open_time.minute == 1
        assert candles[2].open_time.minute == 2


class TestCandleGeneratorTC003:
    """TC-003: Late 데이터

    Given: watermark가 10:02:00
    When: 10:01:30 timestamp의 거래 도착
    Then: Late로 처리, 캔들에 포함 안 됨
    """

    def test_late_data_handling(self):
        candles = []
        late_items = []

        generator = CandleGenerator(
            window_size=timedelta(minutes=1),
            watermark_delay=timedelta(seconds=5),
            on_candle=lambda c: candles.append(c),
            on_late=lambda l: late_items.append(l),
        )

        # 먼저 10:02:06 거래로 watermark를 10:02:01로 진행
        trigger_trade = Trade("BTCUSDT", 50000.0, 0.1, datetime(2026, 1, 26, 10, 2, 6, tzinfo=timezone.utc))
        generator.process(trigger_trade)

        # 이제 10:01:30 (watermark 이전) 거래 도착 → Late
        late_trade = Trade("BTCUSDT", 49000.0, 0.5, datetime(2026, 1, 26, 10, 1, 30, tzinfo=timezone.utc))
        generator.process(late_trade)

        # Late 데이터로 처리됨
        assert len(late_items) == 1
        assert late_items[0].trade.price == 49000.0
        assert late_items[0].window_start.minute == 1


class TestCandleGeneratorTC004:
    """TC-004: 여러 심볼

    Given: BTCUSDT 2건, ETHUSDT 2건
    When: 처리
    Then: 각 심볼별 독립 캔들 생성
    """

    def test_multiple_symbols(self):
        candles = []
        generator = CandleGenerator(
            window_size=timedelta(minutes=1),
            watermark_delay=timedelta(seconds=5),
            on_candle=lambda c: candles.append(c),
        )

        # 두 심볼의 거래
        trades = [
            Trade("BTCUSDT", 50000.0, 1.0, datetime(2026, 1, 26, 10, 0, 10, tzinfo=timezone.utc)),
            Trade("ETHUSDT", 3000.0, 10.0, datetime(2026, 1, 26, 10, 0, 15, tzinfo=timezone.utc)),
            Trade("BTCUSDT", 50100.0, 2.0, datetime(2026, 1, 26, 10, 0, 30, tzinfo=timezone.utc)),
            Trade("ETHUSDT", 3050.0, 5.0, datetime(2026, 1, 26, 10, 0, 35, tzinfo=timezone.utc)),
        ]

        for t in trades:
            generator.process(t)

        # flush로 모든 윈도우 닫기
        generator.flush()

        assert len(candles) == 2

        btc_candle = next(c for c in candles if c.symbol == "BTCUSDT")
        eth_candle = next(c for c in candles if c.symbol == "ETHUSDT")

        # BTC 캔들 검증
        assert btc_candle.open == 50000.0
        assert btc_candle.close == 50100.0
        assert btc_candle.volume == 3.0
        assert btc_candle.trade_count == 2

        # ETH 캔들 검증
        assert eth_candle.open == 3000.0
        assert eth_candle.close == 3050.0
        assert eth_candle.volume == 15.0
        assert eth_candle.trade_count == 2


class TestCandleGeneratorTC005:
    """TC-005: 빈 윈도우

    Given: 10:00:30에만 거래
    When: watermark가 10:03:00
    Then: 10:00 캔들만 생성, 10:01, 10:02는 없음
    """

    def test_empty_windows_not_emitted(self):
        candles = []
        generator = CandleGenerator(
            window_size=timedelta(minutes=1),
            watermark_delay=timedelta(seconds=5),
            on_candle=lambda c: candles.append(c),
        )

        # 10:00 윈도우에만 거래
        trade1 = Trade("BTCUSDT", 50000.0, 1.0, datetime(2026, 1, 26, 10, 0, 30, tzinfo=timezone.utc))
        generator.process(trade1)

        # 10:03:06으로 바로 점프 (10:01, 10:02는 거래 없음)
        trade2 = Trade("BTCUSDT", 50100.0, 1.0, datetime(2026, 1, 26, 10, 3, 6, tzinfo=timezone.utc))
        generator.process(trade2)

        # 10:00 캔들만 생성 (빈 윈도우는 생성 안 함)
        assert len(candles) == 1
        assert candles[0].open_time.minute == 0


class TestCandleGeneratorFlush:
    """flush() 메서드 테스트"""

    def test_flush_emits_all_open_windows(self):
        candles = []
        generator = CandleGenerator(
            window_size=timedelta(minutes=1),
            watermark_delay=timedelta(seconds=5),
            on_candle=lambda c: candles.append(c),
        )

        # 같은 윈도우에 여러 거래 (flush 전에 닫히지 않도록)
        trades = [
            Trade("BTCUSDT", 50000.0, 1.0, datetime(2026, 1, 26, 10, 0, 10, tzinfo=timezone.utc)),
            Trade("BTCUSDT", 50100.0, 1.0, datetime(2026, 1, 26, 10, 0, 30, tzinfo=timezone.utc)),
        ]

        for t in trades:
            generator.process(t)

        # 아직 캔들 없음 (같은 윈도우 내)
        assert len(candles) == 0

        # flush로 강제 닫기
        generator.flush()

        # 윈도우 1개 캔들 생성
        assert len(candles) == 1
        assert candles[0].trade_count == 2


class TestProcessDict:
    """process_dict() 메서드 테스트"""

    def test_process_dict(self):
        candles = []
        generator = CandleGenerator(
            window_size=timedelta(minutes=1),
            watermark_delay=timedelta(seconds=5),
            on_candle=lambda c: candles.append(c),
        )

        # dict로 직접 처리
        data = {
            "symbol": "BTCUSDT",
            "price": 50000.0,
            "quantity": 1.0,
            "timestamp": "2026-01-26T10:00:30Z",
        }
        generator.process_dict(data)

        generator.flush()

        assert len(candles) == 1
        assert candles[0].symbol == "BTCUSDT"
