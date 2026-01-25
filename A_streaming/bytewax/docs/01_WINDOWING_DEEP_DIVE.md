# bytewax 윈도우 처리 심층 분석 (L3)

> **분석 대상**: `pysrc/bytewax/operators/windowing.py` (2286 lines)
> **핵심 질문**: 스트리밍에서 시간 기반 집계를 어떻게 구현하는가?

---

## 1. 윈도우 처리 아키텍처

### 1.1 3개의 핵심 컴포넌트

```
┌─────────────────────────────────────────────────────────────┐
│                    Window Operator                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │    Clock    │  │   Windower  │  │   WindowLogic       │  │
│  │ (시간 정의) │  │ (윈도우 정의)│  │ (집계 로직)          │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
│         │                │                     │             │
│         ▼                ▼                     ▼             │
│    timestamp,       open_for(),          on_value(),         │
│    watermark        close_for()          on_close()          │
└─────────────────────────────────────────────────────────────┘
```

**왜 이렇게 분리했나?**
```
각 컴포넌트의 관심사 분리:
- Clock: "지금 몇 시인가?" (시간 추출 방법)
- Windower: "이 데이터는 어느 윈도우에 속하는가?" (윈도우 정책)
- WindowLogic: "데이터를 어떻게 집계할 것인가?" (비즈니스 로직)

→ 조합하면 다양한 윈도우 처리 가능
   예: EventClock + TumblingWindower + FoldWindowLogic
```

---

## 2. Clock 시스템 분석

### 2.1 Clock 인터페이스

```python
# windowing.py:78-188
class ClockLogic(ABC, Generic[V, S]):
    """각 키별로 인스턴스화됨"""

    @abstractmethod
    def before_batch(self) -> None:
        """배치 처리 전 현재 시간 캐싱"""

    @abstractmethod
    def on_item(self, value: V) -> Tuple[datetime, datetime]:
        """각 아이템의 (timestamp, watermark) 반환"""

    @abstractmethod
    def on_notify(self) -> datetime:
        """아이템 없이도 watermark 반환 (윈도우 닫기용)"""

    @abstractmethod
    def on_eof(self) -> datetime:
        """스트림 종료 시 watermark (보통 UTC_MAX)"""

    @abstractmethod
    def snapshot(self) -> S:
        """복구용 상태 스냅샷"""
```

### 2.2 SystemClock vs EventClock

#### SystemClock (windowing.py:191-222)
```python
@dataclass
class _SystemClockLogic(ClockLogic[Any, None]):
    """시스템 시간을 타임스탬프로 사용"""
    now_getter: Callable[[], datetime]
    _now: datetime = field(init=False)

    def on_item(self, value: Any) -> Tuple[datetime, datetime]:
        # 모든 아이템에 현재 시스템 시간 부여
        return (self._now, self._now)
```
- **용도**: 데이터에 타임스탬프가 없을 때
- **장점**: 단순함
- **단점**: 처리 지연이 결과에 영향

#### EventClock (windowing.py:231-311)
```python
@dataclass
class _EventClockLogic(ClockLogic[V, _EventClockState]):
    """이벤트 내장 타임스탬프 사용"""
    ts_getter: Callable[[V], datetime]      # 타임스탬프 추출
    wait_for_system_duration: timedelta     # late 데이터 대기 시간

    def on_item(self, value: V) -> Tuple[datetime, datetime]:
        value_event_timestamp = self.ts_getter(value)

        # watermark = 가장 큰 타임스탬프 - 대기시간 + 경과 시간
        watermark = self.state.watermark_base + (
            self._system_now - self.state.system_time_of_max_event
        )
        return value_event_timestamp, watermark
```
- **용도**: 이벤트 시간 기반 처리 (Kafka 메시지의 producer timestamp 등)
- **watermark**: "이 시간 이전의 모든 데이터가 도착했다"는 보장
- **wait_for_system_duration**: 늦게 도착하는 데이터 허용 시간

### 2.3 Watermark 동작 원리

```
시간 축:
|-------|-------|-------|-------|-------|-------|
t0      t1      t2      t3      t4      t5     now

이벤트 도착 순서:
  [t2]  →  [t1]  →  [t3]  →  [t1]  →  [t4]
        (순서 바뀜)      (late!)

wait_for_system_duration = 2초일 때:

watermark 진행:
  t2-2s → t2-2s → t3-2s → t3-2s → t4-2s
  (t2가 최대)     (t3가 최대)

[t1] 두 번째: watermark(t3-2s) > t1 → Late 데이터!
```

