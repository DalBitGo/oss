# bytewax 원본 vs 내 구현 비교

## 1. 개요

| 항목 | bytewax 원본 | 내 구현 |
|------|-------------|---------|
| **목적** | 범용 스트리밍 프레임워크 | 캔들 생성 특화 |
| **언어** | Python + Rust | Python only |
| **코드 규모** | ~50,000 lines | ~400 lines |
| **의존성** | Timely Dataflow, PyO3 | 없음 (순수 Python) |

---

## 2. 아키텍처 비교

### 2.1 전체 구조

**bytewax 원본**:
```
┌──────────────────────────────────────────────────────────────┐
│                      User API (Python)                       │
├──────────────────────────────────────────────────────────────┤
│  Dataflow │ Stream │ Operators │ Windowing │ Connectors     │
├──────────────────────────────────────────────────────────────┤
│                    PyO3 Binding Layer                        │
├──────────────────────────────────────────────────────────────┤
│                    Rust Engine Core                          │
├──────────────────────────────────────────────────────────────┤
│                   Timely Dataflow (Rust)                     │
└──────────────────────────────────────────────────────────────┘
```

**내 구현**:
```
┌──────────────────────────────────────────────────────────────┐
│                    CandleGenerator API                       │
├──────────────────────────────────────────────────────────────┤
│  WindowManager │ CandleAggregator │ TumblingWindow          │
├──────────────────────────────────────────────────────────────┤
│                   Trade / Candle Models                      │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 핵심 차이점

| 관점 | bytewax | 내 구현 |
|------|---------|---------|
| **분산 처리** | Timely Dataflow 기반 | 단일 프로세스 |
| **상태 관리** | 체크포인트, 복구 지원 | In-memory only |
| **윈도우 타입** | Tumbling, Session, Sliding | Tumbling only |
| **시간 처리** | Clock + Windower + Logic 분리 | 통합 구조 |
| **연산자** | 다양한 연산자 (map, filter, join 등) | 캔들 집계만 |

---

## 3. 컴포넌트 매핑

### 3.1 윈도우 처리

| bytewax 컴포넌트 | 역할 | 내 구현 |
|-----------------|------|---------|
| `Clock` | 이벤트 시간 추출 | `trade.timestamp` 직접 사용 |
| `Windower` | 윈도우 경계 계산 | `TumblingWindow` |
| `WindowLogic` | 집계 로직 | `CandleAggregator` |
| `StatefulBatchLogic` | 상태 관리 | `WindowManager` |

### 3.2 코드 비교: 윈도우 시작 계산

**bytewax 원본** (operators/windowing.py):
```python
class TumblingWindower(Windower):
    def open_for(self, value: V) -> list[_WindowMetadata]:
        # Clock에서 시간 추출은 별도 컴포넌트
        # Windower는 윈도우 계산만 담당
        return [_WindowMetadata(
            open_time=...,
            close_time=...,
            merged_ids=...
        )]
