# OSS 분석 후보 목록

> **목적**: 커리어 Gap 해소에 직접 도움이 되는 OSS 우선 분석
> **Last Updated**: 2026-01-25

---

## 분류 체계

```
┌─────────────────────────────────────────────────────────────────┐
│                    OSS 분석 카테고리                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [A] 스트리밍        [B] 배치 처리       [C] 데이터 레이크       │
│  ┌───────────┐       ┌───────────┐       ┌───────────┐         │
│  │ Kafka     │       │ Spark     │       │ Delta Lake│         │
│  │ Flink     │       │ dbt       │       │ Iceberg   │         │
│  │ Bytewax   │       │ Polars    │       │           │         │
│  └───────────┘       └───────────┘       └───────────┘         │
│                                                                 │
│  [D] 오케스트레이션   [E] 데이터 품질      [F] 기타/참고용        │
│  ┌───────────┐       ┌───────────┐       ┌───────────┐         │
│  │ Airflow   │       │ GX        │       │ LLM 관련  │         │
│  │ Dagster   │       │ dbt-test  │       │ 크롤링    │         │
│  └───────────┘       └───────────┘       └───────────┘         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 커리어 Gap 매핑

| Gap 스킬 | 우선순위 | 관련 OSS 카테고리 |
|----------|----------|-------------------|
| **Spark** | 1순위 | [B] 배치 처리, [C] 데이터 레이크 |
| **Kafka** | 2순위 | [A] 스트리밍 |
| **Kubernetes** | 3순위 | 배포/운영 (별도 학습) |
| **dbt** | 4순위 | [B] 배치 처리, [E] 데이터 품질 |

---

## [A] 스트리밍 (Stream Processing) ⭐ 2순위 Gap

### 분석 완료
| 프로젝트 | Stars | 설명 | 분석 문서 |
|----------|-------|------|-----------|
| **aiokafka** | 1.1K | Python asyncio Kafka 클라이언트 | ✅ `aiokafka/docs/` |

### 분석 예정 (높은 우선순위)
| 프로젝트 | Stars | 설명 | 학습 포인트 |
|----------|-------|------|-------------|
| **bytewax** | 1.7K | Python 스트리밍 (Rust 엔진) | Flink 대안, Python 친화적 |
| **arroyo** | 3.7K | 분산 스트림 엔진 (Rust) | SQL 기반 스트리밍, Flink 대안 |
| **faust-streaming** | 1.5K | Python Kafka Streams | Kafka Streams Python 포팅 |

### 참고용 (대규모)
| 프로젝트 | Stars | 설명 | 비고 |
|----------|-------|------|------|
| **apache/kafka** | 29K | Kafka 본체 | Java, 규모 큼 |
| **apache/flink** | 24K | 스트림 처리 엔진 | Java/Scala, 규모 큼 |

---

## [B] 배치 처리 (Batch Processing) ⭐ 1순위 Gap

### 분석 예정 (높은 우선순위)
| 프로젝트 | Stars | 설명 | 학습 포인트 |
|----------|-------|------|-------------|
| **polars** | 32K | 고성능 DataFrame (Rust) | Spark 대안, 최신 패턴 |
| **dbt-core** | 10K | 데이터 변환 프레임워크 | SQL 기반 ELT, 4순위 Gap |
| **duckdb** | 27K | 인메모리 분석 DB | OLAP, Spark 소규모 대안 |

### 참고용 (대규모)
| 프로젝트 | Stars | 설명 | 비고 |
|----------|-------|------|------|
| **apache/spark** | 40K | 분산 처리 엔진 | Scala, 규모 큼 |

---

## [C] 데이터 레이크 (Data Lake) ⭐ 1순위 Gap 연계

### 분석 예정 (높은 우선순위)
| 프로젝트 | Stars | 설명 | 학습 포인트 |
|----------|-------|------|-------------|
| **delta-rs** | 3.1K | Delta Lake Python/Rust | Spark 없이 Delta Lake 사용 |
| **pyiceberg** | 1.2K | Apache Iceberg Python | 테이블 포맷, 시간 여행 |

### 참고용
| 프로젝트 | Stars | 설명 | 비고 |
|----------|-------|------|------|
| **delta-io/delta** | 8.5K | Delta Lake (Scala) | Spark 의존 |
| **apache/iceberg** | 7K | Iceberg 본체 | Java |

---

## [D] 오케스트레이션 (Orchestration)

### 이미 보유한 스킬 (Airflow) - 참고용
| 프로젝트 | Stars | 설명 | 비고 |
|----------|-------|------|------|
| **apache/airflow** | 38K | 워크플로우 오케스트레이션 | 이미 보유 ★★★★☆ |
| **dagster** | 12K | 데이터 오케스트레이션 | Airflow 대안 |
| **prefect** | 18K | 워크플로우 자동화 | Airflow 대안 |

---

## [E] 데이터 품질 (Data Quality)

### 분석 예정 (중간 우선순위)
| 프로젝트 | Stars | 설명 | 학습 포인트 |
|----------|-------|------|-------------|
| **great-expectations** | 10K | 데이터 검증 프레임워크 | 품질 체크, Airflow 연동 |
| **soda-core** | 2.3K | 데이터 품질 검사 | SQL 기반 품질 체크 |

---

## [F] 기타/참고용 (LLM, 크롤링 등)

### 분석 완료 (커리어 연관성 낮음)
| 프로젝트 | Stars | 설명 | 분석 문서 |
|----------|-------|------|-----------|
| mini-sglang | - | LLM 서빙 런타임 | ✅ 완료 |
| crawl4ai | - | LLM 친화적 웹 크롤러 | ✅ 완료 |
| exo | - | 분산 AI 클러스터 | ✅ 완료 |
| unsloth | - | LLM 파인튜닝 최적화 | ✅ 완료 |
| chatterbox | - | TTS 파이프라인 | ✅ 완료 |
| cocoindex | - | 데이터 변환 (Rust) | ✅ 완료 |
| dify | - | 에이전트 워크플로우 | ✅ 완료 |
| vanna | - | Text-to-SQL AI | ✅ 완료 |
| claude-agent-sdk | - | Claude 에이전트 SDK | ✅ 완료 |

---

## 우선순위 정리

### 즉시 분석 (1-2주)
```
1. bytewax      - Python 스트리밍, Phase 3 참고
2. delta-rs     - Delta Lake Python, Phase 3 적용
```

### 단기 분석 (1개월)
```
3. polars       - 고성능 DataFrame, Spark 패턴 이해
4. dbt-core     - 데이터 변환, 4순위 Gap
```

### 중기 분석 (2-3개월)
```
5. arroyo       - 분산 스트리밍, Rust
6. great-expectations - 데이터 품질
```

---

## 참고 자료

### Awesome 리스트
- [awesome-opensource-data-engineering](https://github.com/gunnarmorling/awesome-opensource-data-engineering) - 3K stars
- [awesome-open-source-data-engineering](https://github.com/pracdata/awesome-open-source-data-engineering)
- [awesome-streaming](https://github.com/manuzhang/awesome-streaming)

### 실습 프로젝트 예시
- [e2e-structured-streaming](https://github.com/akarce/e2e-structured-streaming) - Spark + Kafka + Cassandra + Airflow
- [dag-stack](https://github.com/spbail/dag-stack) - dbt + Airflow + Great Expectations
- [open-source-data-stack](https://github.com/luchonaveiro/open-source-data-stack) - Airflow + dbt + GX + Superset

---

## 분석 방법론

```
1. README/Docs 읽기     → 프로젝트 목적 이해
2. 폴더 구조 분석       → 아키텍처 파악
3. 핵심 코드 리딩       → 설계 패턴 학습
4. 문서 작성           → 나만의 언어로 정리
5. my-impl 구현 (선택)  → 직접 적용
```

---

*마지막 업데이트: 2026-01-25*
