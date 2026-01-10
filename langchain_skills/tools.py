"""Custom tools for the CLI agent."""

from typing import Any, Literal

import requests
from markdownify import markdownify
from pathlib import Path

def http_request(
    url: str,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    data: str | dict | None = None,
    params: dict[str, str] | None = None,
    timeout: int = 30,
) -> dict[str, Any]:
    """Make HTTP requests to APIs and web services.

    Args:
        url: Target URL
        method: HTTP method (GET, POST, PUT, DELETE, etc.)
        headers: HTTP headers to include
        data: Request body data (string or dict)
        params: URL query parameters
        timeout: Request timeout in seconds

    Returns:
        Dictionary with response data including status, headers, and content
    """
    try:
        kwargs = {"url": url, "method": method.upper(), "timeout": timeout}

        if headers:
            kwargs["headers"] = headers
        if params:
            kwargs["params"] = params
        if data:
            if isinstance(data, dict):
                kwargs["json"] = data
            else:
                kwargs["data"] = data

        response = requests.request(**kwargs)

        try:
            content = response.json()
        except:
            content = response.text

        return {
            "success": response.status_code < 400,
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "content": content,
            "url": response.url,
        }

    except requests.exceptions.Timeout:
        return {
            "success": False,
            "status_code": 0,
            "headers": {},
            "content": f"Request timed out after {timeout} seconds",
            "url": url,
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "status_code": 0,
            "headers": {},
            "content": f"Request error: {e!s}",
            "url": url,
        }
    except Exception as e:
        return {
            "success": False,
            "status_code": 0,
            "headers": {},
            "content": f"Error making request: {e!s}",
            "url": url,
        }



def fetch_url(url: str, timeout: int = 30) -> dict[str, Any]:
    """Fetch content from a URL and convert HTML to markdown format.

    This tool fetches web page content and converts it to clean markdown text,
    making it easy to read and process HTML content. After receiving the markdown,
    you MUST synthesize the information into a natural, helpful response for the user.

    Args:
        url: The URL to fetch (must be a valid HTTP/HTTPS URL)
        timeout: Request timeout in seconds (default: 30)

    Returns:
        Dictionary containing:
        - success: Whether the request succeeded
        - url: The final URL after redirects
        - markdown_content: The page content converted to markdown
        - status_code: HTTP status code
        - content_length: Length of the markdown content in characters

    IMPORTANT: After using this tool:
    1. Read through the markdown content
    2. Extract relevant information that answers the user's question
    3. Synthesize this into a clear, natural language response
    4. NEVER show the raw markdown to the user unless specifically requested
    """
    try:
        response = requests.get(
            url,
            timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0 (compatible; DeepAgents/1.0)"},
        )
        response.raise_for_status()

        # Convert HTML content to markdown
        markdown_content = markdownify(response.text)

        return {
            "url": str(response.url),
            "markdown_content": markdown_content,
            "status_code": response.status_code,
            "content_length": len(markdown_content),
        }
    except Exception as e:
        return {"error": f"Fetch URL error: {e!s}", "url": url}



# ✅ 定义项目根目录（tools.py 所在目录的父级）
PROJECT_ROOT = Path(__file__).parent.resolve()

# ✅ 定义所有允许的技能根目录（绝对路径）
ALLOWED_SKILL_ROOTS = {
    "project-skills": (PROJECT_ROOT / "project-skills").resolve(),
    "user-skills": (PROJECT_ROOT / "user-skills").resolve(),
    # 可以继续加： "community-skills": ...
}

def read_file(path: str) -> str:
    """
    Read file contents. Supports:
    - Absolute paths (e.g., C:\\... or /...)
    - Relative paths (resolved relative to project root)

    Only allows reading files under the 'project-skills' directory for security.
    """
    if not isinstance(path, str):
        raise TypeError("Path must be a string")

    input_path = Path(path)

    # Step 1: 如果是相对路径，尝试匹配到某个技能根目录
    if not input_path.is_absolute():
        resolved_path = None
        for root_name, root_path in ALLOWED_SKILL_ROOTS.items():
            if path.startswith(root_name + "/") or path.startswith(root_name + "\\"):
                # 提取子路径，拼接到真实根目录
                sub_path = path[len(root_name) + 1:]  # 去掉 "project-skills/"
                resolved_path = (root_path / sub_path).resolve()
                break
        if resolved_path is None:
            # 如果不匹配任何已知技能前缀，就当作相对于 PROJECT_ROOT
            resolved_path = (PROJECT_ROOT / path).resolve()
    else:
        # 绝对路径：直接使用
        resolved_path = input_path.resolve()

    # Step 2: 安全检查 —— 必须落在某一个允许的根目录下
    allowed = False
    for root_path in ALLOWED_SKILL_ROOTS.values():
        try:
            resolved_path.relative_to(root_path)
            allowed = True
            break
        except ValueError:
            continue

    if not allowed:
        allowed_list = [str(p) for p in ALLOWED_SKILL_ROOTS.values()]
        raise PermissionError(
            f"Access denied: {resolved_path} is not inside any allowed skill directory.\n"
            f"Allowed roots: {allowed_list}"
        )

    # Step 3: 检查文件是否存在
    if not resolved_path.is_file():
        raise FileNotFoundError(f"File not found: {resolved_path}")

    # Step 4: 读取文件
    try:
        with open(resolved_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        raise RuntimeError(f"Failed to read {resolved_path}: {e}")