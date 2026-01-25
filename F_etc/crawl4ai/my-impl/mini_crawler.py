"""
미니 LLM 크롤러 - crawl4ai 핵심만 추출한 가벼운 버전

목표: URL → LLM 친화적 Markdown
"""

import asyncio
from playwright.async_api import async_playwright
import html2text
from bs4 import BeautifulSoup


async def crawl(url: str) -> str:
    """
    URL을 받아서 Markdown으로 반환

    Args:
        url: 크롤링할 URL

    Returns:
        페이지 내용을 Markdown으로 변환한 문자열
    """
    async with async_playwright() as p:
        # 1. 브라우저 시작 (headless)
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # 2. 페이지 로드
        await page.goto(url, wait_until="domcontentloaded")

        # 3. HTML 가져오기
        html = await page.content()

        # 4. 브라우저 종료
        await browser.close()

        # 5. HTML → Markdown 변환
        markdown = html_to_markdown(html)

        return markdown


def clean_html(html: str) -> str:
    """노이즈 제거 (nav, footer, script 등)"""
    soup = BeautifulSoup(html, "html.parser")

    # 불필요한 태그 제거
    for tag in soup.find_all(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    # 광고/팝업 관련 클래스 제거
    for element in soup.find_all(class_=lambda x: x and any(
        keyword in x.lower() for keyword in ["ad", "popup", "modal", "banner", "cookie"]
    )):
        element.decompose()

    return str(soup)


def html_to_markdown(html: str) -> str:
    """HTML을 Markdown으로 변환"""
    # 1. 노이즈 제거
    cleaned = clean_html(html)

    # 2. html2text 설정
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = False
    h.body_width = 0  # 줄바꿈 없이
    h.single_line_break = True

    # 3. 변환
    markdown = h.handle(cleaned)

    return markdown.strip()


# 테스트
if __name__ == "__main__":
    import sys

    # 인자로 URL 받거나 기본값 사용
    test_url = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"

    print(f"🔍 크롤링: {test_url}\n")
    print("=" * 50)

    result = asyncio.run(crawl(test_url))
    print(result)

    print("=" * 50)
    print(f"\n📊 결과: {len(result)} 글자")
