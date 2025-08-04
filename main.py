# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx", "beautifulsoup4", "playwright"]
# ///
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import httpx, os, subprocess, asyncio, json
from typing import Dict, Any

# --- tool implementations --------------------------------------------------- #
def get_relevant_data(file_name: str, js_selector: str | None = None) -> Dict[str, Any]:
    """Extract text (or selector-filtered text) from a saved HTML file."""
    with open(file_name, encoding="utf-8") as f:
        html = f.read()
    soup = BeautifulSoup(html, "html.parser")
    if js_selector:
        elements = soup.select(js_selector)
        return {"data": [el.get_text(strip=True) for el in elements]}
    return {"data": soup.get_text(strip=True)}

async def scrape_website(url: str, output_file: str = "scraped_content.html"):
    """Headless Chromium scrape; saves full DOM to disk."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60_000)
            content = await page.content()
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            print("Failed to load page:", e)
        finally:
            await browser.close()

def answer_questions(code: str) -> str:
    """Write arbitrary Python code to disk and execute it."""
    with open("temp_script.py", "w") as f:
        f.write(code)
    result = subprocess.run(
        ["python", "temp_script.py"], capture_output=True, text=True
    )
    return result.stdout

# --- tool schemas passed to GPT-4o ----------------------------------------- #
tools: list[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "scrape_website",
            "description": "Scrapes a website and saves the content to a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Page URL"},
                    "output_file": {"type": "string", "description": "Destination file"},
                },
                "required": ["url", "output_file"],
            },
            "strict": True,
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_relevant_data",
            "description": "Extracts relevant data from a saved HTML file",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_name": {"type": "string", "description": "HTML filename"},
                    "js_selector": {"type": "string", "description": "CSS selector"},
                },
                "required": ["file_name", "js_selector"],
            },
            "strict": True,
        },
    },
]

# --- LLM orchestration ------------------------------------------------------ #
def query_gpt(prompt: str) -> Dict[str, Any]:
    """Calls the AIPipe-proxied OpenAI ChatCompletions endpoint."""
    resp = httpx.post(
        "https://aipipe.org/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {os.getenv('AIPIPE_TOKEN')}",
            "Content-Type": "application/json",
        },
        json={
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "tools": tools,
            "tool_choice": "auto",
        },
        timeout=90,
    )
    with open("gpt_response.json", "w", encoding="utf-8") as f:
        f.write(resp.text)           # keep a full trace for debugging
    return resp.json()["choices"][0]["message"]

def handle_tool_calls(calls: list[Dict[str, Any]]):
    for call in calls:
        if call["type"] != "function":
            continue
        fn, args = call["function"]["name"], call["function"]["arguments"]
        if fn == "scrape_website":
            asyncio.run(scrape_website(**args))
        elif fn == "get_relevant_data":
            print(get_relevant_data(**args))
        elif fn == "answer_questions":
            print(answer_questions(**args))

def main():
    user_prompt = input("Enter your query: ")
    msg = query_gpt(user_prompt)
    if "tool_calls" in msg:
        handle_tool_calls(msg["tool_calls"])
    print("Assistant:", msg.get("content", "No direct answer returned."))

if __name__ == "__main__":
    main()
