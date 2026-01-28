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

## 개발자 사고 흐름 추적 (Developer Thinking Process)

> 코드 뒤에 숨겨진 개발자의 고민 과정을 재구성한다

### 핵심 개념
```
코드는 "결과물"이고, 우리가 알고 싶은 건 "과정"이다.

좋은 개발자 → 문제 인식 → 여러 해결책 고민 → 비교 → 선택 → 구현
                ↑                                    ↓
              우리가 추적해야 할 사고 흐름
```

### 1단계: 문제 재구성 (Problem Reconstruction)

**원래 개발자가 마주한 문제는 무엇이었을까?**

```
역방향 사고:
현재 코드 → 이게 해결하려는 문제가 뭐지?

질문:
- 이 코드가 없었다면 어떤 문제가 있었을까?
- 사용자가 어떤 불편을 겪었을까?
- 기존 해결책은 왜 부족했을까?
```

**예시 (bytewax)**:
```
현재 코드: Python + Rust 하이브리드 아키텍처

문제 재구성:
"Python 개발자가 스트리밍 처리를 하고 싶은데..."
- Flink/Spark는 JVM이라 Python 친화적이지 않음
- 순수 Python (Faust)은 성능이 부족함
- Kafka Streams는 Java 전용

→ 개발자의 고민: "Python 생태계 + 고성능"을 어떻게 둘 다 잡지?
```

### 2단계: 대안 탐색 (Alternative Exploration)

**개발자가 고려했을 다른 선택지는?**

```
"왜 A 대신 B를 선택했을까?"

방법:
1. GitHub Issues에서 "alternative", "why not", "considered" 검색
2. 비슷한 프로젝트와 비교 (왜 그게 아닌 이걸?)
3. 초기 커밋 / RFC 문서 확인
```

**대안 분석 템플릿**:
```
| 대안 | 장점 | 단점 | 왜 선택 안 했나 |
|------|------|------|----------------|
| 순수 Python | 간단함 | 성능 | GIL 한계 |
| 순수 Rust | 성능 | 진입장벽 | Python 생태계 포기 |
| Cython | 절충 | 복잡 | 유지보수 어려움 |
| **PyO3** ✓ | 두 세계 연결 | 복잡성 | → 이게 최선이었음 |
```

### 3단계: 의사결정 과정 재현 (Decision Reconstruction)

**개발자가 어떤 기준으로 결정했을까?**

```
의사결정 프레임워크:

1. 제약 조건 파악
   - 성능 요구사항은?
   - 팀 역량은? (Python만? Rust도?)
   - 시간/리소스 제약은?

2. 우선순위 파악
   - 가장 중요한 품질 속성은?
   - 타협 가능한 것은?

3. 결정 근거 추론
   - "이 상황에서 나라면 어떻게 했을까?"
   - "왜 다른 선택을 안 했을까?"
```

**예시**:
```
bytewax 의사결정 재현:

제약: Python 개발자 타겟, 고성능 필요
우선순위: ① 사용 편의성 ② 성능 ③ 유지보수성

결정 과정 (추정):
1. "Python API는 필수" → 사용자 경험
2. "성능은 Rust로" → 핵심 엔진
3. "PyO3로 연결" → 검증된 바인딩
4. "Timely 활용" → 바퀴 재발명 방지
```

### 4단계: 진화 과정 추적 (Code Archaeology)

**코드가 어떻게 지금 형태가 되었나?**

```bash
# Git 히스토리로 진화 추적
git log --oneline --all | head -50
git log --follow -p -- {핵심파일}

# 주요 변경점 찾기
git log --grep="refactor" --oneline
git log --grep="breaking" --oneline
```

**분석 포인트**:
```
1. 초기 버전은 어땠나?
   - 처음엔 단순했는데 왜 복잡해졌지?
   - 어떤 문제 때문에 바뀌었지?

2. Breaking Changes는 왜?
   - API를 바꾼 이유는?
   - 이전 방식의 한계는?

3. 리팩토링 히스토리
   - 왜 구조를 바꿨지?
   - 어떤 문제를 해결하려 했지?
```

### 5단계: "만약에" 사고 (Counterfactual Thinking)

**다르게 했다면 어떻게 됐을까?**