---

## 3. Windower 시스템 분석

### 3.1 Windower 인터페이스

```python
# windowing.py:446-595
class WindowerLogic(ABC, Generic[S]):
    """각 키별로 인스턴스화됨"""

    @abstractmethod
    def open_for(self, timestamp: datetime) -> Iterable[int]:
        """이 타임스탬프가 속하는 윈도우 ID들 반환"""

    @abstractmethod
    def late_for(self, timestamp: datetime) -> Iterable[int]:
        """늦은 데이터가 속했을 윈도우 ID들 (메타데이터용)"""

    @abstractmethod
    def merged(self) -> Iterable[Tuple[int, int]]:
        """병합된 윈도우 쌍 반환 (Session 윈도우용)"""

    @abstractmethod
    def close_for(self, watermark: datetime) -> Iterable[Tuple[int, WindowMetadata]]:
        """watermark 이전의 닫을 윈도우들 반환"""
```

### 3.2 윈도우 타입별 구현

#### TumblingWindower (고정 크기, 겹치지 않음)
```python
# windowing.py:896-927
@dataclass
class TumblingWindower(Windower[_SlidingWindowerState]):
    """length 간격으로 나뉜 윈도우"""
    length: timedelta
    align_to: datetime  # 윈도우 시작 기준점

    def build(self, resume_state):
        # SlidingWindower의 특수 케이스 (offset == length)
        return _SlidingWindowerLogic(
            self.length,
            self.length,  # offset = length → 겹치지 않음
            self.align_to,
            state
        )
```

**예시**:
```
align_to = 00:00:00, length = 10분

|-------|-------|-------|-------|
00:00   00:10   00:20   00:30

window_id = (timestamp - align_to) // offset
```

#### SlidingWindower (겹치는 윈도우)
```python
# windowing.py:604-669
@dataclass
class _SlidingWindowerLogic(WindowerLogic[_SlidingWindowerState]):
    length: timedelta
    offset: timedelta   # 윈도우 시작 간격

    def intersects(self, timestamp: datetime) -> List[int]:
        """이 타임스탬프가 속하는 모든 윈도우 ID"""
        since_origin = timestamp - self.align_to
        return list(range(
            (since_origin - self.length) // self.offset + 1,
            since_origin // self.offset + 1,
        ))
```

**예시**:
```
length = 10분, offset = 5분

|---------|         window 0
     |---------|    window 1
          |---------|  window 2

하나의 이벤트가 2개 윈도우에 속할 수 있음
```

#### SessionWindower (세션 기반)
```python
# windowing.py:719-811
@dataclass
class _SessionWindowerLogic(WindowerLogic[_SessionWindowerState]):
    gap: timedelta  # 세션 간 최대 간격

    def open_for(self, timestamp: datetime) -> Iterable[int]:
        for window_id, meta in self.state.sessions.items():
            # 기존 세션 범위 내?
            if meta.open_time <= timestamp <= meta.close_time:
                return (window_id,)
            # gap 이내에 있으면 세션 확장
            elif 0 < (meta.open_time - timestamp) <= self.gap:
                meta.open_time = timestamp
                self._find_merges()  # 세션 병합 확인
                return (window_id,)

        # 새 세션 생성
        self.state.max_key += 1
        return (self.state.max_key,)
```

**예시**:
```
gap = 5분

|--[이벤트1]--|                  session 1
                    |--[이벤트2]--|  session 2 (5분 이상 간격)

|--[이벤트1]--|--[이벤트3]--|     session 1 (5분 이내 → 확장)
```

---

## 4. WindowLogic 구현 패턴

### 4.1 FoldWindowLogic (일반적인 집계)

```python
# windowing.py:1693-1715
@dataclass
class _FoldWindowLogic(WindowLogic[V, S, S]):
    folder: Callable[[S, V], S]   # 값 누적 함수
    merger: Callable[[S, S], S]   # 윈도우 병합 함수
    state: S

    def on_value(self, value: V) -> Iterable[S]:
        # 값 누적 (emit하지 않음)
        self.state = self.folder(self.state, value)
        return _EMPTY  # 빈 튜플

    def on_merge(self, consume: Self) -> Iterable[S]:
        # 세션 병합 시 상태 합치기
        self.state = self.merger(self.state, consume.state)
        return _EMPTY

    def on_close(self) -> Iterable[S]:
        # 윈도우 닫힐 때만 결과 emit
        return (self.state,)
```

