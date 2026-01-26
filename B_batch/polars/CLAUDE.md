# polars - OSS 분석 작업 지침

## 프로젝트 개요
| 항목 | 내용 |
|------|------|
| **프로젝트명** | polars |
| **원본 레포** | https://github.com/pola-rs/polars |
| **한 줄 요약** | Rust 기반 고성능 DataFrame 라이브러리 |
| **커리어 연관** | ⭐⭐ (Spark 대안, 배치 처리) |
| **분석 시작일** | - |

---

## 현재 상태 (Quick View)

```
분석 레벨: L1 (Quick Scan)
진행률:   ██░░░░░░░░  20%
```

### ✅ 분석 완료
- L1: Quick Scan

### ⬜ 예정
- L2: Architecture (Lazy vs Eager, 쿼리 최적화)
- L3: Deep Dive (표현식, 윈도우 함수)

### 👉 다음에 할 일
- Spark vs Polars 비교 분석

---

## 분석 레벨 현황

| 레벨 | 이름 | 상태 | 산출물 |
|:----:|------|:----:|--------|
| L1 | Quick Scan | ✅ | `docs/00_SUMMARY.md` |
| L2 | Architecture | ⬜ | - |
| L3 | Deep Dive | ⬜ | - |
| L4 | Implementation | ⬜ | - |

---

## realtime-crypto-pipeline 연계

### 적용 가능성
- 배치 분석 시 Pandas 대체
- 대용량 히스토리컬 데이터 처리

---

*분석 예정*
