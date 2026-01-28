# Crypto Candle Generator - bytewax my-impl

## 1. 개요

| 항목 | 내용 |
|------|------|
| **원본** | bytewax (https://github.com/bytewax/bytewax) |
| **목적** | bytewax 윈도우 처리 패턴을 학습하고 실제 캔들 생성기 구현 |
| **범위** | 핵심만 추출 - 윈도우 집계 로직만 구현 |
| **적용 대상** | realtime-crypto-pipeline Phase 3 |

### 왜 직접 구현하는가?

```
1. 학습 효과
   - bytewax 분석만으로는 50%, 직접 구현해야 100%
   - 윈도우 처리 로직을 완전히 이해

2. 프로젝트 적용
   - realtime-crypto-pipeline에 바로 적용 가능한 코드
   - Kafka → 캔들 생성 → 저장 파이프라인

3. 포트폴리오
   - "bytewax 분석하고 직접 적용했다" 증명
```

---

## 2. 원본과의 차이점

| 항목 | bytewax 원본 | 내 구현 |
|------|-------------|---------|
| **범위** | 범용 스트리밍 프레임워크 | 캔들 생성 특화 |
| **언어** | Python + Rust | Python only |
| **의존성** | Timely Dataflow | 없음 (순수 Python) |
| **윈도우** | Clock + Windower + Logic 3분법 | 간소화된 TumblingWindow |
| **상태** | 분산 상태 관리 | 단일 프로세스 in-memory |

### 가져오는 패턴

```
✅ 윈도우 처리 개념 (Tumbling Window)
✅ Watermark 기반 Late 데이터 처리
✅ OHLCV 집계 로직
✅ 이벤트 시간 기반 처리

❌ 분산 처리 (Timely Dataflow)
❌ Rust 엔진
❌ 복잡한 상태 복구
```

---

## 3. 핵심 학습 목표

- [ ] Tumbling Window 직접 구현
- [ ] Watermark 기반 Late 데이터 판단
- [ ] OHLCV 캔들 집계 로직
- [ ] Kafka 연동 (Consumer → 처리 → Producer)

---

## 4. 기능 범위

### 4.1 Core 기능

```
1. 캔들 생성기 (CandleGenerator)
   - 입력: Trade 데이터 (symbol, price, volume, timestamp)
   - 출력: OHLCV 캔들 (open, high, low, close, volume)
   - 윈도우: 1분, 5분, 15분 등 설정 가능

2. 윈도우 관리 (WindowManager)
   - Tumbling Window 구현
   - Watermark 추적
   - Late 데이터 처리

3. Kafka 연동 (선택)
   - Consumer: raw trades 읽기
   - Producer: 캔들 출력
```

### 4.2 Out of Scope

```
- 분산 처리
- Exactly-once 보장
- 복잡한 상태 복구
- Session/Sliding 윈도우
```

---

## 5. 기술 스택

| 영역 | 기술 | 이유 |
|------|------|------|
| 언어 | Python 3.10+ | 빠른 프로토타이핑 |
| 메시지 큐 | aiokafka (선택) | 기존 학습 활용 |
| 테스트 | pytest | 표준 |

---

## 6. 실행 방법

```bash
# 단독 실행 (테스트 데이터)
python -m src.candle_generator

# Kafka 연동 실행
python -m src.kafka_pipeline
```

---

## 7. 테스트

```bash
# 전체 테스트
pytest tests/

# 특정 테스트
pytest tests/test_window.py -v
```

---

## 8. 폴더 구조

```
my-impl/
├── README.md               # 이 파일 (PRD)
├── docs/
│   ├── 요구사항.md          # 상세 요구사항
│   ├── 설계.md             # 아키텍처, 클래스 설계
│   └── COMPARISON.md       # 원본 vs 내 구현 비교
├── src/
│   ├── __init__.py
│   ├── candle.py           # OHLCV 캔들 모델
│   ├── window.py           # 윈도우 관리
│   ├── candle_generator.py # 메인 로직
│   └── kafka_pipeline.py   # Kafka 연동 (선택)
└── tests/
    ├── __init__.py
    ├── test_candle.py
    ├── test_window.py
    └── test_generator.py
```

---

## 9. 일정

```
Phase 1: 문서 작성
   - [x] README.md (PRD)
   - [ ] 요구사항.md
   - [ ] 설계.md

Phase 2: 코드 구현
   - [ ] candle.py (모델)
   - [ ] window.py (윈도우)
   - [ ] candle_generator.py (메인)

Phase 3: 테스트 & 검증
   - [ ] 단위 테스트
   - [ ] COMPARISON.md
```

---

## 10. 성공 기준

```
1. 테스트 데이터로 정확한 OHLCV 캔들 생성
2. Late 데이터 올바르게 처리 (또는 식별)
3. bytewax 원본 대비 학습 포인트 3개 이상 정리
4. realtime-crypto-pipeline에 적용 가능한 코드
```

---

*작성일: 2026-01-26*
*다음 단계: docs/요구사항.md 작성*
