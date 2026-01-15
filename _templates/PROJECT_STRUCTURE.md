# OSS 프로젝트 구조 가이드

## 폴더 구조

```
oss/
├── _templates/              # 분석 템플릿
│   ├── ANALYSIS_TEMPLATE.md
│   └── PROJECT_STRUCTURE.md
│
├── [project-name]/
│   ├── original/            # 원본 코드 (git clone)
│   ├── docs/                # 분석 문서들
│   │   ├── 00_SUMMARY.md    # 전체 요약 (ANALYSIS_TEMPLATE 기반)
│   │   ├── architecture.md  # 아키텍처 상세
│   │   ├── [module].md      # 모듈별 분석
│   │   └── ...
│   └── my-impl/             # 내가 다시 만든 버전
│
└── CANDIDATES.md            # 분석 후보 목록
```

## 워크플로우

```
1. 프로젝트 선정 (CANDIDATES.md에 추가)
      ↓
2. original/ 에 git clone
      ↓
3. docs/ 에 분석 문서 작성 (ANALYSIS_TEMPLATE.md 사용)
      ↓
4. 코드 읽으면서 docs/ 보강
      ↓
5. my-impl/ 에 나만의 버전 구현
```

## 분석 문서 네이밍

- `00_SUMMARY.md` - 전체 요약 (필수)
- `architecture.md` - 아키텍처/구조
- `[모듈명].md` - 모듈별 상세 분석
- `design-decisions.md` - 설계 결정 모음
- `lessons-learned.md` - 배운 점 정리

## 체크리스트

### 분석 시작 전
- [ ] CANDIDATES.md에 프로젝트 추가
- [ ] original/ 에 클론
- [ ] README, CONTRIBUTING 읽기

### 분석 중
- [ ] 00_SUMMARY.md 작성 시작
- [ ] 아키텍처 파악
- [ ] 핵심 모듈 분석
- [ ] 디자인 결정 정리

### 분석 후
- [ ] my-impl 계획 수립
- [ ] 구현 시작
