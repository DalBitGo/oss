# crawl4ai 분석

## 1. 개요
- **GitHub**: https://github.com/unclecode/crawl4ai
- **Stars**: 51K+
- **분석 일자**: 2025-01-15
- **한 줄 요약**: LLM 친화적인 웹 크롤러 - 웹을 깔끔한 Markdown으로 변환

## 2. 서비스 의도
> 이 프로젝트가 해결하려는 문제는 무엇인가?

### 문제
- 기존 웹 크롤러는 HTML을 그대로 반환 → LLM에 바로 넣기 어려움
- 상용 크롤링 API는 비싸고 (계정, API 키, 월정액 필요)
- RAG, AI 에이전트에 웹 데이터 넣으려면 전처리가 필요

### 해결
- **웹 → 깔끔한 Markdown** 자동 변환
- **LLM Ready**: 노이즈 제거, 구조화된 출력
- **무료 오픈소스**: API 키 없이 로컬에서 실행

### 타겟 사용자
- RAG 파이프라인 구축하는 개발자
- AI 에이전트에 웹 데이터 연동하려는 개발자
- 데이터 엔지니어 (웹 데이터 수집 ETL)

### 기존 대안 대비 차별점
| 기존 | crawl4ai |
|------|----------|
| BeautifulSoup | HTML 파싱만 | Markdown + LLM 추출 |
| Scrapy | 범용 크롤러 | LLM 최적화 출력 |
| Firecrawl (상용) | 유료 API | 무료 오픈소스 |

---

## 3. 아키텍처

### 3.1 전체 구조
```
┌─────────────────────────────────────────────────────────────┐
│  User Code                                                   │
│  async with AsyncWebCrawler() as crawler:                   │
│      result = await crawler.arun(url="...")                 │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│  AsyncWebCrawler (async_webcrawler.py)                      │
│  - 진입점, 설정 관리                                         │
│  - Cache 관리                                                │
│  - Deep Crawl 조율                                           │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│  Crawler Strategy (async_crawler_strategy.py)               │
│  - Playwright 브라우저 제어                                  │
│  - 페이지 로드, JS 실행                                      │
│  - 스크린샷, 대기 로직                                       │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│  Content Processing                                          │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐ │
│  │ Scraping     │ │ Markdown     │ │ Extraction           │ │
│  │ Strategy     │ │ Generator    │ │ Strategy             │ │
│  │ (HTML→구조화)│ │ (HTML→MD)    │ │ (LLM/CSS/Cosine)    │ │
│  └──────────────┘ └──────────────┘ └──────────────────────┘ │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│  Output: CrawlResult                                         │
│  - markdown (깔끔한 MD)                                      │
│  - extracted_content (JSON)                                  │
│  - links, images, metadata                                   │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 주요 컴포넌트
| 컴포넌트 | 역할 | 핵심 파일 |
|---------|------|----------|
| AsyncWebCrawler | 메인 진입점 | async_webcrawler.py |
| CrawlerStrategy | 브라우저 제어 (Playwright) | async_crawler_strategy.py |
| MarkdownGenerator | HTML → Markdown 변환 | markdown_generation_strategy.py |
| ExtractionStrategy | 구조화 데이터 추출 (LLM, CSS, Cosine) | extraction_strategy.py |
| ContentFilter | 노이즈 제거 (BM25, Pruning) | content_filter_strategy.py |
| DeepCrawl | 다중 페이지 크롤링 (BFS, DFS) | deep_crawling/ |
| BrowserManager | 브라우저 풀 관리 | browser_manager.py |

### 3.3 데이터 흐름
```
[URL]
    → Playwright로 페이지 로드 (JS 실행, 동적 콘텐츠)
    → HTML 추출
    → Content Scraping (구조 파싱)
    → Markdown 생성 (노이즈 제거)
    → Extraction (LLM/CSS로 구조화)
    → [CrawlResult]
```

---

## 4. 기술 스택
| 영역 | 기술 | 선택 이유 (추정) |
|------|------|-----------------|
| 언어 | Python 3.10+ | AI/ML 생태계, asyncio |
| 브라우저 | Playwright | 헤드리스, 안티봇 우회, 다중 브라우저 |
| HTML 파싱 | lxml, BeautifulSoup | 빠른 파싱 |
| Markdown | html2text (커스텀) | LLM 친화적 변환 |
| LLM 연동 | OpenAI, Ollama 등 | 구조화 추출 |
| 캐싱 | SQLite | 로컬 캐시, 간단함 |
| 비동기 | asyncio | 대량 크롤링 성능 |

---

## 5. 핵심 구현 분석

### 5.1 AsyncWebCrawler - 메인 진입점
**파일**: `async_webcrawler.py`
```python
async with AsyncWebCrawler() as crawler:
    result = await crawler.arun(url="https://example.com")
    print(result.markdown)
