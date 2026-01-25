# bytewax 전체 아키텍처 요약

## 1. 프로젝트 개요

- **GitHub**: https://github.com/bytewax/bytewax
- **Stars**: 1.7K
- **분석 일자**: 2026-01-25
- **한 줄 요약**: **Python + Rust 하이브리드 스트리밍 프레임워크** (Flink/Spark Streaming의 Python 대안)

---

## 2. 서비스 의도

> **이 프로젝트가 해결하려는 문제는 무엇인가?**

### 타겟 사용자
- Python 개발자로서 스트리밍 처리가 필요한 경우
- Flink/Spark를 쓰기엔 너무 무거운 경우
- 기존 Python 라이브러리(pandas, ML 등)를 스트리밍에서 쓰고 싶은 경우

### 핵심 가치
```
"Apache Flink의 기능을 Python에서 쉽게!"
```

| 기존 문제 | bytewax 해결책 |
|-----------|----------------|
| Flink/Spark는 JVM 기반 | Python + Rust 네이티브 |
| Python에서 Kafka Streams 없음 | Python 친화적 API |
| 스트리밍에서 Python 라이브러리 활용 어려움 | 기존 Python 생태계 그대로 활용 |
| 상태 관리 복잡 | 자동 상태 관리 + 복구 |

### 기존 대안 대비 차별점

| 대안 | 단점 | bytewax 장점 |
|------|------|--------------|
| **Apache Flink** | JVM, 무거움, Python API 제한적 | 순수 Python API |
| **Kafka Streams** | Java 전용 | Python 지원 |
| **Spark Streaming** | JVM, 마이크로배치 | 진짜 스트리밍 |
| **Faust** | 순수 Python (성능 제한) | Rust 엔진 (고성능) |

---

## 3. 아키텍처

### 3.1 전체 계층 구조

```
┌─────────────────────────────────────────────────────────────────┐
│  User Application                                               │
│  (Python: Dataflow 정의, operators 사용)                        │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────────┐
│  Python Layer (pysrc/bytewax/)                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Dataflow API                                             │  │
│  │  - Dataflow: 파이프라인 정의                              │  │
│  │  - Stream: 데이터 스트림 핸들                             │  │
│  │  - operators: map, filter, reduce, window 등              │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Connectors                                               │  │
│  │  - inputs.py: Source (Kafka, File, WebSocket)            │  │
│  │  - outputs.py: Sink (Kafka, File, DB)                    │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────┬───────────────────────────────────────────┘
                      │ PyO3 바인딩
┌─────────────────────┴───────────────────────────────────────────┐
│  Rust Layer (src/)                                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Execution Engine                                         │  │
│  │  - operators.rs: 핵심 연산자 구현                         │  │
│  │  - worker.rs: 워커 관리                                   │  │
│  │  - run.rs: 실행 진입점                                    │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Timely Dataflow Integration                             │  │
│  │  - timely.rs: Timely Dataflow 래핑                       │  │
│  │  - recovery.rs: 상태 복구 (67KB!)                        │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────────┐
│  Timely Dataflow (Rust 라이브러리)                              │
│  - 분산 데이터플로우 처리 엔진                                  │
│  - 논리적 시간(epoch) 기반 진행 추적                            │
│  - 워커 간 데이터 교환                                          │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 주요 컴포넌트

| 컴포넌트 | 역할 | 핵심 파일 |
|---------|------|----------|
| **Dataflow** | 파이프라인 정의 | `pysrc/bytewax/dataflow.py` |
| **Stream** | 데이터 스트림 핸들 | `pysrc/bytewax/dataflow.py` |
| **Operators** | 데이터 변환 연산자 | `pysrc/bytewax/operators/__init__.py` |
| **Source/Sink** | 입출력 커넥터 | `pysrc/bytewax/inputs.py`, `outputs.py` |
| **Rust Engine** | 실제 실행 엔진 | `src/operators.rs`, `src/timely.rs` |
| **Recovery** | 상태 복구 | `src/recovery.rs` |

### 3.3 데이터 흐름

```
[Source]          [Operators]           [Sink]
   │                   │                   │
   ▼                   ▼                   ▼
