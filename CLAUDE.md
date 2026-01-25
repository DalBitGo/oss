# OSS 분석 연구소 - Claude 작업 지침

> **목표**: 커리어 Gap 해소를 위한 체계적인 OSS 분석
> **전략**: 분석 → 패턴 학습 → realtime-crypto-pipeline 적용

---

## 현재 상태 (Quick View)

```
┌─────────────────────────────────────────────────────────────┐
│  OSS 분석 진행률                                             │
│                                                             │
│  A_streaming/     ██████████  2/3 완료 (aiokafka, bytewax✅) │
│  B_batch/         ░░░░░░░░░░  0/2 대기                      │
│  C_data-lake/     ░░░░░░░░░░  0/1 대기                      │
│  E_data-quality/  ░░░░░░░░░░  0/1 대기                      │
│  F_etc/           ██████████  9/9 완료 (커리어 연관 낮음)    │
│                                                             │
│  다음 분석: delta-rs → polars → dbt-core                    │
└─────────────────────────────────────────────────────────────┘
```

### 다음 할 일 (Next Action)
```
→ delta-rs 분석 (Delta Lake Rust 구현)
→ bytewax PoC 구현 (my-impl에 캔들 생성기)
```

---

## 분석 철학

### 핵심 원칙
```
"코드를 읽는 것이 아니라, 설계 의도를 읽는다"
```

### 왜 깊이 있는 분석인가?
```
❌ 얕은 분석의 문제점
   → "이 프로젝트는 스트리밍 처리를 한다" (누구나 아는 것)
   → 면접에서 "그래서 어떻게 동작하나요?"에 답 못함
   → 프로젝트에 적용할 때 막힘

✅ 깊은 분석의 가치
   → "왜 이 구조를 선택했는지" 설명 가능
   → "이 패턴을 내 프로젝트에 이렇게 적용했다" 증명 가능
   → 기술 면접에서 아키텍처 토론 가능
```

### 분석의 3가지 관점
```
1. What  → 이 프로젝트가 무엇을 하는가?
2. How   → 어떻게 구현했는가? (아키텍처, 패턴)
3. Why   → 왜 이렇게 설계했는가? (Trade-off, 의도)

대부분 What에서 멈춤. How와 Why까지 가야 진짜 이해.
```

---

## 분석 깊이 레벨

| 레벨 | 이름 | 목표 | 산출물 | 언제 사용 |
|:----:|------|------|--------|----------|
| **L1** | Quick Scan | 관심 판단 | 한 줄 요약 | 30분, 처음 볼 때 |
| **L2** | Architecture | 구조 이해 | 00_ARCHITECTURE_SUMMARY.md | 2-4시간, 기본 |
| **L3** | Deep Dive | 핵심 모듈 완전 이해 | 모듈별 상세 문서 | 1-2일, 핵심 OSS |
| **L4** | Implementation | 직접 구현 능력 | my-impl/ 코드 | 3-5일, 적용할 때 |

---

## L1: Quick Scan (30분)

### 목표
```
이 프로젝트를 계속 분석할 가치가 있는가?
```

### 체크리스트
```
□ README.md 읽기
□ 폴더 구조 확인 (ls -la)
□ GitHub Stars, 최근 커밋 확인 (활성도)
□ "이게 뭐하는 프로젝트인지" 한 줄 정리
□ 커리어 연관성 판단 (계속 볼지 말지)
```

### 결과물
```
프로젝트명: bytewax
한 줄 요약: Python + Rust 하이브리드 스트리밍 프레임워크
커리어 연관: ⭐⭐⭐ (Kafka 스트리밍 Gap과 직결)
계속 분석: Yes → L2 진행
```

---

## L2: Architecture Analysis (2-4시간)

### 목표
```
전체 구조를 그림으로 그릴 수 있는가?
주요 컴포넌트 간 관계를 설명할 수 있는가?
```

### 분석 프레임워크

#### 2.1 계층 구조 파악
```
질문:
- 이 프로젝트는 몇 개의 레이어로 구성되어 있는가?
- 각 레이어의 책임은 무엇인가?
- 레이어 간 의존성 방향은?

예시 (bytewax):
┌──────────────────────────┐
│  User API (Python)       │  ← 사용자가 보는 것
├──────────────────────────┤
│  Operators (Python)      │  ← 데이터 변환
├──────────────────────────┤
│  Engine (Rust + PyO3)    │  ← 실행
├──────────────────────────┤
│  Timely Dataflow (Rust)  │  ← 분산 처리
└──────────────────────────┘
```

