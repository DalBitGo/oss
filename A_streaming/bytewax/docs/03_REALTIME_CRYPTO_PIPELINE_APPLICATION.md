# bytewax → realtime-crypto-pipeline 적용 가이드

> **목적**: bytewax 분석 결과를 프로젝트에 실제 적용
> **대상 프로젝트**: `/home/junhyun/projects/realtime-crypto-pipeline`

---

## 1. 적용 가능 영역

### 1.1 Phase별 매핑

```
realtime-crypto-pipeline Phase 구조:
┌──────────────────────────────────────────────────────────────┐
│ Phase 1: Data Collection (수집)                               │
│   - Binance WebSocket → Kafka                                │
│   → bytewax 대체 가능? ❌ (단순 수집은 별도 스크립트 유지)     │
├──────────────────────────────────────────────────────────────┤
│ Phase 2: Stream Processing (스트림 처리)                      │
│   - Kafka → 변환/집계 → Kafka                                │
│   → bytewax 적용 적합! ✅                                    │
├──────────────────────────────────────────────────────────────┤
│ Phase 3: Batch Processing (배치 처리)                         │
│   - Spark로 대용량 집계                                      │
│   → bytewax로 대체 검토 가능 (소규모 시)                      │
├──────────────────────────────────────────────────────────────┤
│ Phase 4: Serving Layer (서빙)                                 │
│   - Redis/API                                                │
│   → 별도 유지                                                │
└──────────────────────────────────────────────────────────────┘
```

### 1.2 Phase 2 대체 시나리오

**현재 구조 (계획)**:
```
Kafka(raw) → [Faust/Kafka Streams?] → Kafka(processed)
```

**bytewax 적용 시**:
```
Kafka(raw) → [bytewax] → Kafka(candles)
                      ↘ Redis(실시간 지표)
```

---

## 2. 구체적 구현 계획

### 2.1 캔들 스틱 생성 파이프라인

