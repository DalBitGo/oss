# OSS 분석 & 재구현 연구소

> 오픈소스를 분석하고, 배우고, 나만의 방식으로 다시 만든다.
> **목표**: 커리어 Gap 해소에 직접 도움이 되는 OSS 우선 분석

---

## 폴더 구조

```
oss/
├── A_streaming/        ⭐ Kafka, 스트리밍 (Gap 2순위)
│   ├── aiokafka/       ✅ 분석 완료
│   ├── bytewax/        ⬜ 1순위 분석 예정
│   └── arroyo/         ⬜ 3순위
│
├── B_batch/            ⭐⭐ Spark, 배치 처리 (Gap 1순위)
│   ├── polars/         ⬜ 2순위 분석 예정
│   └── dbt-core/       ⬜ 4순위
│
├── C_data-lake/        ⭐⭐ Delta Lake, Iceberg (Gap 1순위 연계)
│   └── delta-rs/       ⬜ 1순위 분석 예정
│
├── E_data-quality/     데이터 품질
│   └── great-expectations/ ⬜ 5순위
│
├── F_etc/              기타 (LLM, 크롤링 등 - 커리어 연관 낮음)
│   ├── vanna/          ✅ 분석 완료
│   ├── claude-agent-sdk-python/ ✅ 분석 완료
│   └── ... (7개 더)
│
├── CLAUDE.md           방향 가이드
├── README.md           ← 지금 보는 파일
├── CANDIDATES.md       분석 후보 상세 목록
└── _templates/         분석 템플릿
```

---

## 현재 상태

| 카테고리 | 프로젝트 수 | 분석 완료 | 커리어 Gap |
|----------|:-----------:|:---------:|:----------:|
| **A_streaming** | 3 | 2 (aiokafka, bytewax✅) | 2순위 |
| **B_batch** | 2 | 0 | **1순위** |
| **C_data-lake** | 1 | 0 | **1순위** |
| **E_data-quality** | 1 | 0 | 중간 |
| **F_etc** | 9 | 9 | 낮음 |

---

## 다음 할 일

```
분석 순서:
1. ✅ A_streaming/bytewax  → 완료! (L3 심층 분석)
2. C_data-lake/delta-rs    → Delta Lake (Phase 3 저장소)
3. B_batch/polars          → 고성능 DataFrame
4. B_batch/dbt-core        → 데이터 변환
5. A_streaming/arroyo      → 분산 스트리밍
```

---

## 워크플로우

### 1. 프로젝트 선정
우선순위: A, B, C 카테고리 먼저

### 2. 분석 문서 작성
```bash
# 각 프로젝트의 docs/00_SUMMARY.md 작성
```

### 3. 핵심 패턴 학습
- 아키텍처, 데이터 흐름, 설계 결정

### 4. 프로젝트 적용
- realtime-crypto-pipeline에 배운 패턴 적용

---

## 새 세션 시작할 때

```bash
cat /home/junhyun/oss/CLAUDE.md
ls /home/junhyun/oss/
```

---

*마지막 업데이트: 2026-01-25*