#### 2.2 핵심 컴포넌트 식별
```
질문:
- 가장 중요한 클래스/모듈 3-5개는?
- 각각의 책임(SRP)은?
- 서로 어떻게 협력하는가?

예시:
| 컴포넌트 | 책임 | 핵심 파일 |
|---------|------|----------|
| Dataflow | 파이프라인 정의 | dataflow.py |
| Stream | 데이터 흐름 | dataflow.py |
| Operators | 변환 로직 | operators/__init__.py |
```

#### 2.3 데이터 흐름 추적
```
질문:
- 데이터가 어디서 들어오는가? (Source)
- 어떻게 변환되는가? (Transform)
- 어디로 나가는가? (Sink)
- 상태(State)는 어디에 저장되는가?

다이어그램으로 그리기:
[Source] → [Op1] → [Op2] → [State] → [Sink]
              ↓        ↑
           [Side Output]
```

#### 2.4 기술 스택 분석
```
질문:
- 왜 이 언어/프레임워크를 선택했는가?
- 핵심 의존성은 무엇이고, 왜 그것을 썼는가?
- 빌드/배포는 어떻게 하는가?

예시:
| 기술 | 선택 이유 |
|------|----------|
| Rust | 성능, 메모리 안전성 |
| PyO3 | Python ↔ Rust 바인딩 |
| Timely | 검증된 분산 데이터플로우 |
```

### L2 산출물: 00_ARCHITECTURE_SUMMARY.md
```markdown
# {프로젝트} 아키텍처 요약

## 1. 한 줄 요약
## 2. 서비스 의도 (왜 만들었나)
## 3. 아키텍처 다이어그램
## 4. 핵심 컴포넌트
## 5. 데이터 흐름
## 6. 기술 스택
## 7. 학습 포인트
## 8. 적용 가능성
```

---

## L3: Deep Dive Analysis (1-2일)

### 목표
```
핵심 모듈의 내부 동작을 완전히 이해했는가?
"이게 왜 이렇게 구현되어 있지?"에 답할 수 있는가?
면접에서 이 기술을 설명할 수 있는가?
```

### L3 분석 프레임워크

#### 3.1 핵심 모듈 선정
```
기준:
- 파일 크기가 큰 것 (복잡한 로직)
- 프로젝트의 핵심 기능을 담당하는 것
- 내가 배우고 싶은 패턴이 있는 것

예시 (bytewax):
1. operators/__init__.py (3007 lines) → Stateless/Stateful 연산자
2. operators/windowing.py (2286 lines) → 윈도우 처리
3. dataflow.py (716 lines) → @operator 데코레이터
```

#### 3.2 인터페이스 먼저, 구현은 나중에
```
순서:
1. 이 모듈의 public API는 무엇인가?
2. 사용자는 이걸 어떻게 쓰는가? (예제 코드)
3. 내부적으로 어떻게 동작하는가?

예시:
# 1. Public API
fold_window(step_id, stream, clock, windower, builder, folder, merger)

# 2. 사용 예시
candles = fold_window("ohlcv", prices, EventClock(...), TumblingWindower(...), ...)

# 3. 내부 동작
Clock.on_item() → Windower.open_for() → WindowLogic.on_value() → ...
```

#### 3.3 핵심 클래스 분석 템플릿
```markdown
### 클래스명: StatefulBatchLogic

**책임**: 상태 기반 배치 처리의 핵심 인터페이스

**왜 이렇게 설계했는가?**
- 배치 단위 처리로 Python ↔ Rust 오버헤드 감소
- 스냅샷 메서드로 장애 복구 지원
- RETAIN/DISCARD로 메모리 누수 방지

**핵심 메서드**:
| 메서드 | 역할 | 언제 호출되나 |
|--------|------|--------------|
| on_batch() | 배치 처리 | 데이터 도착 시 |
| on_notify() | 타이머 | notify_at() 시각 경과 시 |
| on_eof() | 종료 처리 | 스트림 끝 |
| snapshot() | 상태 저장 | 주기적 체크포인트 |

**코드 스니펫**:
```python
class StatefulBatchLogic(ABC):
    @abstractmethod
    def on_batch(self, values: List[V]) -> Tuple[Iterable[W], bool]:
        """(출력값들, 폐기여부) 반환"""
```

**실제 구현 예시**: _CollectLogic, _JoinLogic, _WindowLogic
```

#### 3.4 디자인 패턴 식별
```
찾아볼 패턴:
- Factory: 객체 생성 추상화
- Strategy: 알고리즘 교체 가능
- Template Method: 골격 정의, 세부 구현 위임
- Observer: 이벤트 기반 처리
- Composite: 트리 구조 처리

예시 (bytewax):
- Clock + Windower + WindowLogic = Strategy 패턴 조합
- @operator 데코레이터 = Factory 패턴
- StatefulBatchLogic = Template Method 패턴
```