```python
# realtime-crypto-pipeline/src/stream_processing/candle_generator.py

from datetime import datetime, timedelta, timezone
from bytewax.dataflow import Dataflow
import bytewax.operators as op
from bytewax.operators.windowing import (
    EventClock, TumblingWindower, fold_window, WindowOut
)
from bytewax.connectors.kafka import KafkaSource, KafkaSink
import json

# ============================================================
# 1. Dataflow 정의
# ============================================================
flow = Dataflow("candle_generator")

# ============================================================
# 2. Kafka Source (raw trades)
# ============================================================
source_config = {
    "brokers": ["localhost:9092"],
    "topics": ["crypto.trades.raw"],
    "starting_offset": "end",  # 최신부터
    "group_id": "candle-generator",
}

raw_trades = op.input("kafka_source", flow, KafkaSource(**source_config))

# ============================================================
# 3. 데이터 파싱 및 검증
# ============================================================
def parse_trade(kafka_msg) -> dict | None:
    """
    Kafka 메시지를 파싱하고 유효성 검증
    None 반환 시 해당 메시지는 제거됨
    """
    try:
        data = json.loads(kafka_msg.value)
        required_fields = ["symbol", "price", "quantity", "timestamp"]

        if not all(f in data for f in required_fields):
            return None

        # 타입 변환
        return {
            "symbol": data["symbol"],
            "price": float(data["price"]),
            "quantity": float(data["quantity"]),
            "timestamp": datetime.fromisoformat(data["timestamp"]),
            "trade_id": data.get("trade_id"),
        }
    except (json.JSONDecodeError, ValueError, KeyError):
        return None

valid_trades = op.filter_map("parse", raw_trades, parse_trade)

# ============================================================
# 4. 심볼별 키 지정
# ============================================================
keyed_trades = op.key_on("by_symbol", valid_trades, lambda x: x["symbol"])

# ============================================================
# 5. 윈도우 설정
# ============================================================
# 이벤트 시간 기반 Clock
clock = EventClock(
    ts_getter=lambda trade: trade["timestamp"],
    wait_for_system_duration=timedelta(seconds=5),  # 5초 대기
)

# 1분봉 윈도우
one_min_windower = TumblingWindower(
    length=timedelta(minutes=1),
    align_to=datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc),
)

# ============================================================
# 6. OHLCV 집계 로직
# ============================================================
def create_empty_candle() -> dict:
    """빈 캔들 생성"""
    return {
        "open": None,
        "high": float("-inf"),
        "low": float("inf"),
        "close": None,
        "volume": 0.0,
        "trade_count": 0,
    }

def update_candle(candle: dict, trade: dict) -> dict:
    """새 거래로 캔들 업데이트"""
    price = trade["price"]
    quantity = trade["quantity"]

    if candle["open"] is None:
        candle["open"] = price

    candle["high"] = max(candle["high"], price)
    candle["low"] = min(candle["low"], price)
    candle["close"] = price
    candle["volume"] += quantity
    candle["trade_count"] += 1

    return candle

def merge_candles(a: dict, b: dict) -> dict:
    """두 캔들 병합 (Session 윈도우 등에서 사용)"""
    return {
        "open": a["open"],
        "high": max(a["high"], b["high"]),
        "low": min(a["low"], b["low"]),
        "close": b["close"],
        "volume": a["volume"] + b["volume"],
        "trade_count": a["trade_count"] + b["trade_count"],
    }

# ============================================================
# 7. 윈도우 집계
# ============================================================
candles_out: WindowOut = fold_window(
    "ohlcv_1m",
    keyed_trades,
    clock,
    one_min_windower,
    builder=create_empty_candle,
    folder=update_candle,
    merger=merge_candles,
)

# ============================================================
# 8. 결과 포맷팅
# ============================================================
def format_candle(item):
    """출력 포맷으로 변환"""
    key, (window_id, candle) = item
    return {
        "symbol": key,
        "interval": "1m",
        "window_id": window_id,
        "open": candle["open"],
        "high": candle["high"],
        "low": candle["low"],
        "close": candle["close"],
        "volume": candle["volume"],
        "trade_count": candle["trade_count"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

formatted_candles = op.map("format", candles_out.down, format_candle)

# ============================================================
# 9. 출력
# ============================================================
# 정상 캔들 → Kafka
sink_config = {
    "brokers": ["localhost:9092"],
    "topic": "crypto.candles.1m",
}
op.output("kafka_sink", formatted_candles, KafkaSink(**sink_config))

# Late 데이터 → DLQ
def format_late(item):
    key, (window_id, trade) = item
    return {
        "type": "late_trade",
        "symbol": key,
        "window_id": window_id,
        "trade": trade,
        "detected_at": datetime.now(timezone.utc).isoformat(),
    }

late_formatted = op.map("format_late", candles_out.late, format_late)
op.output("dlq_sink", late_formatted, KafkaSink(
    brokers=["localhost:9092"],
    topic="crypto.candles.dlq",
))

# ============================================================
# 실행: python -m bytewax.run candle_generator:flow -w 4
# ============================================================
```

### 2.2 실시간 지표 계산

