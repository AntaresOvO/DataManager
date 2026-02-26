"""
Stress test for the Form Builder System API.
Uses concurrent threads to simulate multiple users hitting the API.
Requires: requests (pip install requests)
"""
import sys
import os
import time
import json
import threading
import statistics
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "http://127.0.0.1:5000"

# ── Config ──
CONCURRENT_USERS = 20       # Number of concurrent threads
REQUESTS_PER_TEST = 100     # Total requests per test scenario
ADMIN_USER = "admin"
ADMIN_PASS = "Test123456"   # Password after E2E setup changed it

results_lock = threading.Lock()


class StressResult:
    def __init__(self, name):
        self.name = name
        self.latencies = []
        self.success = 0
        self.fail = 0
        self.errors = []

    def record(self, latency, ok, error_msg=None):
        with results_lock:
            self.latencies.append(latency)
            if ok:
                self.success += 1
            else:
                self.fail += 1
                if error_msg and len(self.errors) < 5:
                    self.errors.append(error_msg)

    def summary(self):
        total = self.success + self.fail
        if not self.latencies:
            return f"  {self.name}: No requests completed"
        avg = statistics.mean(self.latencies)
        p50 = statistics.median(self.latencies)
        p95 = sorted(self.latencies)[int(len(self.latencies) * 0.95)] if len(self.latencies) > 1 else self.latencies[0]
        p99 = sorted(self.latencies)[int(len(self.latencies) * 0.99)] if len(self.latencies) > 1 else self.latencies[0]
        max_lat = max(self.latencies)
        rps = total / sum(self.latencies) if sum(self.latencies) > 0 else 0
        return (
            f"  {self.name}\n"
            f"    Requests: {total} | Success: {self.success} | Failed: {self.fail}\n"
            f"    Avg: {avg*1000:.1f}ms | P50: {p50*1000:.1f}ms | P95: {p95*1000:.1f}ms | P99: {p99*1000:.1f}ms | Max: {max_lat*1000:.1f}ms\n"
            f"    Throughput: ~{rps:.1f} req/s"
        )


def get_token(username=ADMIN_USER, password=ADMIN_PASS):
    """Login and return JWT token."""
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "username": username, "password": password
    })
    if resp.status_code == 200:
        return resp.json()["data"]["token"]
    raise Exception(f"Login failed: {resp.status_code} {resp.text}")


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def timed_request(method, url, result: StressResult, **kwargs):
    """Execute a request and record timing."""
    start = time.perf_counter()
    try:
        resp = method(url, **kwargs)
        latency = time.perf_counter() - start
        ok = resp.status_code in (200, 201)
        error_msg = None if ok else f"{resp.status_code}: {resp.text[:100]}"
        result.record(latency, ok, error_msg)
    except Exception as e:
        latency = time.perf_counter() - start
        result.record(latency, False, str(e)[:100])


# ── Test Scenarios ──

def stress_login(n, concurrency):
    """Stress test: POST /api/auth/login"""
    result = StressResult("POST /api/auth/login (login)")
    def task(_):
        timed_request(requests.post, f"{BASE_URL}/api/auth/login", result,
                      json={"username": ADMIN_USER, "password": ADMIN_PASS})
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        list(pool.map(task, range(n)))
    return result


def stress_login_invalid(n, concurrency):
    """Stress test: POST /api/auth/login with wrong password"""
    result = StressResult("POST /api/auth/login (invalid)")
    def task(_):
        start = time.perf_counter()
        try:
            resp = requests.post(f"{BASE_URL}/api/auth/login",
                                 json={"username": "admin", "password": "wrong"})
            latency = time.perf_counter() - start
            # 400 is expected here
            result.record(latency, resp.status_code == 400)
        except Exception as e:
            latency = time.perf_counter() - start
            result.record(latency, False, str(e)[:100])
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        list(pool.map(task, range(n)))
    return result