#### 3.5 Trade-off 분석
```
질문:
- 이 설계의 장점은?
- 이 설계의 단점은?
- 다른 선택지는 없었을까?
- 왜 이 방식을 선택했을까?

예시:
| 선택 | 장점 | 단점 | 왜 선택했나 |
|------|------|------|------------|
| Python API + Rust Engine | 사용 편의성 + 성능 | 복잡성, PyO3 오버헤드 | Python 생태계 활용 |
| 배치 단위 처리 | 성능 최적화 | 지연 증가 | GIL 오버헤드 감소 |
| 문자열 키만 지원 | 일관된 해싱 | 유연성 감소 | 분산 처리 안정성 |
```

#### 3.6 면접 예상 질문 정리
```
모듈 분석 후 반드시 작성:

Q: 이 프로젝트의 핵심 아키텍처는?
A: ...

Q: 왜 이렇게 설계했는가?
A: ...

Q: 다른 방식 대비 장단점은?
A: ...

Q: 실제로 어떻게 활용했는가?
A: realtime-crypto-pipeline에서 ...
```

### L3 산출물: 모듈별 상세 문서
```
docs/
├── 00_ARCHITECTURE_SUMMARY.md  (L2)
├── 01_WINDOWING_DEEP_DIVE.md   (L3)
├── 02_OPERATORS_DEEP_DIVE.md   (L3)
└── 03_APPLICATION_GUIDE.md     (적용)
```

---

## L4: Implementation (3-5일)

### 목표
```
핵심 기능을 직접 구현할 수 있는가?
원본과 비교하여 개선점을 도출할 수 있는가?
```

### 구현 접근법
```
1. 전체 클론: 원본을 그대로 재구현
   → 학습 효과 높음, 시간 많이 소요

2. 핵심만 추출: 필요한 부분만 구현
   → 실용적, 적용하기 좋음

3. 변형/개선: 원본 아이디어 + 내 개선
   → 포트폴리오에 가장 좋음
```

### my-impl 폴더 구조
```
my-impl/
├── README.md           # 구현 목표, 원본과 차이점
├── src/
│   └── ...
├── tests/
│   └── ...
└── COMPARISON.md       # 원본 vs 내 구현 비교
```

---

## 분석 실행 절차

### Phase 1: 프로젝트 셋업
```bash
# 1. 폴더 생성
cd /home/junhyun/oss/{카테고리}/
mkdir -p {프로젝트명}/{docs,my-impl}

# 2. 원본 클론 (최신 커밋만)
cd {프로젝트명}
git clone --depth 1 {repo-url} original

# 3. 기본 정보 확인
ls -la original/
du -sh original/*/
cat original/README.md
```

### Phase 2: 구조 분석
```bash
# 1. 진입점 찾기
# Python: __main__.py, main.py, cli.py
# Rust: main.rs, lib.rs

# 2. 핵심 파일 식별 (라인 수 기준)
find original/src -name "*.py" -o -name "*.rs" | xargs wc -l | sort -n | tail -20

# 3. 의존성 확인
# Python: pyproject.toml, requirements.txt
# Rust: Cargo.toml
```

### Phase 3: 코드 분석
```
1. L2 분석 (전체 구조)
   → 00_ARCHITECTURE_SUMMARY.md 작성

2. L3 분석 (핵심 모듈)
   → 모듈별 상세 문서 작성

3. 적용 가이드 작성
   → realtime-crypto-pipeline 연계
```

### Phase 4: 문서 작성 및 업데이트
```
1. docs/ 폴더에 분석 문서 저장
2. README.md 상태 업데이트
3. CLAUDE.md 진행 상황 업데이트
```

---

## 분석 시 항상 물어볼 질문

### 아키텍처 이해
```
- 이 프로젝트의 핵심 추상화는 무엇인가?
- 레이어/모듈 간 경계는 어디인가?
- 확장 포인트는 어디인가?
```

### 설계 의도
```
- 왜 이런 구조를 선택했을까?
- 어떤 Trade-off가 있었을까?
- 다른 선택지는 뭐가 있었을까?
```

### 코드 품질
```
- 어떤 디자인 패턴을 사용했는가?
- 테스트는 어떻게 구성되어 있는가?
- 에러 처리는 어떻게 하는가?
```

### 실용성
```
- 이 패턴을 내 프로젝트에 어떻게 적용할까?
- 이 기술로 면접에서 어떤 질문이 나올까?
- 이걸 배워서 뭘 할 수 있게 되었나?
```

---

## 폴더 구조