### 4.2 윈도우 연산자 전체 흐름

```python
# windowing.py:1047-1191
@dataclass
class _WindowLogic(StatefulBatchLogic):
    clock: ClockLogic
    windower: WindowerLogic
    builder: Callable  # WindowLogic 빌더
    logics: Dict[int, WindowLogic]  # window_id → logic

    def on_batch(self, values: List[V]):
        self.clock.before_batch()

        for value in values:
            timestamp, watermark = self.clock.on_item(value)

            if timestamp < watermark:
                # Late 데이터
                late_ids = self.windower.late_for(timestamp)
                events.extend((id, "L", value) for id in late_ids)
            else:
                # 정상 데이터 → 큐에 추가
                self.queue.append((value, timestamp))

        # 큐에서 due된 항목 처리
        events.extend(self._flush_queue(watermark))
        return events
```

---

## 5. 고급 윈도우 연산자

### 5.1 collect_window (리스트 수집)

```python
# windowing.py:1437-1577
@operator
def collect_window(
    step_id: str,
    up: KeyedStream[V],
    clock: Clock[V, Any],
    windower: Windower[Any],
    into=list,  # list, set, dict 지원
) -> WindowOut[V, Any]:
    """윈도우 내 모든 값을 컬렉션으로 수집"""

    # 내부적으로 fold_window 사용
    return fold_window(
        "fold_window", up, clock, windower,
        builder=list,
        folder=lambda s, v: (s.append(v), s)[1],
        merger=list.__add__,
    )
```

### 5.2 join_window (윈도우 조인)

```python
# windowing.py:2056-2143
@operator
def join_window(
    step_id: str,
    clock: Clock[Any, Any],
    windower: Windower[Any],
    *sides: KeyedStream[Any],
    insert_mode: JoinInsertMode = "last",
    emit_mode: JoinEmitMode = "final",
):
    """여러 스트림을 윈도우 내에서 조인"""

# insert_mode:
#   "first": 각 side의 첫 값만
#   "last": 각 side의 마지막 값만
#   "product": 모든 조합 (Cartesian product)

# emit_mode:
#   "complete": 모든 side에 값이 있을 때만 emit
#   "final": 윈도우 닫힐 때 emit
#   "running": 값 들어올 때마다 emit
```

---

## 6. 상태 스냅샷 및 복구

### 6.1 윈도우 상태 구조

```python
# windowing.py:1033-1038
@dataclass(frozen=True)
class _WindowSnapshot(Generic[V, SC, SW, S]):
    clock_state: SC           # Clock 상태
    windower_state: SW        # Windower 상태 (열린 윈도우들)
    logic_states: Dict[int, S]  # window_id → WindowLogic 상태
    queue: List[Tuple[V, datetime]]  # 버퍼링된 아이템
```

### 6.2 복구 흐름

```
Checkpoint 시:
┌─────────────────────────────────────────────────┐
│  snapshot() 호출                                 │
│                                                 │
│  clock.snapshot() → clock_state                 │
│  windower.snapshot() → windower_state           │
│  for window_id, logic in logics.items():        │
│      logic.snapshot() → logic_states[window_id] │
│  queue → queue 복사                              │
└─────────────────────────────────────────────────┘

재시작 시:
┌─────────────────────────────────────────────────┐
│  build(resume_state) 호출                        │
│                                                 │
│  clock = Clock.build(resume_state.clock_state)  │
│  windower = Windower.build(resume_state.windower_state)
│  logics = {id: builder(s) for id, s in logic_states}
│  queue = resume_state.queue                     │
└─────────────────────────────────────────────────┘
```

---

## 7. realtime-crypto-pipeline 적용

### 7.1 캔들 스틱 생성 (OHLCV)

