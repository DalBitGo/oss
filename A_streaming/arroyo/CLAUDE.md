# arroyo - OSS 분석 작업 지침

## 프로젝트 개요
| 항목 | 내용 |
|------|------|
| **프로젝트명** | arroyo |
| **원본 레포** | https://github.com/ArroyoSystems/arroyo |
| **한 줄 요약** | Rust 기반 분산 스트림 처리 엔진 (SQL 지원) |
| **커리어 연관** | ⭐⭐ (스트리밍, bytewax 대안) |
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
- L2: Architecture (SQL 엔진, 윈도우 처리)
- bytewax와 비교 분석

### 👉 다음에 할 일
- bytewax 분석 완료 후 비교 분석

---

## 분석 레벨 현황

| 레벨 | 이름 | 상태 | 산출물 |
|:----:|------|:----:|--------|
| L1 | Quick Scan | ✅ | `docs/00_SUMMARY.md` |
| L2 | Architecture | ⬜ | - |
| L3 | Deep Dive | ⬜ | - |
| L4 | Implementation | ⬜ | - |

---

## bytewax와 비교

| 항목 | arroyo | bytewax |
|------|--------|---------|
| 언어 | Rust | Python + Rust |
| API | SQL + Rust | Python |
| 진입장벽 | 높음 | 낮음 |

---

*분석 예정*
