# crawl4ai 심층 분석 주제

## 분석할만한 핵심 영역 5가지

---

## 1. Playwright 비동기 브라우저 제어 ⭐⭐⭐
**파일**: `async_crawler_strategy.py` (2400줄)

### 배울 수 있는 것
- **Hook 시스템**: 크롤링 라이프사이클에 커스텀 로직 삽입
  ```python
  hooks = {
      "on_browser_created": None,
      "before_goto": None,
      "after_goto": None,
      "before_return_html": None,
  }
  ```
- **BrowserManager**: 브라우저 풀 관리, 세션 재사용
- **Context Manager 패턴**: `async with`로 리소스 자동 정리
- **안티봇 우회**: UndetectedAdapter 사용

### 데이터 엔지니어 관점
- 대량 크롤링 시 브라우저 리소스 관리
- 세션 유지하면서 여러 페이지 크롤링
- JS 렌더링이 필요한 동적 사이트 처리

---

## 2. Extraction Strategy (추출 전략) ⭐⭐⭐
**파일**: `extraction_strategy.py` (2166줄)

### 3가지 추출 방식
| 전략 | 사용 시점 | 기술 |
|------|----------|------|
| **LLMExtractionStrategy** | 비정형 데이터 | OpenAI/Ollama로 구조화 |
| **JsonCssExtractionStrategy** | 정형 사이트 | CSS 선택자로 빠른 추출 |
| **CosineStrategy** | 의미 기반 필터링 | 임베딩 + 코사인 유사도 |

### CosineStrategy 핵심 로직
```python
# 1. 문서 임베딩 생성
document_embeddings = self.get_embeddings(documents)

# 2. 쿼리와 유사도 계산
similarities = cosine_similarity([query_embedding], document_embeddings)

# 3. 임계값 이상만 필터링
filtered_docs = [doc for doc, sim in zip(documents, similarities) if sim >= threshold]
```

### 데이터 엔지니어 관점
- RAG 파이프라인에 바로 연동 가능
- 임베딩 모델 선택 (MiniLM, BGE 등)
- 배치 처리로 대량 문서 처리

---

## 3. Markdown 생성 + Citations ⭐⭐
**파일**: `markdown_generation_strategy.py` (260줄)

### 핵심 기능
1. **HTML → Markdown**: 커스텀 html2text 사용
2. **Citations 변환**: 링크를 참조 형식으로
   ```
   [링크텍스트](url) → 링크텍스트⟨1⟩

   ## References
   ⟨1⟩ https://example.com
   ```
3. **Fit Markdown**: 노이즈 제거된 버전

### 데이터 엔지니어 관점
- LLM 입력 전처리 표준화
- 토큰 절약 (노이즈 제거)
- 출처 추적 가능한 형태

---

## 4. Deep Crawling (다중 페이지) ⭐⭐
**파일**: `deep_crawling/` 폴더

### 탐색 전략
| 전략 | 설명 | 사용 시점 |
|------|------|----------|
| **BFS** | 너비 우선 | 같은 depth 페이지 먼저 |
| **DFS** | 깊이 우선 | 특정 경로 깊게 |
| **BestFirst** | 점수 기반 | 중요한 페이지 먼저 |

### Filter & Scorer 시스템
```python
# 필터: 어떤 URL을 크롤링할지
filters = [
    DomainFilter(allowed=["example.com"]),
    URLPatternFilter(patterns=["/blog/*"]),
    ContentTypeFilter(allowed=["text/html"]),
]

# 스코어: 어떤 페이지가 중요한지
scorers = [
    KeywordRelevanceScorer(keywords=["python", "data"]),
    PathDepthScorer(),  # 얕은 경로 우선
]
```

### 데이터 엔지니어 관점
- 사이트맵 없이 전체 사이트 크롤링
- 특정 섹션만 선택적 수집
- 크롤링 예산 관리 (max_pages)

---

## 5. Content Filter (노이즈 제거) ⭐⭐
**파일**: `content_filter_strategy.py`

### 필터 종류
| 필터 | 방식 | 특징 |
|------|------|------|
| **PruningContentFilter** | 규칙 기반 | nav, footer, ads 제거 |
| **BM25ContentFilter** | TF-IDF 기반 | 키워드 관련도 |
| **LLMContentFilter** | LLM 판단 | 가장 정확하지만 느림 |

### 데이터 엔지니어 관점
- ETL의 Transform 단계
- 데이터 품질 향상
- 토큰 비용 절감

---

## 추천 분석 순서

### 빠르게 핵심만 (1-2시간)
1. `markdown_generation_strategy.py` (260줄) - 가장 짧음
2. `00_SUMMARY.md` 다시 읽기

### 제대로 분석 (반나절)
1. `async_webcrawler.py` - 진입점 이해
2. `async_crawler_strategy.py` - Playwright 제어
3. `extraction_strategy.py` - 추출 로직

### 완전 분석 (1-2일)
- 위 전부 + deep_crawling/ + content_filter

---

## my-impl 구현 시 참고할 부분

### 최소 버전 (500줄 목표)
```
1. Playwright로 페이지 로드 (async_crawler_strategy.py 참고)
2. HTML → Markdown (markdown_generation_strategy.py 참고)
3. 간단한 노이즈 제거 (nav, footer 태그 제거)
```

### 확장 버전
```
4. LLM 추출 추가 (extraction_strategy.py 참고)
5. 멀티 페이지 크롤링 (deep_crawling/ 참고)
```
