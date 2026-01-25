# bytewax 연산자 심층 분석 (L3)

> **분석 대상**: `pysrc/bytewax/operators/__init__.py` (3007 lines)
> **핵심 질문**: Stateless/Stateful 연산자를 어떻게 설계했는가?

---

## 1. 연산자 분류 체계

### 1.1 전체 연산자 맵

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          bytewax Operators                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────┐   │
│  │   Core (5)       │  │   Transform (8)  │  │   Stateful (10)      │   │
│  │   _core=True     │  │   Stateless      │  │   키별 상태 유지      │   │
│  ├──────────────────┤  ├──────────────────┤  ├──────────────────────┤   │
│  │ • input          │  │ • map            │  │ • stateful           │   │
│  │ • output         │  │ • flat_map       │  │ • stateful_batch     │   │
│  │ • branch         │  │ • filter         │  │ • stateful_map       │   │
│  │ • merge          │  │ • filter_map     │  │ • stateful_flat_map  │   │
│  │ • redistribute   │  │ • flatten        │  │ • collect            │   │
│  │ • inspect_debug  │  │ • map_value      │  │ • fold_final         │   │
│  │ • flat_map_batch │  │ • flat_map_value │  │ • reduce_final       │   │
│  └──────────────────┘  │ • filter_value   │  │ • join               │   │
│                        └──────────────────┘  │ • count_final        │   │
│                                              │ • max_final          │   │
│  ┌──────────────────┐  ┌──────────────────┐  │ • min_final          │   │
│  │   Key Ops (2)    │  │   Utility (3)    │  └──────────────────────┘   │
│  ├──────────────────┤  ├──────────────────┤                              │
│  │ • key_on         │  │ • inspect        │                              │
│  │ • key_rm         │  │ • raises         │                              │
│  └──────────────────┘  │ • enrich_cached  │                              │
│                        └──────────────────┘                              │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Core vs Non-Core 연산자

```python
# Core 연산자: Rust에서 직접 구현
@operator(_core=True)
def branch(...):
    """Rust 레이어에서 실행"""

# Non-Core 연산자: Python에서 Core 연산자 조합
@operator
def map(...):
    """flat_map_batch(_core) 위에 구현"""
    return flat_map_batch("flat_map_batch", up, shim_mapper)
```

---

## 2. Stateless 연산자 패턴

### 2.1 모든 Stateless 연산자의 기반: flat_map_batch

```python
# operators/__init__.py:180-237
@operator(_core=True)
def flat_map_batch(
    step_id: str,
    up: Stream[X],
    mapper: Callable[[List[X]], Iterable[Y]],  # 배치 단위 처리
) -> Stream[Y]:
    """핵심 Core 연산자 - 다른 Stateless 연산자의 기반"""
    return Stream(f"{up._scope.parent_id}.down", up._scope)
```

**왜 batch 단위인가?**
```
성능 최적화:
- Python ↔ Rust 전환 오버헤드 감소
- GIL 획득 횟수 감소
- 벡터화 연산 가능
```

### 2.2 map 구현 분석

```python
# operators/__init__.py:2498-2555
@operator
def map(
    step_id: str,
    up: Stream[X],
    mapper: Callable[[X], Y],
) -> Stream[Y]:
    """1:1 변환"""

    # 내부적으로 flat_map_batch 사용
    def shim_mapper(xs: List[X]) -> Iterable[Y]:
        return (mapper(x) for x in xs)  # 제너레이터로 지연 평가

    return flat_map_batch("flat_map_batch", up, shim_mapper)
```

**구현 계층**:
```
map
  ↓ 래핑
flat_map_batch (Python Core)
  ↓ PyO3
Rust flat_map_batch_op
  ↓
Timely Dataflow Operator
```

### 2.3 filter와 filter_map

```python
# filter: 조건을 만족하는 항목만 유지
@operator
def filter(step_id, up, predicate):
    def shim_mapper(x):
        if predicate(x):
            return (x,)  # 단일 항목 튜플
        return _EMPTY  # 빈 튜플

    return flat_map("flat_map", up, shim_mapper)


# filter_map: 변환 + 필터링 (None 제거)
@operator
def filter_map(step_id, up, mapper):
    def shim_mapper(x):
        y = mapper(x)
        if y is not None:
            return (y,)
        return _EMPTY

    return flat_map("flat_map", up, shim_mapper)
```

**사용 패턴**:
```python
# filter_map 활용: JSON 파싱 + 유효성 검증
def parse_and_validate(raw):
    try:
        data = json.loads(raw)
        if "price" in data:
            return data
    except:
        pass
    return None  # 무효한 데이터는 제거

valid = op.filter_map("validate", raw_stream, parse_and_validate)
```