```
현재 설계에 대해 반대 질문:

Q: "만약 순수 Python으로 만들었다면?"
A: 성능 10배 저하, 대용량 처리 불가

Q: "만약 배치 대신 아이템 단위 처리했다면?"
A: Python ↔ Rust 전환 오버헤드 폭증

Q: "만약 키가 문자열 외에도 가능했다면?"
A: 분산 환경에서 해싱 불일치 문제

→ 현재 설계의 합리성 검증
```

### 6단계: 내 상황에 적용 (Personal Application)

**나라면 어떻게 했을까?**

```
1. 같은 문제를 받았다고 가정
   - 내가 아는 기술로 어떻게 풀었을까?
   - 이 프로젝트의 해결책과 뭐가 다른가?

2. 배운 점 정리
   - 내가 몰랐던 접근법은?
   - 내 프로젝트에 적용 가능한 것은?

3. 비판적 사고
   - 이 설계의 약점은?
   - 내가 개선할 수 있는 부분은?
```

### 사고 흐름 추적 템플릿

```markdown
## 개발자 사고 흐름 분석: {기능/모듈명}

### 1. 원래 문제
- 어떤 상황/불편이 있었나?
- 기존 해결책이 왜 부족했나?

### 2. 고려한 대안들
| 대안 | 검토 결과 | 선택 여부 |
|------|----------|----------|
| A    | 장단점   | ❌ 이유   |
| B    | 장단점   | ✓ 채택   |

### 3. 핵심 의사결정
- 가장 중요하게 생각한 것:
- 타협한 것:
- 결정 근거:

### 4. 진화 과정
- v1: 초기 구현 (단순)
- v2: 문제 발생 → 개선
- v3: 현재 (왜 이 형태?)

### 5. 반사실적 분석
- 만약 X했다면? → 결과 Y
- 현재 설계의 합리성:

### 6. 내 프로젝트 적용
- 배운 것:
- 적용할 것:
- 개선 아이디어:
```

### 실전 예시: bytewax 윈도우 처리

```
[문제 재구성]
"스트리밍에서 시간 기반 집계를 어떻게 하지?"
- 무한 스트림을 유한 구간으로 나눠야 함
- Late 데이터 처리 필요
- 다양한 윈도우 타입 지원 필요

[대안 탐색]
1. 윈도우 로직을 하나의 클래스에 모두 → 복잡, 확장 어려움
2. 시간/윈도우/집계를 분리 → 조합 폭발 가능하지만 유연

[의사결정]
"Clock + Windower + WindowLogic 3분법 선택"
- 이유: Strategy 패턴으로 조합 가능
- Trade-off: 학습 곡선 증가, 유연성 획득

[진화 추적]
- 초기: 단순 TumblingWindow만
- 이후: Session, Sliding 추가 요구
- 현재: 3분법으로 모든 조합 지원

[만약에]
- 하나로 합쳤다면? → 새 윈도우 타입마다 전체 수정
- 분리했기에 → Clock만 바꿔도 이벤트 시간 처리 가능

[내 적용]
- realtime-crypto-pipeline에서 캔들 생성 시
- EventClock + TumblingWindower + FoldWindowLogic 조합 사용
```

---

## 적용하는 검증된 분석 방법론

> 업계에서 검증된 소프트웨어 아키텍처 분석 프레임워크 활용

### 1. C4 Model (Simon Brown)

**개념**: 4단계 줌인 방식의 아키텍처 시각화
```
Level 1: Context   → 시스템이 외부와 어떻게 상호작용하는가?
Level 2: Container → 시스템 내부의 주요 실행 단위는?
Level 3: Component → 컨테이너 내부의 주요 컴포넌트는?
Level 4: Code      → 컴포넌트의 실제 구현은?
```

**우리 분석에 적용**:
```
L1 Quick Scan  ≈ C4 Context (전체 맥락)
L2 Architecture ≈ C4 Container + Component (구조)
L3 Deep Dive   ≈ C4 Code (상세 구현)
```

**다이어그램 예시**:
```
[Context] 사용자 → bytewax → Kafka, DB
[Container] Python API | Rust Engine | Timely Dataflow
[Component] Dataflow | Stream | Operators | Recovery
[Code] StatefulBatchLogic.on_batch() 구현
```

### 2. ATAM (Architecture Tradeoff Analysis Method)

