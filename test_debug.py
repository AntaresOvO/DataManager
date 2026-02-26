"""Debug: check login with admin123."""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    page.on("console", lambda msg: print(f"  [console] {msg.type}: {msg.text}"))
    page.on("response", lambda res: print(f"  [resp] {res.status} {res.url}") if "/api/" in res.url else None)

    page.goto("http://localhost:5173/login")
    page.wait_for_load_state("networkidle")

    page.locator('input[placeholder="用户名"]').fill("admin")
    page.locator('input[placeholder="密码"]').fill("admin123")
    page.locator("button:has-text('登 录')").click()

    page.wait_for_timeout(5000)
    print(f"\nURL after login: {page.url}")
    page.screenshot(path="/tmp/test_screenshots/debug_login.png")

    body_text = page.inner_text("body")
    print(f"Body text (first 500): {body_text[:500]}")

    browser.close()
