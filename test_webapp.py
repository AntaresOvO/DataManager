"""
E2E tests for the Flask + Vue 3 form builder system.
Default admin: admin / admin123 (need_change_pwd=1)
"""
import sys
import os
from playwright.sync_api import sync_playwright, expect

BASE_URL = "http://localhost:5173"
SCREENSHOT_DIR = "/tmp/test_screenshots"
ADMIN_USER = "admin"
INIT_PASS = "admin123"
NEW_PASS = "Test123456"

results = []


def record(name, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    results.append((name, status, detail))
    print(f"  [{status}] {name}" + (f" - {detail}" if detail else ""))


def do_login(page, username, password):
    """Fill login form and submit. Does NOT wait for specific URL."""
    page.goto(f"{BASE_URL}/login")
    page.wait_for_load_state("networkidle")
    page.locator('input[placeholder="用户名"]').fill(username)
    page.locator('input[placeholder="密码"]').fill(password)
    page.locator("button:has-text('登 录')").click()
    # Wait until we leave the login page
    page.wait_for_function("() => !window.location.pathname.includes('/login')", timeout=10000)
    page.wait_for_load_state("networkidle")


def login_ready(page):
    """Login with admin (password already changed, need_change_pwd=0)."""
    do_login(page, ADMIN_USER, NEW_PASS)
    page.wait_for_url("**/home", timeout=10000)


# ── Setup: change password to clear need_change_pwd ──

def setup_change_password(browser):
    """First-time login: change password so need_change_pwd becomes 0.
    If password was already changed (INIT_PASS fails), try NEW_PASS directly."""
    # First, check if NEW_PASS already works
    context = browser.new_context()
    page = context.new_page()
    try:
        do_login(page, ADMIN_USER, NEW_PASS)
        if "/home" in page.url:
            print("  [SETUP] Password already changed, skipping setup")
            return True
    except:
        pass
    finally:
        context.close()

    # Need to change password from INIT_PASS
    context = browser.new_context()
    page = context.new_page()
    try:
        do_login(page, ADMIN_USER, INIT_PASS)
        # Should be redirected to /system/profile
        page.wait_for_url("**/system/profile", timeout=10000)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)

        # Fill change password form
        inputs = page.locator("input[type='password']")
        inputs.nth(0).fill(INIT_PASS)    # old password
        inputs.nth(1).fill(NEW_PASS)     # new password
        inputs.nth(2).fill(NEW_PASS)     # confirm
        page.locator("button:has-text('确认修改')").click()
        page.wait_for_timeout(2000)

        # Should redirect to login after password change
        page.wait_for_url("**/login", timeout=10000)
        print("  [SETUP] Password changed successfully")
        return True
    except Exception as e:
        print(f"  [SETUP] Failed to change password: {e}")
        page.screenshot(path=f"{SCREENSHOT_DIR}/setup_fail.png")
        return False
    finally:
        context.close()


# ── Tests ──

def test_login_page_renders(page):
    """Login page renders correctly."""
    page.goto(f"{BASE_URL}/login")
    page.wait_for_load_state("networkidle")
    expect(page.locator("h2")).to_have_text("数据管理平台")
    expect(page.locator('input[placeholder="用户名"]')).to_be_visible()
    expect(page.locator('input[placeholder="密码"]')).to_be_visible()
    expect(page.locator("button:has-text('登 录')")).to_be_visible()
    record("Login page renders", True)


def test_login_empty_validation(page):
    """Empty fields show validation errors."""
    page.goto(f"{BASE_URL}/login")
    page.wait_for_load_state("networkidle")
    page.locator("button:has-text('登 录')").click()
    page.wait_for_timeout(500)
    expect(page.locator(".el-form-item__error").first).to_be_visible()
    record("Login empty fields validation", True)


def test_login_wrong_password(page):
    """Wrong password stays on login page."""
    page.goto(f"{BASE_URL}/login")
    page.wait_for_load_state("networkidle")
    page.locator('input[placeholder="用户名"]').fill("admin")
    page.locator('input[placeholder="密码"]').fill("wrongpassword")
    page.locator("button:has-text('登 录')").click()
    page.wait_for_timeout(2000)
    expect(page.locator('input[placeholder="用户名"]')).to_be_visible()
    record("Login wrong password rejected", True)


def test_login_success(page):
    """Successful login navigates to home."""
    login_ready(page)
    expect(page.locator("text=欢迎使用数据管理平台")).to_be_visible()
    record("Login success", True)


def test_sidebar_navigation(page):
    """All sidebar menu items visible and clickable."""
    login_ready(page)
    for item in ["首页", "模板管理", "表单数据", "数据查询", "表格编辑", "用户管理", "系统日志", "个人中心"]:
        expect(page.locator(f".el-menu-item:has-text('{item}')")).to_be_visible()
    page.locator(".el-menu-item:has-text('模板管理')").click()
    page.wait_for_url("**/templates", timeout=5000)
    record("Sidebar navigation", True)


def test_templates_page(page):
    """Templates page loads with table and controls."""
    login_ready(page)
    page.locator(".el-menu-item:has-text('模板管理')").click()
    page.wait_for_url("**/templates", timeout=5000)
    page.wait_for_load_state("networkidle")
    expect(page.locator('input[placeholder="搜索模板名称"]')).to_be_visible()
    expect(page.locator("button:has-text('新增模板')")).to_be_visible()
    expect(page.locator(".el-table")).to_be_visible()
    record("Templates page loads", True)