**출처**: Carnegie Mellon SEI (Software Engineering Institute)

**핵심 개념**: 아키텍처 결정의 Trade-off 분석
```
1. 품질 속성 식별 (Quality Attributes)
   - 성능, 확장성, 유지보수성, 보안 등

2. 아키텍처 접근법 분석
   - 이 설계가 어떤 품질 속성을 지원/희생하는가?

3. Trade-off 포인트 식별
   - 두 품질 속성이 충돌하는 지점

4. 리스크 식별
   - 아직 해결 안 된 아키텍처 결정
```

**우리 분석에 적용**:
```
L3 분석 시 반드시 포함:

| 설계 결정 | 얻는 것 | 잃는 것 | 왜 선택했나 |
|-----------|---------|---------|------------|
| Python API + Rust Engine | 사용성 + 성능 | 복잡성 | Python 생태계 |
| 배치 처리 | 처리량 | 지연시간 | GIL 오버헤드 |
```

### 3. ADR (Architecture Decision Records)

**개념**: 아키텍처 결정을 체계적으로 기록

**ADR 템플릿**:
```markdown
## ADR-001: [결정 제목]

### 상태
Accepted / Deprecated / Superseded

### 컨텍스트
왜 이 결정이 필요했는가?

### 결정
무엇을 결정했는가?

### 대안들
- 대안 1: 장단점
- 대안 2: 장단점

### 결과
이 결정의 영향은?
```

**우리 분석에 적용**:
```
OSS 분석 시 숨겨진 ADR 찾기:
- GitHub Issues/PR에서 설계 논의 탐색
- "Why not X?" 질문으로 대안 파악
- CHANGELOG에서 Breaking Changes 확인
```

### 4. GoF 디자인 패턴 인식

**23가지 GoF 패턴 중 자주 보이는 것**:
```
생성 패턴:
- Factory: 객체 생성 추상화 (@operator 데코레이터)
- Builder: 복잡한 객체 단계별 생성 (Dataflow 구성)
- Singleton: 전역 인스턴스 (설정, 로거)

구조 패턴:
- Adapter: 인터페이스 변환 (PyO3 바인딩)
- Decorator: 기능 래핑 (@operator)
- Composite: 트리 구조 (Operator 그래프)

행위 패턴:
- Strategy: 알고리즘 교체 (Clock, Windower)
- Template Method: 골격 정의 (StatefulBatchLogic)
- Observer: 이벤트 처리 (콜백)
- Iterator: 순회 (Stream)
```

**분석 시 적용**:
```
코드 읽을 때:
1. "이 구조가 어떤 패턴인가?"
2. "왜 이 패턴을 선택했는가?"
3. "다른 패턴이었다면 어땠을까?"
```

### 5. 역공학 분석 기법

#### Top-Down 분석 (권장)
```
1. README → 전체 목적 파악
2. 진입점 → main(), __main__.py
3. 핵심 흐름 → 데이터가 어떻게 흐르는가
4. 세부 구현 → 필요한 부분만 깊게

장점: 목적 지향적, 효율적
```

#### Bottom-Up 분석
```
1. 관심 있는 함수/클래스부터
2. 호출하는 곳 추적
3. 전체 맥락 파악

장점: 특정 기능 깊이 이해
```

#### Use-Case 기반 분석
```
1. 대표적인 사용 예제 선택
2. 해당 코드 경로 추적
3. 관련 컴포넌트만 분석

장점: 실용적, 적용하기 좋음
```

### 6. Data Flow Analysis

**개념**: 데이터 흐름을 따라 시스템 이해
```
Source → Transform → Sink

각 단계에서:
- 입력 타입은?
- 출력 타입은?
- 상태 변화는?
- 에러 처리는?
```

**시각화**:
```
[Kafka] ──JSON──→ [Parser] ──Dict──→ [Aggregator] ──Candle──→ [DB]
                      │                    │
                      ↓                    ↓
                  [DLQ]               [State Store]
```

### 7. 품질 속성 체크리스트 (ISO 25010)

**분석 시 확인할 품질 속성**:
```
□ 성능 (Performance)
  - 처리량, 지연시간, 리소스 사용량

□ 확장성 (Scalability)
  - 수평/수직 확장 가능성

□ 신뢰성 (Reliability)
  - 장애 복구, 데이터 일관성

□ 유지보수성 (Maintainability)
  - 코드 구조, 테스트 커버리지

□ 보안 (Security)
  - 인증, 인가, 데이터 보호

□ 이식성 (Portability)
  - 환경 의존성, 배포 용이성
```