---

## 3. Stateful 연산자 패턴

### 3.1 StatefulBatchLogic 인터페이스

```python
# operators/__init__.py:593-793
class StatefulBatchLogic(ABC, Generic[V, W, S]):
    """상태 기반 연산의 핵심 인터페이스"""

    RETAIN: bool = False  # 상태 유지
    DISCARD: bool = True  # 상태 폐기

    @abstractmethod
    def on_batch(self, values: List[V]) -> Tuple[Iterable[W], bool]:
        """배치 처리. (출력값들, 폐기여부) 반환"""

    def on_notify(self) -> Tuple[Iterable[W], bool]:
        """타이머 알림 (기본: 아무것도 안함)"""
        return (_EMPTY, self.RETAIN)

    def on_eof(self) -> Tuple[Iterable[W], bool]:
        """스트림 종료 (기본: 아무것도 안함)"""
        return (_EMPTY, self.RETAIN)

    def notify_at(self) -> Optional[datetime]:
        """다음 알림 시각 (기본: 없음)"""
        return None

    @abstractmethod
    def snapshot(self) -> S:
        """복구용 상태 스냅샷 (반드시 불변!)"""
```

### 3.2 StatefulBatchLogic 실행 흐름

```
┌─────────────────────────────────────────────────────────────┐
│  Key: "BTCUSD" 에 대한 StatefulBatchLogic 인스턴스           │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  1. on_batch([item1, item2, ...])                            │
│     → 배치 처리, 출력 생성                                   │
│     → (outputs, should_discard) 반환                         │
└─────────┬───────────────────────────────────────────────────┘
         │
         ▼ (notify_at() 시각이 지났으면)
┌─────────────────────────────────────────────────────────────┐
│  2. on_notify()                                              │
│     → 타임아웃 처리                                          │
│     → (outputs, should_discard) 반환                         │
└─────────┬───────────────────────────────────────────────────┘
         │
         ▼ (upstream EOF면)
┌─────────────────────────────────────────────────────────────┐
│  3. on_eof()                                                 │
│     → 마지막 처리                                            │
│     → (outputs, should_discard) 반환                         │
└─────────┬───────────────────────────────────────────────────┘
         │
         ▼ (RETAIN이면)
┌─────────────────────────────────────────────────────────────┐
│  4. notify_at()                                              │
│     → 다음 알림 시각 반환                                    │
└─────────────────────────────────────────────────────────────┘
         │
         ▼ (주기적으로)
┌─────────────────────────────────────────────────────────────┐
│  5. snapshot()                                               │
│     → 상태 스냅샷 반환 (복구용)                              │
│     ⚠️ 반드시 copy.deepcopy() 사용!                          │
└─────────────────────────────────────────────────────────────┘
```

### 3.3 collect 연산자 구현 분석

```python
# operators/__init__.py:1107-1219
@dataclass
class _CollectLogic(StatefulLogic[V, List[V], _CollectState[V]]):
    timeout: timedelta
    max_size: int
    state: _CollectState[V]

    def on_item(self, value: V) -> Tuple[Iterable[List[V]], bool]:
        # 타임아웃 갱신
        self.state.timeout_at = self.now_getter() + self.timeout

        # 값 추가
        self.state.acc.append(value)

        # max_size 도달하면 즉시 emit
        if len(self.state.acc) >= self.max_size:
            return ((self.state.acc,), StatefulLogic.DISCARD)

        return (_EMPTY, StatefulLogic.RETAIN)

    def on_notify(self) -> Tuple[Iterable[List[V]], bool]:
        # 타임아웃 시 현재까지 수집된 것 emit
        return ((self.state.acc,), StatefulLogic.DISCARD)

    def on_eof(self) -> Tuple[Iterable[List[V]], bool]:
        # 스트림 종료 시 남은 것 emit
        return ((self.state.acc,), StatefulLogic.DISCARD)

    def notify_at(self) -> Optional[datetime]:
        return self.state.timeout_at
```

**collect 동작**:
```
timeout=10초, max_size=3

입력: [a, b, c, d, e] (1초 간격)

t=0: [a]         (대기, timeout_at = t+10)
t=1: [a, b]      (대기)
t=2: [a, b, c]   → emit [a,b,c], 상태 폐기
t=3: [d]         (새 상태 생성)
t=4: [d, e]      (대기)
...
t=13: notify!    → emit [d,e], 상태 폐기
```

---

## 4. Join 연산자 분석

### 4.1 Join 모드

```python
# operators/__init__.py:2123-2155
JoinInsertMode = Literal["first", "last", "product"]
JoinEmitMode = Literal["complete", "final", "running"]
```