```python
# realtime-crypto-pipeline/src/stream_processing/realtime_metrics.py

from bytewax.dataflow import Dataflow
import bytewax.operators as op
from bytewax.connectors.kafka import KafkaSource
import redis

flow = Dataflow("realtime_metrics")

# Kafka에서 캔들 읽기
candles = op.input("candles", flow, KafkaSource(
    brokers=["localhost:9092"],
    topics=["crypto.candles.1m"],
))

keyed_candles = op.key_on("by_symbol", candles, lambda x: x["symbol"])

# ============================================================
# 이동평균 계산 (Stateful)
# ============================================================
def calculate_ema(state, candle):
    """지수 이동평균 계산"""
    if state is None:
        state = {
            "ema_12": candle["close"],
            "ema_26": candle["close"],
            "count": 1,
        }
    else:
        # EMA 공식: EMA = price * k + EMA_prev * (1 - k)
        k_12 = 2 / (12 + 1)
        k_26 = 2 / (26 + 1)

        state["ema_12"] = candle["close"] * k_12 + state["ema_12"] * (1 - k_12)
        state["ema_26"] = candle["close"] * k_26 + state["ema_26"] * (1 - k_26)
        state["count"] += 1

    # MACD 계산
    macd = state["ema_12"] - state["ema_26"]

    result = {
        **candle,
        "ema_12": state["ema_12"],
        "ema_26": state["ema_26"],
        "macd": macd,
    }

    return (state, result)

with_indicators = op.stateful_map("ema", keyed_candles, calculate_ema)

# ============================================================
# Redis로 실시간 푸시
# ============================================================
class RedisSink:
    def __init__(self, host="localhost", port=6379):
        self.client = redis.Redis(host=host, port=port)

    def write(self, item):
        key, data = item
        redis_key = f"crypto:metrics:{key}"
        self.client.hset(redis_key, mapping={
            "close": data["close"],
            "ema_12": data["ema_12"],
            "ema_26": data["ema_26"],
            "macd": data["macd"],
            "updated_at": data.get("timestamp", ""),
        })
        # TTL 설정 (1시간)
        self.client.expire(redis_key, 3600)

op.output("redis", with_indicators, RedisSink())
```

---

## 3. 기존 aiokafka 패턴과 비교

### 3.1 Producer 패턴 (Phase 1)

**aiokafka 방식** (현재 권장):
```python
# 단순 수집 → aiokafka 유지
async def collect_trades():
    async with websocket.connect(BINANCE_WS) as ws:
        async for msg in ws:
            await producer.send("crypto.trades.raw", msg)
```

**bytewax는 여기선 불필요**:
- 단순 포워딩이라 스트리밍 프레임워크 오버헤드만 추가
- aiokafka가 더 가벼움

### 3.2 Consumer + Processing 패턴 (Phase 2)

**aiokafka + 직접 구현**:
```python
async def process_trades():
    async for msg in consumer:
        trade = parse(msg)
        candle = update_candle(current_candle, trade)
        if should_close_window():
            await emit_candle(candle)
```
- 윈도우 관리 직접 구현 필요
- 상태 복구 직접 구현 필요
- Late 데이터 처리 복잡

**bytewax 사용**:
```python
fold_window("candle", keyed, clock, windower, ...)
```
- 윈도우/워터마크 자동 관리
- 상태 스냅샷 자동
- Late 데이터 분리 스트림

---

## 4. 마이그레이션 전략

### 4.1 단계별 적용

```
Step 1: 병렬 실행 (A/B 테스트)
┌─────────────────────────────────────────────────────────┐
│  Kafka(raw) ─┬─→ [기존 코드] ─→ Kafka(candles.old)     │
│              │                                          │
│              └─→ [bytewax]   ─→ Kafka(candles.new)     │
└─────────────────────────────────────────────────────────┘
→ 결과 비교, 성능 측정

Step 2: 부분 전환
┌─────────────────────────────────────────────────────────┐
│  Kafka(raw) ─→ [bytewax] ─→ Kafka(candles)             │
│                                                         │
│  기존 코드는 백업으로 유지                               │
└─────────────────────────────────────────────────────────┘

Step 3: 완전 전환
┌─────────────────────────────────────────────────────────┐
│  bytewax만 운영                                         │
│  기존 코드 폐기                                          │
└─────────────────────────────────────────────────────────┘
```

### 4.2 실행 방법

```bash
# 개발 (단일 워커)
python -m bytewax.run candle_generator:flow

# 프로덕션 (멀티 워커)
python -m bytewax.run candle_generator:flow -w 4

# Docker로 실행
docker run -v $(pwd):/app bytewax/bytewax \
  python -m bytewax.run /app/candle_generator.py:flow -w 4
```

---

## 5. 폴더 구조 제안