┌─────┐   ┌─────┐   ┌─────┐   ┌─────┐   ┌─────┐
│Kafka│ → │ map │ → │filter│ → │reduce│ → │ DB  │
│File │   │     │   │     │   │     │   │Kafka│
│WS   │   └─────┘   └─────┘   └─────┘   └─────┘
└─────┘

Python: Dataflow 정의 (what)
   ↓
Rust: 실제 실행 (how)
   ↓
Timely: 분산 처리 (where)
```

---

## 4. 기술 스택

| 영역 | 기술 | 선택 이유 (추정) |
|------|------|-----------------|
| **Python API** | Python 3.8+ | 사용자 친화적 |
| **실행 엔진** | Rust | 성능, 메모리 안전성 |
| **Python-Rust 바인딩** | PyO3 | 가장 성숙한 바인딩 |
| **분산 처리** | Timely Dataflow | 검증된 Rust 데이터플로우 엔진 |
| **빌드** | maturin | PyO3 표준 빌드 도구 |

### 핵심 의존성

**Rust (Cargo.toml)**:
- `timely` - 분산 데이터플로우 엔진
- `pyo3` - Python 바인딩
- `chrono` - 시간 처리
- `opentelemetry` - 메트릭/트레이싱

**Python**:
- 최소 의존성 (표준 라이브러리 위주)
- 선택적: `confluent-kafka`, `boto3` 등 커넥터용

---

## 5. 핵심 구현 분석

### 5.1 Dataflow 정의 (Python)

**파일**: `pysrc/bytewax/dataflow.py`

```python
@dataclass(frozen=True)
class Dataflow:
    """Dataflow definition."""
    flow_id: str
    substeps: List[Operator] = field(default_factory=list)
    _scope: _Scope = field(default=None, compare=False)

@dataclass(frozen=True)
class Stream(Generic[X_co]):
    """Handle to a specific stream of items."""
    stream_id: str
    _scope: _Scope = field(compare=False)

    def then(self, op_fn, step_id, *args, **kwargs):
        """Chain a new step onto this stream (fluent API)."""
        return op_fn(step_id, self, *args, **kwargs)
```

**핵심 포인트**:
- `Dataflow`: 전체 파이프라인 컨테이너
- `Stream`: 불변(frozen) 데이터클래스, 체이닝 지원
- `@operator` 데코레이터로 커스텀 연산자 정의 가능

### 5.2 Operators (Python)

**파일**: `pysrc/bytewax/operators/__init__.py`

```python
@operator(_core=True)
def branch(
    step_id: str,
    up: Stream[X],
    predicate: Callable[[X], bool],
) -> BranchOut:
    """Divide items into two streams with a predicate."""
    return BranchOut(
        trues=Stream(f"{up._scope.parent_id}.trues", up._scope),
        falses=Stream(f"{up._scope.parent_id}.falses", up._scope),
    )
```

**주요 연산자**:

| 연산자 | 설명 | 상태 |
|--------|------|------|
| `input` | 소스에서 데이터 읽기 | Stateless |
| `output` | 싱크로 데이터 쓰기 | Stateless |
| `map` | 1:1 변환 | Stateless |
| `flat_map` | 1:N 변환 | Stateless |
| `filter` | 조건 필터링 | Stateless |
| `branch` | 조건 분기 | Stateless |
| `reduce` | 키별 집계 | **Stateful** |
| `fold_window` | 윈도우 집계 | **Stateful** |
| `stateful_map` | 상태 기반 변환 | **Stateful** |

### 5.3 Rust 연산자 구현

**파일**: `src/operators.rs`

```rust
pub(crate) trait BranchOp<S>
where
    S: Scope,
{
    fn branch(
        &self,
        step_id: StepId,
        predicate: TdPyCallable,
    ) -> PyResult<(Stream<S, TdPyAny>, Stream<S, TdPyAny>)>;
}

