# bytewax - OSS 분석 작업 지침

## 프로젝트 개요
| 항목 | 내용 |
|------|------|
| **프로젝트명** | bytewax |
| **원본 레포** | https://github.com/bytewax/bytewax |
| **한 줄 요약** | Python + Rust 하이브리드 스트리밍 프레임워크 |
| **커리어 연관** | ⭐⭐⭐ (Kafka/스트리밍 Gap 해소) |
| **분석 시작일** | 2026-01-15 |

---

## 현재 상태 (Quick View)

```
분석 레벨: L3 (Deep Dive)
진행률:   ██████████  100%  ✅ 완료
```

### ✅ 분석 완료
- L1: Quick Scan (프로젝트 개요 파악)
- L2: Architecture (전체 구조, 컴포넌트)
- L3: Deep Dive (윈도우 처리, 연산자)
- 적용 가이드 작성

### 🔄 진행 중
- 없음

### ⬜ 예정
- L4: my-impl 직접 구현 (캔들 생성기)

### 📝 마지막 작업 (2026-01-25)
- 윈도우 처리 심층 분석 완료
- realtime-crypto-pipeline 적용 가이드 작성

### 👉 다음에 할 일
- my-impl에 캔들 생성 PoC 구현

---

## 분석 레벨 현황

| 레벨 | 이름 | 상태 | 산출물 |
|:----:|------|:----:|--------|
| L1 | Quick Scan | ✅ | 한 줄 요약 |
| L2 | Architecture | ✅ | `docs/00_ARCHITECTURE_SUMMARY.md` |
| L3 | Deep Dive | ✅ | `docs/01_WINDOWING_DEEP_DIVE.md`, `docs/02_OPERATORS_DEEP_DIVE.md` |
| L4 | Implementation | ⬜ | `my-impl/` |

---

## 폴더 구조

```
bytewax/
├── CLAUDE.md                              # 이 파일
├── original/                              # git submodule
├── docs/
│   ├── 00_ARCHITECTURE_SUMMARY.md         # L2 ✅
│   ├── 00_SUMMARY.md                      # 요약
│   ├── 01_WINDOWING_DEEP_DIVE.md          # L3 ✅
│   ├── 02_OPERATORS_DEEP_DIVE.md          # L3 ✅
│   └── 03_REALTIME_CRYPTO_PIPELINE_APPLICATION.md  # 적용 ✅
└── my-impl/                               # L4 예정
```

---

## 핵심 파일 (분석 대상)

| 파일 | 역할 | 분석 상태 |
|------|------|:--------:|
| `original/pysrc/bytewax/dataflow.py` | Dataflow API, @operator | ✅ |
| `original/pysrc/bytewax/operators/__init__.py` | 연산자 정의 | ✅ |
| `original/pysrc/bytewax/operators/windowing.py` | 윈도우 처리 | ✅ |

---

## 핵심 학습 포인트

### 1. Strategy 패턴 조합 (Clock + Windower + Logic)
- 시간, 윈도우, 집계를 분리해서 조합 가능하게 설계
- 새로운 윈도우 타입 추가 시 기존 코드 수정 불필요

### 2. Python + Rust 하이브리드
- Python API로 사용 편의성
- Rust Engine으로 고성능
- PyO3로 연결

### 3. 배치 단위 처리 (StatefulBatchLogic)
- Python ↔ Rust 전환 오버헤드 감소
- GIL 문제 회피

---

## realtime-crypto-pipeline 연계

### 적용 가능한 패턴
- **윈도우 처리**: 1분/5분 캔들 생성
- **상태 관리**: OHLCV 집계
- **이벤트 시간**: EventClock으로 순서 보장

### 적용 상태
- [x] 패턴 문서화 (`docs/03_...APPLICATION.md`)
- [ ] 프로젝트에 적용 (Phase 3)
- [ ] 테스트

---

## 면접 예상 질문

### Q1: bytewax의 핵심 아키텍처는?
A: Python API + Rust Engine 하이브리드. Timely Dataflow 기반 분산 처리.

### Q2: 왜 이렇게 설계했는가?
A: Python 생태계 활용 + 고성능 둘 다 필요. 순수 Python은 GIL 한계, JVM은 Python 친화적이지 않음.

### Q3: 윈도우 처리를 어떻게 구현했는가?
A: Clock + Windower + WindowLogic 3분법. Strategy 패턴으로 조합 가능. TumblingWindow, SessionWindow 등 쉽게 교체.

### Q4: 실제로 어떻게 활용했는가?
A: realtime-crypto-pipeline에서 실시간 캔들 생성에 적용 예정. EventClock + TumblingWindower 조합.

---

## 참고 자료

### OSS 분석 방법론
- `/home/junhyun/oss/CLAUDE.md` - 분석 철학 및 방법론

### 관련 학습 자료
- `/home/junhyun/kb/Kafka-Stream-Processing/` - 스트리밍 개념

### 연계 프로젝트
- `/home/junhyun/projects/A_data-engineering/realtime-crypto-pipeline/`

---

## 히스토리

| 날짜 | 작업 내용 |
|------|----------|
| 2026-01-15 | 분석 시작, L1 완료 |
| 2026-01-20 | L2 아키텍처 분석 완료 |
| 2026-01-25 | L3 윈도우/연산자 심층 분석 완료 |

---

*이 파일은 Claude가 새 세션마다 읽어서 분석 컨텍스트를 파악합니다.*