def stress_userinfo(token, n, concurrency):
    """Stress test: GET /api/auth/userinfo"""
    result = StressResult("GET  /api/auth/userinfo")
    headers = auth_headers(token)
    def task(_):
        timed_request(requests.get, f"{BASE_URL}/api/auth/userinfo", result, headers=headers)
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        list(pool.map(task, range(n)))
    return result


def stress_list_templates(token, n, concurrency):
    """Stress test: GET /api/templates"""
    result = StressResult("GET  /api/templates")
    headers = auth_headers(token)
    def task(_):
        timed_request(requests.get, f"{BASE_URL}/api/templates?page=1&page_size=10", result, headers=headers)
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        list(pool.map(task, range(n)))
    return result


def stress_list_forms(token, n, concurrency):
    """Stress test: GET /api/forms"""
    result = StressResult("GET  /api/forms")
    headers = auth_headers(token)
    def task(_):
        timed_request(requests.get, f"{BASE_URL}/api/forms?page=1&page_size=10", result, headers=headers)
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        list(pool.map(task, range(n)))
    return result


def stress_list_users(token, n, concurrency):
    """Stress test: GET /api/users"""
    result = StressResult("GET  /api/users")
    headers = auth_headers(token)
    def task(_):
        timed_request(requests.get, f"{BASE_URL}/api/users?page=1&page_size=10", result, headers=headers)
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        list(pool.map(task, range(n)))
    return result


def stress_list_logs(token, n, concurrency):
    """Stress test: GET /api/logs"""
    result = StressResult("GET  /api/logs")
    headers = auth_headers(token)
    def task(_):
        timed_request(requests.get, f"{BASE_URL}/api/logs?page=1&page_size=10", result, headers=headers)
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        list(pool.map(task, range(n)))
    return result


def stress_create_template(token, n, concurrency):
    """Stress test: POST /api/templates (create + delete)"""
    result = StressResult("POST /api/templates (create)")
    headers = auth_headers(token)
    counter = {"i": 0}
    counter_lock = threading.Lock()

    def task(_):
        with counter_lock:
            counter["i"] += 1
            idx = counter["i"]
        tpl_name = f"stress_tpl_{idx}_{time.time_ns()}"
        payload = {
            "name": tpl_name,
            "remark": "stress test",
            "meta_data": [{"name": "field1", "label": "Field 1", "type": "text", "required": True}]
        }
        timed_request(requests.post, f"{BASE_URL}/api/templates", result,
                      headers=headers, json=payload)

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        list(pool.map(task, range(n)))
    return result


def stress_create_form(token, template_id, n, concurrency):
    """Stress test: POST /api/forms (create form data)"""
    result = StressResult("POST /api/forms (create)")
    headers = auth_headers(token)

    def task(_):
        payload = {
            "template_id": template_id,
            "data": {"field1": f"value_{time.time_ns()}"}
        }
        timed_request(requests.post, f"{BASE_URL}/api/forms", result,
                      headers=headers, json=payload)

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        list(pool.map(task, range(n)))
    return result


def stress_mixed_read(token, n, concurrency):
    """Stress test: mixed read operations"""
    result = StressResult("MIXED read (templates+forms+users+logs)")
    headers = auth_headers(token)
    endpoints = [
        f"{BASE_URL}/api/templates?page=1&page_size=10",
        f"{BASE_URL}/api/forms?page=1&page_size=10",
        f"{BASE_URL}/api/users?page=1&page_size=10",
        f"{BASE_URL}/api/logs?page=1&page_size=10",
        f"{BASE_URL}/api/auth/userinfo",
    ]

    def task(i):
        url = endpoints[i % len(endpoints)]
        timed_request(requests.get, url, result, headers=headers)

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        list(pool.map(task, range(n)))
    return result


# ── Cleanup ──

def cleanup_stress_data(token):
    """Remove templates and forms created during stress tests."""
    headers = auth_headers(token)
    # Delete stress templates
    resp = requests.get(f"{BASE_URL}/api/templates?page=1&page_size=100&keyword=stress_tpl", headers=headers)
    if resp.status_code == 200:
        for tpl in resp.json().get("data", {}).get("list", []):
            requests.delete(f"{BASE_URL}/api/templates/{tpl['id']}", headers=headers)
    # Delete stress forms
    resp = requests.get(f"{BASE_URL}/api/forms?page=1&page_size=500", headers=headers)
    if resp.status_code == 200:
        for form in resp.json().get("data", {}).get("list", []):
            requests.delete(f"{BASE_URL}/api/forms/{form['id']}", headers=headers)


