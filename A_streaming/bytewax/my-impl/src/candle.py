"""데이터 모델: Trade, Candle, LateData"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class Trade:
    """개별 거래 데이터"""

    symbol: str  # "BTCUSDT"
    price: float  # 50000.0
    quantity: float  # 0.1
    timestamp: datetime  # UTC

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Trade":
        """JSON dict → Trade 변환

        Args:
            data: {"symbol": str, "price": float, "quantity": float, "timestamp": str}

        Returns:
            Trade 인스턴스
        """
        ts_str = data["timestamp"]
        # ISO 8601 형식 지원 (Z → +00:00)
        if ts_str.endswith("Z"):
            ts_str = ts_str[:-1] + "+00:00"
        timestamp = datetime.fromisoformat(ts_str)

        return cls(
            symbol=data["symbol"],
            price=float(data["price"]),
            quantity=float(data["quantity"]),
            timestamp=timestamp,
        )

    def to_dict(self) -> dict[str, Any]:
        """Trade → JSON dict 변환"""
        return {
            "symbol": self.symbol,
            "price": self.price,
            "quantity": self.quantity,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class Candle:
    """OHLCV 캔들 데이터"""

    symbol: str  # "BTCUSDT"
    interval: str  # "1m", "5m"
    open_time: datetime  # 윈도우 시작
    close_time: datetime  # 윈도우 종료
    open: float  # 시가
    high: float  # 고가
    low: float  # 저가
    close: float  # 종가
    volume: float  # 총 거래량
    trade_count: int  # 거래 수

    def to_dict(self) -> dict[str, Any]:
        """Candle → JSON dict 변환"""
        return {
            "symbol": self.symbol,
            "interval": self.interval,
            "open_time": self.open_time.isoformat(),
            "close_time": self.close_time.isoformat(),
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "trade_count": self.trade_count,
        }


@dataclass
class LateData:
    """Late 데이터 정보

    Watermark 이후에 도착한 과거 데이터
    """

    trade: Trade  # 원본 거래
    window_start: datetime  # 속했어야 할 윈도우 시작
    window_end: datetime  # 속했어야 할 윈도우 종료