```
**분석**:
- Context Manager 패턴 (리소스 자동 정리)
- 내부에서 Playwright 브라우저 시작/종료
- `arun()` 하나로 크롤링 → 마크다운 → 추출까지 처리

### 5.2 Markdown 생성 전략
**파일**: `markdown_generation_strategy.py`
- HTML → 깔끔한 Markdown 변환
- **Fit Markdown**: 노이즈 제거 (광고, 네비게이션 등)
- **Citations**: 링크를 참조 형식으로 변환 `[1]`

### 5.3 Extraction Strategy
**파일**: `extraction_strategy.py`
- **LLMExtractionStrategy**: LLM으로 구조화 데이터 추출
- **JsonCssExtractionStrategy**: CSS 선택자로 빠른 추출
- **CosineStrategy**: 임베딩 유사도 기반 추출

### 5.4 Deep Crawling
**파일**: `deep_crawling/`
- **BFS/DFS**: 링크 따라가며 다중 페이지 크롤링
- **Filters**: 도메인, URL 패턴, 콘텐츠 타입 필터
- **Scorers**: 페이지 중요도 점수 (BestFirst)

---

## 6. 개발자의 고민 (Design Decisions)

### 6.1 왜 Playwright인가?
- **문제**: Selenium은 느리고 탐지 당함
- **선택지**: Selenium vs Puppeteer vs Playwright
- **결정**: Playwright
- **이유**:
  - 다중 브라우저 (Chromium, Firefox, WebKit)
  - 더 나은 안티봇 우회
  - async 네이티브

### 6.2 왜 자체 html2text인가?
- **문제**: 기존 html2text는 LLM에 최적화 안됨
- **결정**: 커스텀 html2text 폴더 유지
- **이유**: 테이블, 코드블록, 인용 등 LLM 친화적 처리

### 6.3 Strategy 패턴
- Markdown 생성, 추출, 필터링 모두 Strategy 패턴
- 사용자가 쉽게 커스텀 전략 주입 가능

---

## 7. 아쉬운 점 / 개선 아이디어
- [ ] 코드가 좀 큼 (33K+ 줄) - 핵심만 추출하면 더 가벼울 듯
- [ ] 파일명에 `copy`, `back` 붙은 것들 정리 안됨
- [ ] 설정 옵션이 너무 많아 진입장벽
- [ ] 메모리 사용량 (Playwright 브라우저)

---

## 8. 내가 배울 수 있는 것
- **Playwright 비동기 제어**: 헤드리스 브라우저 다루기
- **Strategy 패턴**: 확장 가능한 설계
- **HTML → Markdown 변환**: LLM 전처리
- **Deep Crawling**: BFS/DFS 링크 탐색
- **asyncio 패턴**: 대량 I/O 처리

---

## 9. my-impl 계획
> 이 프로젝트를 참고해서 내가 만들 것

### 목표
**미니 LLM 크롤러** - crawl4ai의 핵심만 추출한 가벼운 버전

### 범위
- [ ] Playwright로 페이지 로드
- [ ] HTML → Markdown 변환 (기본)
- [ ] 노이즈 제거 (nav, footer, ads)
- [ ] 간단한 LLM 추출 (OpenAI)

### 차별점
- 코드 500줄 이하로 핵심만
- 설정 최소화 (바로 쓸 수 있게)
- 데이터 엔지니어 관점 (파이프라인 연동 쉽게)

---

## 10. 분석 문서 목록

### 작성 예정
1. `00_SUMMARY.md` - 전체 요약 (이 문서) ✅
2. `architecture.md` - 아키텍처 상세
3. `async_webcrawler.md` - 메인 크롤러 분석
4. `markdown_generation.md` - Markdown 변환 분석
5. `extraction_strategy.md` - 추출 전략 분석
6. `deep_crawling.md` - Deep Crawl 분석

---

## 11. 코드 구조 요약

```
crawl4ai/
├── async_webcrawler.py      # 메인 진입점 ⭐
├── async_crawler_strategy.py # Playwright 제어 ⭐
├── markdown_generation_strategy.py # HTML→MD ⭐
├── extraction_strategy.py   # LLM/CSS 추출 ⭐
├── content_filter_strategy.py # 노이즈 제거
├── content_scraping_strategy.py # HTML 파싱
├── deep_crawling/           # 다중 페이지 크롤링
│   ├── bfs_strategy.py
│   ├── dfs_strategy.py
│   └── filters.py
├── browser_manager.py       # 브라우저 풀
├── async_configs.py         # 설정 클래스들
├── models.py                # 데이터 모델 (CrawlResult)
└── html2text/               # 커스텀 MD 변환
```

**핵심 파일 4개**: async_webcrawler, async_crawler_strategy, markdown_generation_strategy, extraction_strategy