def test_create_template_dialog(page):
    """New template dialog opens correctly."""
    login_ready(page)
    page.locator(".el-menu-item:has-text('模板管理')").click()
    page.wait_for_url("**/templates", timeout=5000)
    page.wait_for_load_state("networkidle")
    page.locator("button:has-text('新增模板')").click()
    page.wait_for_timeout(500)
    dialog = page.locator(".el-dialog:visible")
    expect(dialog).to_be_visible()
    expect(dialog.locator("text=新增模板")).to_be_visible()
    record("Create template dialog opens", True)


def test_forms_page(page):
    """Forms page loads with table."""
    login_ready(page)
    page.locator(".el-menu-item:has-text('表单数据')").click()
    page.wait_for_url("**/forms", timeout=5000)
    page.wait_for_load_state("networkidle")
    expect(page.locator(".el-table")).to_be_visible()
    expect(page.locator("button:has-text('填写表单')")).to_be_visible()
    record("Forms page loads", True)


def test_form_browser_page(page):
    """Data query page loads."""
    login_ready(page)
    page.locator(".el-menu-item:has-text('数据查询')").click()
    page.wait_for_url("**/form-browser", timeout=5000)
    page.wait_for_load_state("networkidle")
    record("Form browser page loads", True)


def test_form_sheet_page(page):
    """Table edit page loads."""
    login_ready(page)
    page.locator(".el-menu-item:has-text('表格编辑')").click()
    page.wait_for_url("**/form-sheet", timeout=5000)
    page.wait_for_load_state("networkidle")
    record("Form sheet page loads", True)


def test_users_page(page):
    """Users management page loads (admin)."""
    login_ready(page)
    page.locator(".el-menu-item:has-text('用户管理')").click()
    page.wait_for_url("**/system/users", timeout=5000)
    page.wait_for_load_state("networkidle")
    expect(page.locator(".el-table")).to_be_visible()
    expect(page.locator("button:has-text('新增用户')")).to_be_visible()
    expect(page.locator("td:has-text('admin')").first).to_be_visible()
    record("Users page loads", True)


def test_logs_page(page):
    """System logs page loads (admin)."""
    login_ready(page)
    page.locator(".el-menu-item:has-text('系统日志')").click()
    page.wait_for_url("**/system/logs", timeout=5000)
    page.wait_for_load_state("networkidle")
    expect(page.locator(".el-table")).to_be_visible()
    record("Logs page loads", True)


def test_profile_page(page):
    """Profile page shows user info and password form."""
    login_ready(page)
    page.locator(".el-menu-item:has-text('个人中心')").click()
    page.wait_for_url("**/system/profile", timeout=5000)
    page.wait_for_load_state("networkidle")
    expect(page.locator("h3:has-text('个人中心')")).to_be_visible()
    expect(page.locator("h4:has-text('修改密码')")).to_be_visible()
    record("Profile page loads", True)


def test_logout(page):
    """Logout redirects to login."""
    login_ready(page)
    page.locator("button:has-text('操作')").click()
    page.wait_for_timeout(300)
    page.locator(".el-dropdown-menu__item:has-text('退出登录')").click()
    page.wait_for_url("**/login", timeout=5000)
    expect(page.locator("h2:has-text('数据管理平台')")).to_be_visible()
    record("Logout", True)


def test_unauthenticated_redirect(page):
    """Unauthenticated access redirects to login."""
    page.goto(f"{BASE_URL}/home")
    page.wait_for_url("**/login", timeout=5000)
    expect(page.locator("h2:has-text('数据管理平台')")).to_be_visible()
    record("Unauthenticated redirect", True)


def main():
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)

    print("\n========================================")
    print("  E2E Tests - Form Builder System")
    print("========================================\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # Setup: change admin password to clear need_change_pwd
        if not setup_change_password(browser):
            print("\nSetup failed, aborting tests.")
            browser.close()
            sys.exit(1)

        tests = [
            test_login_page_renders,
            test_login_empty_validation,
            test_login_wrong_password,
            test_login_success,
            test_sidebar_navigation,
            test_templates_page,
            test_create_template_dialog,
            test_forms_page,
            test_form_browser_page,
            test_form_sheet_page,
            test_users_page,
            test_logs_page,
            test_profile_page,
            test_logout,
            test_unauthenticated_redirect,
        ]

        for test_fn in tests:
            ctx = browser.new_context()
            pg = ctx.new_page()
            try:
                test_fn(pg)
            except Exception as e:
                record(test_fn.__doc__ or test_fn.__name__, False, str(e))
            finally:
                pg.screenshot(path=f"{SCREENSHOT_DIR}/{test_fn.__name__}.png")
                ctx.close()

        browser.close()

    passed = sum(1 for _, s, _ in results if s == "PASS")
    failed = sum(1 for _, s, _ in results if s == "FAIL")
    total = len(results)

    print(f"\n========================================")
    print(f"  Results: {passed}/{total} passed, {failed} failed")
    print(f"  Screenshots: {SCREENSHOT_DIR}/")
    print(f"========================================\n")

    if failed:
        print("Failed tests:")
        for name, status, detail in results:
            if status == "FAIL":
                print(f"  - {name}: {detail}")
        print()

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