```

**내 구현** (window.py):
```python
class TumblingWindow:
    @staticmethod
    def get_window_start(timestamp: datetime, window_size: timedelta) -> datetime:
        ts_seconds = timestamp.timestamp()
        window_seconds = window_size.total_seconds()
        window_start_seconds = int(ts_seconds // window_seconds) * window_seconds
        return datetime.fromtimestamp(window_start_seconds, tz=timestamp.tzinfo)
```

**차이점**:
- bytewax: Clock과 Windower 분리 (Strategy 패턴)
- 내 구현: 단일 유틸리티 함수로 통합 (단순화)

### 3.3 코드 비교: 집계 로직

**bytewax 원본** (사용 예시):
```python
def fold_window(...):
    # FoldWindowLogic 사용
    # builder: 초기값 생성
    # folder: 값 누적
    # merger: 윈도우 병합 (Late 데이터용)
```

**내 구현** (candle_generator.py):
```python
class CandleAggregator:
    def add_trade(self, trade: Trade) -> None:
        # OHLCV 집계 로직 하드코딩
        if self._first_timestamp is None or ts < self._first_timestamp:
            self.open = price
        self.high = max(self.high, price)
        self.low = min(self.low, price)
        ...
```

**차이점**:
- bytewax: 범용 fold 연산 (임의의 집계 함수)
- 내 구현: OHLCV 특화 (확장성 포기, 단순함 획득)

---

## 4. 설계 결정 비교

### 4.1 Trade-off 분석

| 결정 | bytewax 선택 | 내 선택 | 이유 |
|------|-------------|---------|------|
| **언어** | Python + Rust | Python only | 학습 용이성, 프로토타이핑 |
| **분산** | Timely 기반 분산 | 단일 프로세스 | 범위 제한, 복잡도 감소 |
| **확장성** | Strategy 패턴 조합 | 하드코딩 | 캔들 생성 특화 |
| **Late 처리** | Merger로 업데이트 | 무시 또는 별도 출력 | 단순화 |

### 4.2 무엇을 가져왔는가?

```
✅ 가져온 것:
- Tumbling Window 개념 및 경계 계산 로직
- Watermark 기반 Late 데이터 판별
- 이벤트 시간 기준 OHLCV 집계
- 콜백 기반 출력 패턴

❌ 가져오지 않은 것:
- Rust 엔진 (성능 vs 복잡도)
- 분산 처리 (범위 외)
- Strategy 패턴 분리 (과도한 추상화)
- Session/Sliding 윈도우 (불필요)
```

---

## 5. 학습 포인트

### 5.1 이해한 것

**1. 윈도우 처리의 본질**
```
스트리밍 = 무한 데이터
윈도우 = 유한 구간으로 잘라서 집계

핵심 질문:
- 언제 윈도우를 열 것인가? → 첫 데이터 도착 시
- 언제 윈도우를 닫을 것인가? → Watermark가 윈도우 종료를 넘을 때
- Late 데이터는 어떻게? → 무시 or 별도 처리 or Merger
```

**2. Watermark의 역할**
```
문제: "이 윈도우에 속한 모든 데이터가 도착했는지 어떻게 아나?"
해결: Watermark = "이 시간 이전의 데이터는 다 왔다"는 가정

watermark = max(event_time) - allowed_lateness

윈도우 닫기 조건:
if window.close_time < watermark:
    emit(candle)
    close(window)
```

**3. 이벤트 시간 vs 처리 시간**
```
처리 시간: 서버에 도착한 시간
이벤트 시간: 실제 발생 시간 (trade.timestamp)

캔들 생성에서 이벤트 시간이 중요한 이유:
- 거래가 순서대로 도착하지 않을 수 있음
- 네트워크 지연, 재전송 등
- 정확한 OHLCV를 위해 이벤트 시간 기준 처리 필수
```

### 5.2 새로 배운 것

**1. Strategy 패턴 조합의 장점**
```
bytewax의 Clock + Windower + Logic 분리:

EventClock × TumblingWindower × FoldLogic → 이벤트 시간 + 텀블링 + 집계
SystemClock × SessionWindower × CollectLogic → 처리 시간 + 세션 + 수집

모든 조합이 가능해짐!
```

**2. 배치 처리의 효과**
```
bytewax가 아이템 단위가 아닌 배치 단위 처리를 하는 이유:

Python ↔ Rust 전환 비용이 큼
배치로 묶어서 한 번에 처리하면 오버헤드 감소

StatefulBatchLogic.on_batch(values: List[V])
```

### 5.3 면접에서 설명할 수 있는 것

```
Q: 스트리밍에서 윈도우 처리를 어떻게 구현하셨나요?

A: bytewax를 분석하고 핵심 패턴을 직접 구현했습니다.

1. Tumbling Window로 1분 단위 경계 계산
   - 타임스탬프를 윈도우 크기로 나눈 몫으로 시작 시간 결정

2. Watermark 기반 Late 데이터 처리
   - watermark = 최신 이벤트 시간 - 허용 지연
   - watermark 이전 데이터는 Late로 분류

3. 이벤트 시간 기준 OHLCV 집계
   - 순서가 뒤섞여 도착해도 타임스탬프 기준으로 open/close 결정

코드는 400줄이지만, bytewax의 핵심 개념을 모두 이해하고 적용했습니다.
```

---

## 6. 성능 비교

### 6.1 처리량 (단순 벤치마크)

```python
# 10,000건 Trade 처리 시간 측정
import time
from datetime import datetime, timedelta, timezone

trades = [
    Trade("BTCUSDT", 50000 + i, 0.1,
          datetime(2026, 1, 26, 10, 0, 0, tzinfo=timezone.utc) + timedelta(seconds=i/100))
    for i in range(10000)
]

generator = CandleGenerator(...)

start = time.time()
for t in trades:
    generator.process(t)
generator.flush()
elapsed = time.time() - start

print(f"처리량: {10000/elapsed:.0f} trades/sec")
```

**예상 결과**:
- 내 구현: ~50,000 trades/sec (순수 Python)
- bytewax: ~500,000+ trades/sec (Rust 엔진)

**분석**:
- 내 구현은 학습/프로토타입 용도로 충분
- 프로덕션에서는 bytewax 또는 Rust 구현 권장

### 6.2 메모리 사용

| 시나리오 | 내 구현 | 고려사항 |
|----------|---------|----------|
| 윈도우 1개 | ~1KB | CandleAggregator 인스턴스 |
| 100 심볼 × 10 윈도우 | ~1MB | 충분히 작음 |
| 1000 심볼 × 100 윈도우 | ~100MB | 주의 필요 |

---

## 7. 개선 아이디어

### 7.1 단기 개선

```
1. 여러 윈도우 크기 동시 지원
   - CandleGenerator에 window_sizes: list[timedelta] 파라미터
   - 각 크기별 WindowManager 생성

2. Kafka 연동
   - aiokafka Consumer에서 Trade 읽기
   - Candle을 Kafka Producer로 출력

3. 성능 최적화
   - dict 대신 __slots__ 사용
   - 타임스탬프 파싱 최적화
```

### 7.2 장기 개선

```
1. Sliding Window 추가
   - 겹치는 윈도우 지원
   - Trade가 여러 윈도우에 속할 수 있음

2. Late 데이터 Merge
   - 닫힌 윈도우에도 Late 데이터 반영
   - 수정된 캔들 재출력

3. 체크포인트 / 복구
   - 윈도우 상태 직렬화
   - 재시작 시 상태 복원
```

---

## 8. 결론

### 8.1 구현 요약

```
목표: bytewax 윈도우 처리 패턴 학습 및 적용
결과: 400줄 Python 코드로 핵심 기능 구현
테스트: 27개 테스트 케이스 통과
```

### 8.2 학습 효과

```
분석만 했을 때: 50% 이해
직접 구현 후: 100% 이해

특히 명확해진 것:
- Watermark가 왜 필요한지
- 윈도우 닫기 타이밍
- 이벤트 시간 처리의 중요성
- Strategy 패턴의 장점
```

### 8.3 realtime-crypto-pipeline 적용

```
Phase 3 적용 계획:

1. Kafka Consumer에서 Trade 수신
2. CandleGenerator로 1분/5분/15분 캔들 생성
3. 생성된 캔들을 DB 저장 또는 Kafka 출력

기대 효과:
- 실시간 차트 데이터 제공
- 기술 지표 계산 기반
```

---

*작성일: 2026-01-26*
*bytewax 분석 완료 후 직접 구현*