---

## 분석 레벨별 방법론 매핑

| 레벨 | 적용 방법론 | 핵심 활동 |
|:----:|-------------|-----------|
| **L1** | C4 Context | 시스템 경계, 외부 연동 파악 |
| **L2** | C4 Container/Component, Data Flow | 구조 시각화, 흐름 추적 |
| **L3** | ATAM, GoF 패턴, ADR | Trade-off 분석, 패턴 식별, 결정 이유 |
| **L4** | 역공학 (Use-Case 기반) | 핵심 기능 재구현 |

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

> **적용 방법론**: C4 Model (Container/Component), Data Flow Analysis

### 목표
```
전체 구조를 그림으로 그릴 수 있는가?
주요 컴포넌트 간 관계를 설명할 수 있는가?
```

### 분석 프레임워크

#### 2.1 C4 Context 다이어그램 작성
```
질문:
- 이 시스템의 사용자는 누구인가?
- 어떤 외부 시스템과 연동하는가?
- 시스템의 경계는 어디인가?

예시 (bytewax):
┌─────────────────────────────────────────────────────────┐
│                    [사용자]                              │
│                   Python 개발자                          │
│                        │                                │
│                        ▼                                │
│  [Kafka] ←──→ [ bytewax ] ←──→ [Database]              │
│  [Files]      스트리밍 처리       [Redis]                │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

#### 2.2 C4 Container 다이어그램 작성
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

> **적용 방법론**: ATAM (Trade-off 분석), GoF 패턴 인식, ADR 탐색

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

#### 3.5 ATAM 기반 Trade-off 분석
```
ATAM (Architecture Tradeoff Analysis Method) 적용:

Step 1: 품질 속성 식별
- 이 설계가 중요시하는 품질 속성은? (성능? 확장성? 유지보수성?)

Step 2: 아키텍처 접근법 분석
- 이 설계의 장점은?
- 이 설계의 단점은?

Step 3: Trade-off 포인트 식별
- 어떤 품질 속성을 희생했는가?
- 다른 선택지는 없었을까?

Step 4: 리스크 분석
- 이 설계의 잠재적 문제는?

예시:
| 설계 결정 | 얻는 것 (품질↑) | 잃는 것 (품질↓) | Trade-off 이유 |
|-----------|-----------------|-----------------|---------------|
| Python API + Rust Engine | 사용성, 성능 | 복잡성 | Python 생태계 필요 |
| 배치 단위 처리 | 처리량 | 지연시간 | GIL 오버헤드 감소 |
| 문자열 키만 지원 | 안정성 | 유연성 | 분산 해싱 일관성 |
```

#### 3.6 ADR (Architecture Decision Records) 탐색
```
OSS에서 숨겨진 설계 결정 찾기:

1. GitHub Issues 검색
   - "why", "alternative", "considered" 키워드
   - 예: "Why did you choose X over Y?"

2. Pull Requests 분석
   - 큰 변경의 PR 설명
   - 리뷰 코멘트에서 논의

3. CHANGELOG / BREAKING CHANGES
   - 왜 API를 바꿨는가?
   - 이전 방식의 문제점은?

4. 코드 주석
   - TODO, FIXME, HACK 주석
   - "This is because..." 설명

5. 공식 문서 / RFC
   - Design docs, RFCs 폴더
   - Architecture decision 문서
```

#### 3.7 면접 예상 질문 정리
```
모듈 분석 후 반드시 작성:

Q: 이 프로젝트의 핵심 아키텍처는?
A: (C4 Container 다이어그램 기반으로 설명)

Q: 왜 이렇게 설계했는가?
A: (ATAM Trade-off 분석 결과로 설명)

Q: 어떤 디자인 패턴을 사용했는가?
A: (GoF 패턴 식별 결과로 설명)

Q: 다른 방식 대비 장단점은?
A: (ADR 탐색 결과로 설명)

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

> **핵심**: projects 개발 방법론을 따른다! (문서 먼저, 코드 나중)

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

---

### 📘 개발 방법론 참조

