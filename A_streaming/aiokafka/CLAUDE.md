# aiokafka - OSS 분석 작업 지침

## 프로젝트 개요
| 항목 | 내용 |
|------|------|
| **프로젝트명** | aiokafka |
| **원본 레포** | https://github.com/aio-libs/aiokafka |
| **한 줄 요약** | Python asyncio 기반 Kafka 클라이언트 |
| **커리어 연관** | ⭐⭐⭐ (Kafka Gap 해소, Phase 3 직접 활용) |
| **분석 시작일** | 2026-01-10 |

---

## 현재 상태 (Quick View)

```
분석 레벨: L3 (Deep Dive)
진행률:   ██████████  100%  ✅ 완료
```

### ✅ 분석 완료
- L1: Quick Scan
- L2: Architecture (클라이언트 구조, 프로토콜)
- L3: Deep Dive (Producer, Consumer, Connection)
- realtime-crypto-pipeline에 Producer 패턴 적용

### 🔄 진행 중
- 없음

### ⬜ 예정
- L4는 불필요 (라이브러리 직접 사용)

### 📝 마지막 작업 (2026-01-23)
- Kafka Producer 패턴 분석
- realtime-crypto-pipeline Producer 구현에 적용

### 👉 다음에 할 일
- Consumer 패턴 분석 (Spark 연동 시)

---

## 분석 레벨 현황

| 레벨 | 이름 | 상태 | 산출물 |
|:----:|------|:----:|--------|
| L1 | Quick Scan | ✅ | 한 줄 요약 |
| L2 | Architecture | ✅ | `docs/00_ARCHITECTURE_SUMMARY.md` |
| L3 | Deep Dive | ✅ | `docs/producer_overview.md`, `docs/consumer_overview.md` |
| L4 | Implementation | - | 라이브러리 직접 사용 |

---

## 폴더 구조

```
aiokafka/
├── CLAUDE.md                    # 이 파일
├── original/                    # git submodule
└── docs/
    ├── 00_ARCHITECTURE_SUMMARY.md
    ├── producer_overview.md     # Producer 분석 ✅
    ├── consumer_overview.md     # Consumer 분석 ✅
    ├── client.py.md             # 클라이언트 구조
    ├── conn.py.md               # 연결 관리
    ├── protocol_overview.md     # Kafka 프로토콜
    └── ...
```

---

## 핵심 파일 (분석 대상)

| 파일 | 역할 | 분석 상태 |
|------|------|:--------:|
| `original/aiokafka/producer/producer.py` | AIOKafkaProducer | ✅ |
| `original/aiokafka/consumer/consumer.py` | AIOKafkaConsumer | ✅ |
| `original/aiokafka/client.py` | 클라이언트 기반 클래스 | ✅ |
| `original/aiokafka/conn.py` | 연결 관리 | ✅ |

---

## 핵심 학습 포인트

### 1. asyncio 패턴
- 비동기 컨텍스트 매니저 (`async with`)
- 배치 전송 (linger_ms, batch_size)

### 2. Kafka 프로토콜 이해
- Request/Response 구조
- Metadata, Produce, Fetch API

### 3. 연결 풀 관리
- 브로커별 연결 관리
- 재연결 전략

---

## realtime-crypto-pipeline 연계

### 적용 완료
- **Kafka Producer**: `src/kafka/producer.py`에 aiokafka 패턴 적용
  - 비동기 배치 전송
  - acks=all로 안정성 확보

### 적용 예정
- **Kafka Consumer**: Spark Streaming으로 대체 예정

### 적용 상태
- [x] Producer 패턴 문서화
- [x] Producer 코드 구현
- [ ] 테스트 (docker-compose up 후)

---

## 면접 예상 질문

### Q1: aiokafka를 선택한 이유는?
A: Python asyncio 기반으로 기존 비동기 코드와 자연스럽게 통합. kafka-python은 동기식이라 별도 스레드 필요.

### Q2: Producer 최적화 방법은?
A: linger_ms로 배치 대기, batch_size로 한 번에 전송. acks=all로 안정성과 성능 트레이드오프.

### Q3: 에러 처리는 어떻게?
A: 재시도 로직, DLQ(Dead Letter Queue) 패턴. 연결 끊김 시 자동 재연결.

---

## 참고 자료

### OSS 분석 방법론
- `/home/junhyun/oss/CLAUDE.md`

### 관련 학습 자료
- `/home/junhyun/kb/Kafka-Stream-Processing/`

### 연계 프로젝트
- `/home/junhyun/projects/A_data-engineering/realtime-crypto-pipeline/src/kafka/producer.py`

---

## 히스토리

| 날짜 | 작업 내용 |
|------|----------|
| 2026-01-10 | 분석 시작 |
| 2026-01-15 | L2 아키텍처 분석 완료 |
| 2026-01-20 | L3 Producer/Consumer 분석 완료 |
| 2026-01-23 | realtime-crypto-pipeline Producer 적용 |

---

*이 파일은 Claude가 새 세션마다 읽어서 분석 컨텍스트를 파악합니다.*
