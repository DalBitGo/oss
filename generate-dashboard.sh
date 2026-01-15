#!/bin/bash

# OSS 분석 대시보드 생성 스크립트
# 사용법: ./generate-dashboard.sh

cd /home/junhyun/oss

# 프로젝트 목록 (숨김 폴더, _templates 제외)
projects=$(ls -d */ 2>/dev/null | grep -v "^_" | sed 's/\///')

# HTML 시작
cat > dashboard.html << 'HTMLHEAD'
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OSS 분석 대시보드</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0d1117;
            color: #c9d1d9;
            padding: 40px;
            min-height: 100vh;
        }
        h1 {
            font-size: 28px;
            margin-bottom: 8px;
            color: #f0f6fc;
        }
        .subtitle {
            color: #8b949e;
            margin-bottom: 32px;
            font-size: 14px;
        }
        .stats {
            display: flex;
            gap: 24px;
            margin-bottom: 32px;
        }
        .stat-card {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 20px;
            min-width: 140px;
        }
        .stat-number {
            font-size: 32px;
            font-weight: 600;
            color: #58a6ff;
        }
        .stat-label {
            font-size: 12px;
            color: #8b949e;
            margin-top: 4px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            background: #161b22;
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid #30363d;
        }
        th {
            background: #21262d;
            padding: 12px 16px;
            text-align: left;
            font-weight: 600;
            font-size: 12px;
            text-transform: uppercase;
            color: #8b949e;
            border-bottom: 1px solid #30363d;
        }
        td {
            padding: 16px;
            border-bottom: 1px solid #21262d;
        }
        tr:last-child td { border-bottom: none; }
        tr:hover { background: #1c2128; }
        .project-name {
            font-weight: 600;
            color: #58a6ff;
        }
        .status {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 28px;
            height: 28px;
            border-radius: 50%;
            font-size: 14px;
        }
        .status.done {
            background: #238636;
            color: #fff;
        }
        .status.empty {
            background: #30363d;
            color: #484f58;
        }
        .status.partial {
            background: #9e6a03;
            color: #fff;
        }
        .progress-bar {
            width: 100%;
            height: 6px;
            background: #30363d;
            border-radius: 3px;
            overflow: hidden;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #238636, #2ea043);
            transition: width 0.3s;
        }
        .timestamp {
            text-align: right;
            color: #484f58;
            font-size: 12px;
            margin-top: 24px;
        }
    </style>
</head>
<body>
    <h1>OSS 분석 대시보드</h1>
    <p class="subtitle">오픈소스 분석 → 문서화 → 나만의 구현</p>

    <div class="stats">
HTMLHEAD

# 통계 계산
total=0
cloned=0
analyzed=0
implemented=0

for project in $projects; do
    [ ! -d "$project" ] && continue
    [ "$project" = "_templates" ] && continue

    ((total++))

    # original 체크
    if [ -d "$project/original" ] && [ "$(ls -A $project/original 2>/dev/null)" ]; then
        ((cloned++))
    fi

    # docs 체크
    if [ -d "$project/docs" ] && [ "$(ls $project/docs/*.md 2>/dev/null)" ]; then
        ((analyzed++))
    fi

    # my-impl 체크
    if [ -d "$project/my-impl" ] && [ "$(ls -A $project/my-impl 2>/dev/null | grep -v '.gitkeep')" ]; then
        ((implemented++))
    fi
done

# 통계 카드 출력
cat >> dashboard.html << EOF
        <div class="stat-card">
            <div class="stat-number">$total</div>
            <div class="stat-label">전체 프로젝트</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">$cloned</div>
            <div class="stat-label">원본 클론</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">$analyzed</div>
            <div class="stat-label">분석 완료</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">$implemented</div>
            <div class="stat-label">구현 완료</div>
        </div>
    </div>

    <table>
        <thead>
            <tr>
                <th>프로젝트</th>
                <th>원본</th>
                <th>분석</th>
                <th>구현</th>
                <th>진행률</th>
            </tr>
        </thead>
        <tbody>
EOF

# 각 프로젝트 행 출력
for project in $projects; do
    [ ! -d "$project" ] && continue
    [ "$project" = "_templates" ] && continue

    # 상태 체크
    has_original="empty"
    has_docs="empty"
    has_impl="empty"
    progress=0

    if [ -d "$project/original" ] && [ "$(ls -A $project/original 2>/dev/null)" ]; then
        has_original="done"
        ((progress+=33))
    fi

    if [ -d "$project/docs" ] && [ "$(ls $project/docs/*.md 2>/dev/null)" ]; then
        has_docs="done"
        ((progress+=33))
    fi

    if [ -d "$project/my-impl" ] && [ "$(ls -A $project/my-impl 2>/dev/null | grep -v '.gitkeep')" ]; then
        has_impl="done"
        ((progress+=34))
    fi

    cat >> dashboard.html << EOF
            <tr>
                <td class="project-name">$project</td>
                <td><span class="status $has_original">$([ "$has_original" = "done" ] && echo "✓" || echo "−")</span></td>
                <td><span class="status $has_docs">$([ "$has_docs" = "done" ] && echo "✓" || echo "−")</span></td>
                <td><span class="status $has_impl">$([ "$has_impl" = "done" ] && echo "✓" || echo "−")</span></td>
                <td>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${progress}%"></div>
                    </div>
                </td>
            </tr>
EOF
done

# HTML 마무리
cat >> dashboard.html << EOF
        </tbody>
    </table>

    <p class="timestamp">마지막 업데이트: $(date '+%Y-%m-%d %H:%M:%S')</p>
</body>
</html>
EOF

echo "✅ dashboard.html 생성 완료"
echo "👉 브라우저에서 열기: file:///home/junhyun/oss/dashboard.html"