```python
from datetime import datetime, timedelta, timezone
from bytewax.dataflow import Dataflow
import bytewax.operators as op
from bytewax.operators.windowing import (
    EventClock, TumblingWindower, fold_window
)

flow = Dataflow("crypto_candles")

# 가격 스트림 입력 (key=symbol)
prices = op.input("prices", flow, KafkaSource(...))
keyed = op.key_on("by_symbol", prices, lambda x: x["symbol"])

# 이벤트 시간 기반 Clock
clock = EventClock(
    ts_getter=lambda x: datetime.fromisoformat(x["timestamp"]),
    wait_for_system_duration=timedelta(seconds=10),  # 10초 대기
)

# 5분 윈도우
windower = TumblingWindower(
    length=timedelta(minutes=5),
    align_to=datetime(2024, 1, 1, tzinfo=timezone.utc),
)

# OHLCV 집계
def build_candle():
    return {
        "open": None, "high": float('-inf'),
        "low": float('inf'), "close": None,
        "volume": 0
    }

def update_candle(candle, trade):
    price = trade["price"]
    if candle["open"] is None:
        candle["open"] = price
    candle["high"] = max(candle["high"], price)
    candle["low"] = min(candle["low"], price)
    candle["close"] = price
    candle["volume"] += trade["volume"]
    return candle

def merge_candles(a, b):
    return {
        "open": a["open"],
        "high": max(a["high"], b["high"]),
        "low": min(a["low"], b["low"]),
        "close": b["close"],
        "volume": a["volume"] + b["volume"]
    }

candles = fold_window(
    "candle_agg", keyed, clock, windower,
    builder=build_candle,
    folder=update_candle,
    merger=merge_candles,
)
```

### 7.2 이동 평균 계산 (Session 윈도우 활용)

```python
from bytewax.operators.windowing import SessionWindower

# 사용자 활동 세션 (30분 비활성 시 세션 종료)
session_windower = SessionWindower(gap=timedelta(minutes=30))

# 세션 내 평균 거래량
session_stats = fold_window(
    "session_avg", keyed, clock, session_windower,
    builder=lambda: {"sum": 0, "count": 0},
    folder=lambda s, v: {"sum": s["sum"] + v["volume"], "count": s["count"] + 1},
    merger=lambda a, b: {"sum": a["sum"] + b["sum"], "count": a["count"] + b["count"]},
)
```

### 7.3 Late 데이터 처리

```python
# WindowOut에서 late 스트림 활용
candles_out = fold_window("candle_agg", ...)

# 정상 결과
op.output("main", candles_out.down, KafkaSink("candles"))

# Late 데이터 → DLQ (Dead Letter Queue)
op.output("late_dlq", candles_out.late, KafkaSink("candles.late"))

# 메타데이터 (디버깅/모니터링용)
op.inspect("meta", candles_out.meta)
```

---

## 8. 핵심 학습 포인트

### 8.1 Watermark 기반 Late 데이터 처리
```
Watermark = "이 시간 이전의 모든 데이터는 도착했다"

wait_for_system_duration으로 조절:
- 짧으면: 빠른 결과, 많은 late 데이터
- 길면: 느린 결과, 적은 late 데이터
```

### 8.2 윈도우 조합 패턴
```
Clock     + Windower  = 다양한 윈도우 정책
SystemClock + Tumbling = 처리 시간 기반 고정 윈도우
EventClock  + Sliding  = 이벤트 시간 기반 슬라이딩 윈도우
EventClock  + Session  = 사용자 세션 분석
```

### 8.3 상태 스냅샷의 중요성
```
스트리밍에서 장애 복구:
1. 주기적 상태 스냅샷 저장
2. 입력 오프셋 저장
3. 재시작 시 스냅샷 복원
4. 오프셋부터 재처리

→ Exactly-once 처리 가능
```

---

## 9. 면접 예상 질문

**Q: 스트리밍에서 윈도우 처리란?**
> 무한한 데이터 스트림을 유한한 시간 구간으로 나누어 집계하는 것.
> Tumbling(고정), Sliding(겹침), Session(활동 기반) 윈도우 타입이 있음.

**Q: Watermark란?**
> "이 시간 이전의 모든 이벤트가 도착했다"는 논리적 마커.
> 늦게 도착하는 데이터(late data)를 판단하는 기준점.

**Q: 왜 Clock과 Windower를 분리했는가?**
> 관심사 분리(SRP). Clock은 시간 정의, Windower는 윈도우 정책.
> 조합으로 다양한 처리 방식 구현 가능 (조합 폭발 방지).

---

*분석 완료: 2026-01-25*
*분석자: Claude Code (L3 Deep Dive)*