# ── Main ──

def main():
    n = REQUESTS_PER_TEST
    c = CONCURRENT_USERS

    print("\n" + "=" * 56)
    print("  Stress Test - Form Builder System API")
    print(f"  Concurrent users: {c} | Requests per test: {n}")
    print("=" * 56)

    # Login to get token
    print("\n  [SETUP] Logging in...")
    try:
        token = get_token()
        print("  [SETUP] Login OK")
    except Exception as e:
        print(f"  [SETUP] Login failed: {e}")
        sys.exit(1)

    # Create a template for form tests
    headers = auth_headers(token)
    tpl_resp = requests.post(f"{BASE_URL}/api/templates", headers=headers, json={
        "name": f"stress_base_{time.time_ns()}",
        "remark": "base template for stress test",
        "meta_data": [{"name": "field1", "label": "Field 1", "type": "text", "required": True}]
    })
    template_id = None
    if tpl_resp.status_code == 200:
        # Get the template ID
        resp = requests.get(f"{BASE_URL}/api/templates?page=1&page_size=1&keyword=stress_base", headers=headers)
        if resp.status_code == 200:
            tpl_list = resp.json().get("data", {}).get("list", [])
            if tpl_list:
                template_id = tpl_list[0]["id"]
                print(f"  [SETUP] Created base template (id={template_id})")

    all_results = []

    # Run tests
    tests = [
        ("Login (valid credentials)", lambda: stress_login(n, c)),
        ("Login (invalid credentials)", lambda: stress_login_invalid(n, c)),
        ("Get user info", lambda: stress_userinfo(token, n, c)),
        ("List templates", lambda: stress_list_templates(token, n, c)),
        ("List forms", lambda: stress_list_forms(token, n, c)),
        ("List users", lambda: stress_list_users(token, n, c)),
        ("List logs", lambda: stress_list_logs(token, n, c)),
        ("Create templates", lambda: stress_create_template(token, min(n, 50), c)),
        ("Mixed read operations", lambda: stress_mixed_read(token, n * 2, c)),
    ]

    if template_id:
        tests.insert(-1, ("Create form data", lambda: stress_create_form(token, template_id, n, c)))

    for label, test_fn in tests:
        print(f"\n  Running: {label}...")
        start = time.perf_counter()
        result = test_fn()
        elapsed = time.perf_counter() - start
        all_results.append(result)
        print(f"  Completed in {elapsed:.2f}s")

    # Summary
    print("\n" + "=" * 56)
    print("  RESULTS")
    print("=" * 56)
    for r in all_results:
        print(r.summary())
        if r.errors:
            print(f"    Sample errors: {r.errors[:3]}")
        print()

    # Overall stats
    total_reqs = sum(r.success + r.fail for r in all_results)
    total_success = sum(r.success for r in all_results)
    total_fail = sum(r.fail for r in all_results)
    all_latencies = []
    for r in all_results:
        all_latencies.extend(r.latencies)

    print("=" * 56)
    print(f"  OVERALL: {total_reqs} requests | {total_success} success | {total_fail} failed")
    if all_latencies:
        print(f"  Avg latency: {statistics.mean(all_latencies)*1000:.1f}ms")
        print(f"  P95 latency: {sorted(all_latencies)[int(len(all_latencies)*0.95)]*1000:.1f}ms")
    print("=" * 56 + "\n")

    # Cleanup
    print("  [CLEANUP] Removing stress test data...")
    cleanup_stress_data(token)
    print("  [CLEANUP] Done\n")

    sys.exit(1 if total_fail > total_reqs * 0.05 else 0)  # Fail if >5% errors


if __name__ == "__main__":
    main()