```
realtime-crypto-pipeline/
├── src/
│   ├── collectors/              # Phase 1 (aiokafka 유지)
│   │   └── binance_collector.py
│   │
│   ├── stream_processing/       # Phase 2 (bytewax)
│   │   ├── __init__.py
│   │   ├── candle_generator.py  # 메인 캔들 생성
│   │   ├── realtime_metrics.py  # 실시간 지표
│   │   └── anomaly_detector.py  # 이상 탐지
│   │
│   ├── batch_processing/        # Phase 3 (Spark 또는 bytewax)
│   │   └── daily_aggregator.py
│   │
│   └── serving/                 # Phase 4
│       └── api.py
│
├── docs/
│   └── 02_Kafka/
│       └── bytewax_integration.md  # bytewax 관련 문서
│
└── tests/
    └── test_stream_processing/
        └── test_candle_generator.py
```

---

## 6. 테스트 전략

### 6.1 단위 테스트

```python
# tests/test_stream_processing/test_candle_generator.py

from bytewax.testing import TestingSource, run_main
from stream_processing.candle_generator import (
    parse_trade, update_candle, create_empty_candle
)

def test_parse_trade_valid():
    raw = '{"symbol":"BTCUSD","price":"50000","quantity":"0.1","timestamp":"2024-01-01T00:00:00Z"}'
    result = parse_trade(type("Msg", (), {"value": raw})())
    assert result["symbol"] == "BTCUSD"
    assert result["price"] == 50000.0

def test_parse_trade_invalid():
    raw = '{"invalid": "data"}'
    result = parse_trade(type("Msg", (), {"value": raw})())
    assert result is None

def test_candle_update():
    candle = create_empty_candle()
    trade = {"price": 100, "quantity": 1.0}
    candle = update_candle(candle, trade)

    assert candle["open"] == 100
    assert candle["high"] == 100
    assert candle["low"] == 100
    assert candle["close"] == 100
    assert candle["volume"] == 1.0
```

### 6.2 통합 테스트

```python
def test_full_pipeline():
    from bytewax.testing import TestingSource, run_main
    from bytewax.dataflow import Dataflow
    import bytewax.operators as op

    flow = Dataflow("test")
    source_data = [
        {"symbol": "BTC", "price": 100, "quantity": 1, "timestamp": "..."},
        {"symbol": "BTC", "price": 101, "quantity": 2, "timestamp": "..."},
    ]

    inp = op.input("inp", flow, TestingSource(source_data))
    # ... 파이프라인 구성 ...

    results = []
    op.output("out", processed, lambda x: results.append(x))

    run_main(flow)

    assert len(results) == expected_count
```

---

## 7. 모니터링 및 운영

### 7.1 메트릭 수집

```python
from bytewax.connectors.demo import RandomMetricSource
from opentelemetry import trace, metrics

# bytewax는 OpenTelemetry 지원
# 자동으로 처리량, 지연시간 등 수집
```

### 7.2 알람 설정

```yaml
# 예: Prometheus 알람
- alert: BytewaxLateDataHigh
  expr: bytewax_late_items_total > 100
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Late data rate is high"
```

---

## 8. 결론

### 8.1 bytewax 적용 권장 영역

| 영역 | 권장도 | 이유 |
|------|:------:|------|
| **캔들 생성** | ⭐⭐⭐ | 윈도우 집계의 정석 |
| **실시간 지표** | ⭐⭐⭐ | stateful_map 활용 |
| **이상 탐지** | ⭐⭐ | branch + stateful |
| **데이터 수집** | ⭐ | aiokafka가 더 적합 |

### 8.2 기대 효과

```
1. 코드 간소화
   - 윈도우/워터마크 직접 구현 불필요
   - Late 데이터 처리 자동화

2. 신뢰성 향상
   - 상태 스냅샷 자동화
   - 장애 복구 내장

3. 확장성
   - 워커 수 조절로 수평 확장
   - 키 기반 자동 파티셔닝
```

---

*작성: 2026-01-25*
*다음 단계: my-impl 폴더에 PoC 구현*
