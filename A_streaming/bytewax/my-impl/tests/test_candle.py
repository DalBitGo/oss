"""candle.py 모델 테스트"""

from datetime import datetime, timezone

import pytest

from src.candle import Candle, LateData, Trade


class TestTrade:
    """Trade 모델 테스트"""

    def test_from_dict_basic(self):
        """기본 dict → Trade 변환"""
        data = {
            "symbol": "BTCUSDT",
            "price": 50000.0,
            "quantity": 0.1,
            "timestamp": "2026-01-26T10:30:15+00:00",
        }
        trade = Trade.from_dict(data)

        assert trade.symbol == "BTCUSDT"
        assert trade.price == 50000.0
        assert trade.quantity == 0.1
        assert trade.timestamp == datetime(2026, 1, 26, 10, 30, 15, tzinfo=timezone.utc)

    def test_from_dict_z_suffix(self):
        """Z 접미사 ISO 8601 지원"""
        data = {
            "symbol": "ETHUSDT",
            "price": 3000.0,
            "quantity": 1.0,
            "timestamp": "2026-01-26T10:30:15.123Z",
        }
        trade = Trade.from_dict(data)

        assert trade.timestamp.tzinfo == timezone.utc
        assert trade.timestamp.microsecond == 123000

    def test_from_dict_string_numbers(self):
        """문자열로 된 숫자 처리"""
        data = {
            "symbol": "BTCUSDT",
            "price": "50000.5",
            "quantity": "0.15",
            "timestamp": "2026-01-26T10:30:15Z",
        }
        trade = Trade.from_dict(data)

        assert trade.price == 50000.5
        assert trade.quantity == 0.15

    def test_to_dict(self):
        """Trade → dict 변환"""
        trade = Trade(
            symbol="BTCUSDT",
            price=50000.0,
            quantity=0.1,
            timestamp=datetime(2026, 1, 26, 10, 30, 15, tzinfo=timezone.utc),
        )
        result = trade.to_dict()

        assert result["symbol"] == "BTCUSDT"
        assert result["price"] == 50000.0
        assert result["quantity"] == 0.1
        assert "2026-01-26T10:30:15" in result["timestamp"]


class TestCandle:
    """Candle 모델 테스트"""

    def test_to_dict(self):
        """Candle → dict 변환"""
        candle = Candle(
            symbol="BTCUSDT",
            interval="1m",
            open_time=datetime(2026, 1, 26, 10, 30, 0, tzinfo=timezone.utc),
            close_time=datetime(2026, 1, 26, 10, 30, 59, 999000, tzinfo=timezone.utc),
            open=50000.0,
            high=50150.0,
            low=49950.0,
            close=50100.0,
            volume=10.5,
            trade_count=42,
        )
        result = candle.to_dict()

        assert result["symbol"] == "BTCUSDT"
        assert result["interval"] == "1m"
        assert result["open"] == 50000.0
        assert result["high"] == 50150.0
        assert result["low"] == 49950.0
        assert result["close"] == 50100.0
        assert result["volume"] == 10.5
        assert result["trade_count"] == 42


class TestLateData:
    """LateData 모델 테스트"""

    def test_late_data_creation(self):
        """LateData 생성"""
        trade = Trade(
            symbol="BTCUSDT",
            price=50000.0,
            quantity=0.1,
            timestamp=datetime(2026, 1, 26, 10, 30, 15, tzinfo=timezone.utc),
        )
        late = LateData(
            trade=trade,
            window_start=datetime(2026, 1, 26, 10, 30, 0, tzinfo=timezone.utc),
            window_end=datetime(2026, 1, 26, 10, 30, 59, 999000, tzinfo=timezone.utc),
        )

        assert late.trade == trade
        assert late.window_start.minute == 30
        assert late.window_end.minute == 30
