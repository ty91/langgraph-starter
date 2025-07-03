# LangGraph Starter

## 📋 요구사항

- Python 3.12 이상
- uv (Python 패키지 관리자)
- Anthropic API 키

## 🛠️ 설치 및 설정

### 1. uv 설치

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. 프로젝트 설정

```bash
# 프로젝트 클론
git clone <repository-url>
cd langgraph-starter

# 의존성 설치
uv sync
```

### 3. 환경 변수 설정

```bash
# API 키 설정
export ANTHROPIC_API_KEY=your_api_key_here
```

## 🏃 실행

```bash
# 에이전트 실행
uv run python main.py
```