impl<S> BranchOp<S> for Stream<S, TdPyAny>
where
    S: Scope,
{
    fn branch(...) -> PyResult<(Stream<S, TdPyAny>, Stream<S, TdPyAny>)> {
        // Timely OperatorBuilder 사용
        let mut op_builder = OperatorBuilder::new(...);

        // Python predicate 호출
        Python::with_gil(|py| {
            for item in inbuf.drain(..) {
                let res = pred.call1((item.bind(py),))?;
                if res { trues_session.give(item); }
                else { falses_session.give(item); }
            }
        });
    }
}
```

**핵심 포인트**:
- `Timely Dataflow`의 `OperatorBuilder` 사용
- `Python::with_gil()` - Python GIL 획득 후 Python 함수 호출
- `TdPyAny` - Timely + PyO3 호환 타입

### 5.4 Timely Dataflow 통합

**파일**: `src/timely.rs` (48KB)

Timely Dataflow는 Rust 기반 분산 데이터플로우 엔진:

```
특징:
- Progress Tracking: 논리적 시간(epoch) 기반 진행 추적
- Exchange: 워커 간 데이터 교환
- Pipeline: 로컬 워커 내 데이터 전달
- Frontier: 완료된 epoch 추적
```

### 5.5 상태 복구 (Recovery)

**파일**: `src/recovery.rs` (67KB - 가장 큰 파일!)

```
복구 메커니즘:
1. 상태 스냅샷 (checkpoint)
2. 입력 오프셋 저장
3. 재시작 시 스냅샷 복원
4. 오프셋부터 재처리
```

---

## 6. 핵심 실행 흐름

### 6.1 Dataflow 정의 → 실행

```
┌─────────────────────────────────────────────────────────┐
│  User Code (Python)                                      │
└────────┬────────────────────────────────────────────────┘
         │
         │ flow = Dataflow("my_flow")
         │ s = op.input("inp", flow, KafkaSource(...))
         │ s = op.map("transform", s, my_func)
         │ op.output("out", s, KafkaSink(...))
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│  Dataflow 객체 (Python)                                  │
│  - flow_id: "my_flow"                                   │
│  - substeps: [input, map, output] Operator 리스트       │
└────────┬────────────────────────────────────────────────┘
         │ python -m bytewax.run my_flow.py
         ▼
┌─────────────────────────────────────────────────────────┐
│  run.rs (Rust)                                          │
│  1. Python Dataflow 객체 파싱                           │
│  2. Timely 워커 생성                                    │
│  3. 연산자 그래프 구성                                   │
│  4. 실행 시작                                           │
└────────┬────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│  Timely Dataflow (Rust)                                 │
│  - 워커 스레드 실행                                     │
│  - epoch 단위 데이터 처리                               │
│  - Python 함수 호출 (GIL)                               │
└─────────────────────────────────────────────────────────┘
```

### 6.2 단일 아이템 처리 흐름

```
Kafka Message
     │
     ▼
┌─────────────────┐
│  KafkaSource    │  (Python: 메시지 읽기)
│  - poll()       │
└────────┬────────┘
         │ TdPyAny (Rust 타입)
         ▼
┌─────────────────┐
│  map operator   │  (Rust: 실행, Python: 함수 호출)
│  - Python::with_gil()
│  - mapper.call1()
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  filter operator│
│  - predicate.call1()
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  KafkaSink      │  (Python: 메시지 쓰기)
│  - write()      │
└─────────────────┘
```

---

## 7. 학습 포인트

### Python + Rust 하이브리드 패턴

1. **PyO3 바인딩**: Python ↔ Rust 상호 호출
2. **GIL 관리**: `Python::with_gil()` 안에서만 Python 코드 실행
3. **타입 변환**: `TdPyAny` (Timely + Python Any)

### Dataflow 프로그래밍 모델

1. **Operator**: 데이터 변환의 기본 단위
2. **Stream**: 연산자 간 데이터 흐름
3. **Epoch**: 논리적 시간 단위 (배치 경계)
4. **Frontier**: 완료된 epoch 추적

### 상태 관리 패턴

1. **Keyed State**: 키별 상태 (reduce, fold_window)
2. **Checkpoint**: 주기적 상태 스냅샷
3. **Recovery**: 스냅샷 + 오프셋 기반 복구

### Timely Dataflow

1. **Progress Tracking**: 분산 환경에서 진행 상황 추적
2. **Exchange**: 파티션 재분배 (key 기반)
3. **Pipeline**: 로컬 데이터 전달

---

## 8. realtime-crypto-pipeline 적용 포인트

### 직접 활용 가능

```python
# bytewax로 crypto pipeline 구현 예시
from bytewax.dataflow import Dataflow
from bytewax import operators as op
from bytewax.connectors.kafka import KafkaSource, KafkaSink