**InsertMode**:
```
same key로 여러 값이 들어올 때:

"first":   첫 번째 값만 유지
"last":    마지막 값으로 덮어쓰기
"product": 모든 조합 생성 (Cartesian product)
```

**EmitMode**:
```
언제 결과를 emit할 것인가:

"complete": 모든 side에 값이 있을 때 (inner join)
"final":    EOF 또는 윈도우 닫힐 때
"running":  값 들어올 때마다 (left/right outer join 유사)
```

### 4.2 _JoinState 구현

```python
# operators/__init__.py:2075-2121
@dataclass
class _JoinState:
    seen: List[List[Any]]  # [side0_values, side1_values, ...]

    @classmethod
    def for_side_count(cls, side_count: int) -> Self:
        return cls([[] for i in range(side_count)])

    def all_set(self) -> bool:
        """모든 side에 값이 있는가?"""
        return all(len(values) > 0 for values in self.seen)

    def astuples(self) -> List[Tuple]:
        """모든 조합 생성"""
        return list(itertools.product(
            *(vals if len(vals) > 0 else [None] for vals in self.seen)
        ))
```

### 4.3 Join 사용 예시

```python
# 가격 스트림과 뉴스 스트림 조인
prices = op.key_on("price_key", price_stream, lambda x: x["symbol"])
news = op.key_on("news_key", news_stream, lambda x: x["symbol"])

# 같은 심볼의 가격과 뉴스를 매칭
joined = op.join(
    "price_news",
    prices, news,
    insert_mode="last",     # 최신 값만
    emit_mode="running",    # 어느 쪽이든 들어오면 emit
)
# 결과: ("BTCUSD", (price_data, news_data))
# news가 없으면: ("BTCUSD", (price_data, None))
```

---

## 5. 키 라우팅 메커니즘

### 5.1 KeyedStream 개념

```python
# operators/__init__.py:77-78
KeyedStream: TypeAlias = Stream[Tuple[str, V]]
# KeyedStream[V] = Stream[(key, value)]
```

**왜 문자열 키인가?**
```
분산 처리에서 키 기반 파티셔닝:
- 해시 기반 파티션 배정
- 같은 키 → 같은 워커
- 상태 격리 보장
```

### 5.2 key_on과 key_rm

```python
# key_on: 키 추가
@operator
def key_on(step_id, up, key: Callable[[X], str]) -> KeyedStream[X]:
    def shim_mapper(x):
        k = key(x)
        if not isinstance(k, str):
            raise TypeError(...)
        return (k, x)
    return map("map", up, shim_mapper)

# key_rm: 키 제거
@operator
def key_rm(step_id, up: KeyedStream[X]) -> Stream[X]:
    def shim_mapper(k_v):
        k, v = k_v
        return v
    return map("map", up, shim_mapper)
```

### 5.3 redistribute 연산자

```python
# operators/__init__.py:498-591
@operator(_core=True)
def redistribute(step_id: str, up: Stream[X]) -> Stream[X]:
    """워커 간 데이터 재분배 (로드 밸런싱)"""
```

**사용 시점**:
```
┌─────────────────────────────────────────────────────────────┐
│  Source (1개) → map → map → map → Stateful(keyed) → Sink   │
│        ↓                             ↓                       │
│  Worker 0만                    모든 Worker에                 │
│  데이터 처리                   키별로 분배                   │
└─────────────────────────────────────────────────────────────┘

문제: Source 직후 map들이 Worker 0에서만 실행됨

해결: redistribute 삽입
Source → redistribute → map → map → Stateful → Sink
         ↓
    랜덤하게 Worker들에 분배
```

---

## 6. @operator 데코레이터 분석

### 6.1 데코레이터 동작

```python
# dataflow.py:697-716
@overload
def operator(builder: F) -> F: ...

@overload
def operator(*, _core: bool = False) -> Callable[[F], F]: ...

def operator(builder=None, *, _core: bool = False) -> Callable:
    """함수를 연산자로 변환"""
    def inner_deco(builder: FunctionType) -> Callable:
        sig = inspect.signature(builder)
        sig_annos = typing.get_type_hints(builder)

        # 1. Operator 데이터클래스 생성
        cls = _gen_op_cls(builder, sig, sig_annos, _core)

        # 2. 래핑 함수 생성
        fn = _gen_op_fn(sig, sig_annos, builder, cls, _core)

        fn._op_cls = cls
        return fn
    ...
```

### 6.2 커스텀 연산자 정의

```python
from bytewax.dataflow import operator, Stream

@operator
def my_custom_op(
    step_id: str,
    up: Stream[X],
    config: MyConfig,
) -> Stream[Y]:
    """내 커스텀 연산자"""

    # 내부적으로 기존 연산자 조합
    filtered = op.filter("filter", up, config.predicate)
    mapped = op.map("map", filtered, config.mapper)

    return mapped
```