> **my-impl 구현 시 projects의 공통 개발 방법론을 따른다**

**참조 문서**:
- `/home/junhyun/projects/CLAUDE.md` - 공통 개발 방법론
- `/home/junhyun/projects/_templates/` - 템플릿 (버그, 기능, PRD)

### 핵심 원칙: 문서 먼저, 코드 나중

```
목적 (Why) → 기능 (What) → 설계 (How) → 코드 (Implementation)
```

### my-impl 문서 계층

```
레벨 1: README.md (PRD 역할)
    "이 구현이 뭐하는 건지" - 목적, 범위, 원본과 차이점
        ↓
레벨 2: docs/요구사항.md
    "어떤 기능이 필요한지" - 핵심 요구사항
        ↓
레벨 3: docs/설계.md
    "어떻게 구현할지" - 아키텍처, 데이터 흐름
        ↓
코드 구현 (src/)
```

### 4단계 개발 프로세스

```
Phase 1: 요구사항 정의
    - 원본 OSS에서 뭘 가져올 것인가?
    - 어떤 부분을 개선/변형할 것인가?
    - 수락 기준은?

Phase 2: 설계
    - 아키텍처 다이어그램
    - 핵심 컴포넌트
    - 데이터 흐름

Phase 3: 구현
    - 코드 작성
    - 테스트 작성

Phase 4: 검증 및 비교
    - 원본과 비교 (COMPARISON.md)
    - 성능 벤치마크 (선택)
    - 학습 포인트 정리
```

### my-impl 폴더 구조 (표준)

```
my-impl/
├── README.md               # PRD - 목적, 범위, 원본과 차이점
├── docs/
│   ├── 요구사항.md          # 핵심 요구사항, 수락 기준
│   ├── 설계.md             # 아키텍처, 데이터 흐름
│   └── COMPARISON.md       # 원본 vs 내 구현 비교
├── src/
│   └── ...
└── tests/
    └── ...
```

### my-impl README.md 템플릿

```markdown
# {프로젝트명} - my-impl

## 1. 개요
- **원본**: {OSS 이름} ({GitHub URL})
- **목적**: {왜 직접 구현하는가}
- **범위**: {전체 클론 / 핵심만 / 변형}

## 2. 원본과의 차이점
| 항목 | 원본 | 내 구현 |
|------|------|---------|
| {항목1} | {원본 방식} | {내 방식} |

## 3. 핵심 학습 목표
- [ ] {학습 목표 1}
- [ ] {학습 목표 2}

## 4. 실행 방법
{실행 명령어}

## 5. 테스트
{테스트 명령어}
```

### 구현 시 체크리스트

```
□ README.md 작성 (목적, 범위 명확화)
□ docs/요구사항.md 작성
□ docs/설계.md 작성 (다이어그램 포함)
□ 코드 구현
□ 테스트 작성
□ COMPARISON.md 작성 (원본과 비교)
□ 프로젝트 CLAUDE.md 업데이트 (L4 완료 표시)
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
□ README.md 작성 (목적, 범위, 원본과 차이점)
□ docs/요구사항.md 작성
□ docs/설계.md 작성 (다이어그램 포함)
□ src/ 코드 구현
□ tests/ 테스트 코드 포함
□ docs/COMPARISON.md 작성 (원본과 비교, 성능, 학습 포인트)
□ 프로젝트 CLAUDE.md 업데이트 (L4 완료 표시)
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

### 개발 방법론 (my-impl 구현 시 필수 참조)
- `/home/junhyun/projects/CLAUDE.md` - **공통 개발 방법론** (문서 먼저, 4단계 프로세스)
- `/home/junhyun/projects/_templates/` - 템플릿 (버그, 기능, PRD)

### 프로젝트 연계
- `/home/junhyun/projects/A_data-engineering/realtime-crypto-pipeline/CLAUDE.md` - 프로젝트 작업 지침
- `/home/junhyun/career-hub/SKILL_GAP_ANALYSIS.md` - Gap 스킬 상세

### 학습 자료
- `/home/junhyun/kb/Kafka-Stream-Processing/` - Kafka 가이드
- `/home/junhyun/kb/Apache-Spark/` - Spark 가이드

---

*마지막 업데이트: 2026-01-25*
*다음 분석: delta-rs (L2/L3)*