flow = Dataflow("crypto_pipeline")

# 1. Kafka에서 가격 데이터 읽기
prices = op.input("prices", flow, KafkaSource(
    brokers=["localhost:9092"],
    topics=["crypto.prices"],
))

# 2. JSON 파싱
parsed = op.map("parse", prices, lambda x: json.loads(x.value))

# 3. 5분 윈도우 집계 (캔들 생성)
candles = op.fold_window(
    "candle",
    parsed,
    clock=SystemClock(),
    windower=TumblingWindow(length=timedelta(minutes=5)),
    builder=lambda: {"open": None, "high": 0, "low": float('inf'), "close": 0},
    folder=update_candle,
)

# 4. 결과 저장
op.output("sink", candles, KafkaSink(...))
```

### 학습할 패턴

| 패턴 | bytewax 구현 | 적용 |
|------|--------------|------|
| **윈도우 집계** | `fold_window` | 캔들 생성 |
| **상태 관리** | `stateful_map` | 이동평균 계산 |
| **분기 처리** | `branch` | 이상 탐지 알림 |
| **멀티 출력** | `output` 여러개 | DB + Kafka 동시 저장 |

---

## 9. 아쉬운 점 / 개선 아이디어

- [ ] Flink 대비 커뮤니티/생태계 작음
- [ ] 대규모 프로덕션 사례 부족
- [ ] Exactly-once 보장 제한적

---

## 10. 내가 배운 것

1. **Python + Rust 하이브리드**가 스트리밍에서도 가능하다
2. **Timely Dataflow** - Rust의 분산 데이터플로우 엔진
3. **Dataflow 프로그래밍 모델** - Flink/Spark와 동일한 개념
4. **상태 복구**가 스트리밍에서 얼마나 복잡한지 (recovery.rs 67KB!)

---

## 11. 분석 문서 목록

### 완료 (L3)
1. **`00_ARCHITECTURE_SUMMARY.md`** (이 문서) - 전체 아키텍처 (L2)
2. **`01_WINDOWING_DEEP_DIVE.md`** - 윈도우 처리 심층 분석 (L3)
   - Clock, Windower, WindowLogic 3분법
   - Watermark 기반 Late 데이터 처리
   - Tumbling, Sliding, Session 윈도우
3. **`02_OPERATORS_DEEP_DIVE.md`** - 연산자 심층 분석 (L3)
   - Stateless/Stateful 연산자 패턴
   - StatefulBatchLogic 인터페이스
   - Join 모드 및 키 라우팅
4. **`03_REALTIME_CRYPTO_PIPELINE_APPLICATION.md`** - 프로젝트 적용 가이드
   - 캔들 생성 파이프라인 예제
   - 실시간 지표 계산 예제
   - 마이그레이션 전략

### 추가 분석 예정
- `recovery.md` - 상태 복구 상세 분석 (src/recovery.rs 67KB)

---

## 12. my-impl 계획

> 이 프로젝트를 참고해서 내가 만들 것

- **목표**: bytewax를 사용한 crypto candle 생성기
- **범위**: 핵심만 (Kafka → 윈도우 집계 → 저장)
- **차별점**: 기존 Phase 3의 Spark 대신 bytewax 테스트

---

*분석 완료: 2026-01-25*