```
oss/
├── CLAUDE.md           ← 지금 보는 파일 (작업 지침)
├── README.md           전체 현황
├── CANDIDATES.md       분석 후보 상세
├── _templates/         분석 템플릿
│   └── ANALYSIS_TEMPLATE.md
│
├── A_streaming/        ⭐ Kafka, 스트리밍 (Gap 2순위)
│   ├── aiokafka/       ✅ L3 완료
│   ├── bytewax/        ✅ L3 완료
│   └── arroyo/         ⬜ 대기
│
├── B_batch/            ⭐⭐ Spark, 배치 처리 (Gap 1순위)
│   ├── polars/         ⬜ 대기
│   └── dbt-core/       ⬜ 대기
│
├── C_data-lake/        ⭐⭐ Delta Lake (Gap 1순위 연계)
│   └── delta-rs/       ⬜ 대기
│
├── E_data-quality/     데이터 품질
│   └── great-expectations/
│
└── F_etc/              기타 (커리어 연관 낮음)
    └── [9개 프로젝트]  ✅ 완료
```

### 프로젝트 내부 구조
```
{프로젝트명}/
├── original/           # git clone 원본 (읽기 전용)
├── docs/               # 분석 문서
│   ├── 00_ARCHITECTURE_SUMMARY.md   # L2 필수
│   ├── 01_{모듈}_DEEP_DIVE.md       # L3
│   ├── 02_{모듈}_DEEP_DIVE.md       # L3
│   └── 0N_APPLICATION_GUIDE.md      # 적용 가이드
└── my-impl/            # 직접 구현 (L4)
```

---

## 커리어 Gap 매핑

| Gap 스킬 | 우선순위 | 카테고리 | OSS | 분석 레벨 |
|----------|:--------:|----------|-----|:--------:|
| **Spark** | 1순위 | B_batch | polars | L3 예정 |
| **Kafka** | 2순위 | A_streaming | aiokafka ✅, bytewax ✅ | L3 완료 |
| **dbt** | 4순위 | B_batch | dbt-core | L2 예정 |
| **Data Lake** | 연계 | C_data-lake | delta-rs | L3 예정 |

---

## realtime-crypto-pipeline 연계

> OSS 분석 결과를 프로젝트에 직접 적용

### 연계 원칙
```
분석만 하면 50%. 적용해야 100%.

모든 분석 문서에 반드시 포함:
- "이 패턴을 내 프로젝트에 어떻게 쓸까?"
- 구체적인 코드 예시
- 적용 후 예상 효과
```

### 현재 연계 현황

| OSS | Phase | 적용 상태 | 적용 내용 |
|-----|:-----:|:--------:|----------|
| **aiokafka** | 3 | ✅ 적용 | Kafka Producer 패턴 |
| **bytewax** | 3 | ✅ 검토완료 | 캔들 생성, 실시간 지표 파이프라인 설계 |
| **delta-rs** | 3 | ⬜ 예정 | Delta Lake 저장소 |

### 적용 문서 위치
```
/home/junhyun/projects/realtime-crypto-pipeline/
├── CLAUDE.md           # 프로젝트 작업 지침
└── docs/
    ├── 00_공통/
    │   └── 개발_방법론.md
    └── 02_Kafka/       # aiokafka 패턴 적용
```

---

## 분석 품질 체크리스트

### L2 완료 기준
```
□ 전체 아키텍처 다이어그램 있음
□ 핵심 컴포넌트 3-5개 식별
□ 데이터 흐름 설명 가능
□ 기술 스택 + 선택 이유 정리
□ 학습 포인트 3개 이상
□ 적용 가능성 검토
```

### L3 완료 기준
```
□ 핵심 모듈 2-3개 상세 분석
□ 각 모듈의 인터페이스 정리
□ 핵심 클래스 분석 (책임, 메서드, 코드)
□ 디자인 패턴 식별
□ Trade-off 분석
□ 면접 예상 질문 5개 이상
□ realtime-crypto-pipeline 적용 가이드
```

### L4 완료 기준
```
□ my-impl/ 코드 작성
□ 테스트 코드 포함
□ 원본과 비교 문서
□ 개선점/차이점 정리
```

---

## Claude 작업 요청 예시

```
"delta-rs L2 분석해줘"
"bytewax 윈도우 처리 심층 분석해줘 (L3)"
"polars의 핵심 패턴을 realtime-crypto-pipeline에 어떻게 적용할 수 있을까?"
"지금까지 분석한 OSS에서 배운 패턴 정리해줘"
"면접에서 bytewax 설명할 때 뭘 강조해야 할까?"
```

---

## 참고

### 프로젝트 연계
- `/home/junhyun/projects/realtime-crypto-pipeline/CLAUDE.md` - 프로젝트 작업 지침
- `/home/junhyun/career-hub/SKILL_GAP_ANALYSIS.md` - Gap 스킬 상세

### 학습 자료
- `/home/junhyun/kb/Kafka-Stream-Processing/` - Kafka 가이드
- `/home/junhyun/kb/Apache-Spark/` - Spark 가이드

---

*마지막 업데이트: 2026-01-25*
*다음 분석: delta-rs (L2/L3)*