---

## 7. realtime-crypto-pipeline 적용 패턴

### 7.1 데이터 정제 파이프라인

```python
from bytewax.dataflow import Dataflow
import bytewax.operators as op

flow = Dataflow("crypto_etl")

# Raw 데이터 입력
raw = op.input("raw", flow, KafkaSource(...))

# 1. JSON 파싱 + 유효성 검증 (filter_map)
def parse_trade(raw_bytes):
    try:
        data = json.loads(raw_bytes)
        if all(k in data for k in ["symbol", "price", "volume", "timestamp"]):
            return data
    except:
        pass
    return None

valid_trades = op.filter_map("parse", raw, parse_trade)

# 2. 키 추가 (심볼별 처리)
keyed = op.key_on("by_symbol", valid_trades, lambda x: x["symbol"])

# 3. 이상치 필터링 (stateful_map으로 이동평균 기반)
def detect_anomaly(state, trade):
    if state is None:
        state = {"ma": trade["price"], "count": 1}
    else:
        # 지수 이동평균
        alpha = 0.1
        state["ma"] = alpha * trade["price"] + (1 - alpha) * state["ma"]
        state["count"] += 1

    # 이동평균에서 20% 이상 벗어나면 이상치
    deviation = abs(trade["price"] - state["ma"]) / state["ma"]
    trade["is_anomaly"] = deviation > 0.2
    trade["ma"] = state["ma"]

    return (state, trade)

enriched = op.stateful_map("anomaly", keyed, detect_anomaly)

# 4. 정상/이상 분기 (branch)
branched = op.branch("split", enriched, lambda x: not x[1]["is_anomaly"])
normal = branched.trues
anomalies = branched.falses

# 5. 각각 다른 출력
op.output("normal_sink", normal, KafkaSink("trades.normal"))
op.output("anomaly_sink", anomalies, KafkaSink("trades.anomaly"))
```

### 7.2 멀티 소스 조인

```python
# 거래소별 가격 스트림 조인
binance = op.input("binance", flow, KafkaSource("binance.trades"))
coinbase = op.input("coinbase", flow, KafkaSource("coinbase.trades"))

binance_keyed = op.key_on("b_key", binance, lambda x: x["symbol"])
coinbase_keyed = op.key_on("c_key", coinbase, lambda x: x["symbol"])

# 같은 심볼의 양쪽 거래소 가격 매칭
joined = op.join(
    "exchange_compare",
    binance_keyed, coinbase_keyed,
    insert_mode="last",
    emit_mode="running",
)

# 차익 계산
def calc_spread(item):
    key, (b_trade, c_trade) = item
    if b_trade and c_trade:
        spread = abs(b_trade["price"] - c_trade["price"])
        return {"symbol": key, "spread": spread, "spread_pct": spread / b_trade["price"]}
    return None

spreads = op.filter_map("spread", joined, calc_spread)
```

---

## 8. 핵심 학습 포인트

### 8.1 연산자 합성 패턴
```
복잡한 연산자 = 단순한 연산자 조합

map = flat_map_batch + 제너레이터
filter = flat_map + 조건부 튜플
collect = stateful + 타이머
join = merge + stateful + 라벨링
```

### 8.2 상태 관리 원칙
```
1. 상태는 항상 키별로 격리
2. snapshot()은 반드시 불변 객체 반환
3. RETAIN/DISCARD로 메모리 누수 방지
4. on_eof()에서 마지막 처리 잊지 말기
```

### 8.3 배치 최적화
```
flat_map_batch가 핵심인 이유:
- Python ↔ Rust 전환 최소화
- GIL 획득 오버헤드 감소
- 벡터화 연산 가능
```

---

## 9. 면접 예상 질문

**Q: Stateless vs Stateful 연산자 차이?**
> Stateless: 각 아이템 독립 처리 (map, filter)
> Stateful: 이전 아이템 정보 유지 (reduce, join, window)
> Stateful은 키별 상태 격리와 복구 메커니즘 필요

**Q: 왜 모든 연산자가 flat_map_batch 기반인가?**
> 성능 최적화. 배치 단위로 Python ↔ Rust 전환하면
> GIL 오버헤드와 PyO3 변환 비용 감소

**Q: KeyedStream의 키가 문자열인 이유?**
> 분산 처리에서 일관된 해싱 보장.
> Python 객체의 __hash__는 실행마다 다를 수 있음

---

*분석 완료: 2026-01-25*
*분석자: Claude Code (L3 Deep Dive)*
