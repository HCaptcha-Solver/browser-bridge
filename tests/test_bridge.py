import asyncio
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import httpx
import pytest
from hcaptcha_bridge import BridgeError, ChallengeChanged, HCaptchaSolver
from hcaptcha_bridge.api import ApiClient, ApiError, origin, retry_delay
from hcaptcha_bridge.geometry import validate_action
from patchright.async_api import async_playwright

FIXTURES = Path(__file__).parent / "fixtures"
GEO = {"canvases": [{"x": 10, "y": 10, "width": 980, "height": 980}], "tiles": [{}] * 9}


@pytest.mark.parametrize(
    "action",
    [
        {"type": "point", "points": [[250, 450]]},
        {"type": "grid", "indices": [0, 4, 8]},
        {"type": "drag", "moves": [{"source": [200, 200], "target": [700, 700]}]},
    ],
)
def test_valid_actions(action):
    assert validate_action(action, GEO) == action


@pytest.mark.parametrize(
    "action",
    [
        None,
        {"type": "rotate"},
        {"type": "grid", "indices": [0, 0]},
        {"type": "grid", "indices": [True]},
        {"type": "point", "points": [[500, 500], [500, 500]]},
        {"type": "point", "points": [[0, 500]]},
        {"type": "point", "points": [[999, 500]]},
        {"type": "point", "points": [[float("nan"), 500]]},
        {"type": "drag", "moves": [{"source": [200, 200], "target": [200, 200]}]},
    ],
)
def test_invalid_actions(action):
    with pytest.raises(BridgeError):
        validate_action(action, GEO)


def test_action_fields_and_api_origin():
    assert validate_action({"type": "point", "points": [[250, 450]], "indices": [99]}, GEO) == {
        "type": "point",
        "points": [[250, 450]],
    }
    for invalid in (
        "https:",
        "https://x:bad",
        "http://public.example",
        "https://key@api.example",
        "https://api.example/path",
    ):
        with pytest.raises(ValueError):
            origin(invalid)
    assert retry_delay("2") == 2 and retry_delay("NaN") == retry_delay("Infinity") == 1


async def test_retries_keep_body_and_id(monkeypatch):
    seen = []

    async def respond(request):
        seen.append(request)
        return (
            httpx.Response(429, headers={"Retry-After": "1"}, json={"error": "rate_limited"})
            if len(seen) == 1
            else httpx.Response(200, json={"status": "ready"})
        )

    async def sleep(_):
        pass

    monkeypatch.setattr("hcaptcha_bridge.api.asyncio.sleep", sleep)
    client = ApiClient("fixture", "http://localhost", transport=httpx.MockTransport(respond))
    try:
        await client.solve({"challenge_id": "test"}, "same-operation", time.monotonic() + 20)
        assert len(seen) == 2
        assert seen[0].content == seen[1].content
        assert (
            seen[0].headers["Idempotency-Key"]
            == seen[1].headers["Idempotency-Key"]
            == "same-operation"
        )
        assert seen[0].url.path == "/v2/solutions"
    finally:
        await client.close()


@pytest.mark.parametrize("status", [301, 401, 402, 403, 422])
async def test_nonretryable_errors(status):
    calls = []

    def respond(request):
        calls.append(request)
        return httpx.Response(
            status, headers={"Location": "https://other.example"}, json={"error": "fixture"}
        )

    client = ApiClient("fixture", "http://localhost", transport=httpx.MockTransport(respond))
    try:
        with pytest.raises(ApiError):
            await client.solve({}, "idem", time.monotonic() + 20)
        assert len(calls) == 1
    finally:
        await client.close()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def respond(self, value, status=200):
        data = json.dumps(value).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        data = (FIXTURES / "page.html").read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        if self.path.endswith("/feedback"):
            self.server.feedback.append(body)
            return self.respond({"accepted": True})
        self.server.calls.append(body)
        assert self.path == "/v2/solutions"
        assert set(body) - {"frames"} == {
            "protocol",
            "question",
            "challenge_id",
            "image",
            "references",
            "canvases",
            "tiles",
        }
        assert len(body["references"]) == 1
        if self.server.mode.startswith("animated"):
            assert 1 <= len(body["frames"]) <= 5
        if self.server.mode == "stale" and len(self.server.calls) == 1:
            time.sleep(0.8)
        if body["tiles"]:
            action = {
                "type": "grid",
                "indices": list(range(9)) if self.server.mode == "grid_all" else [0, 4, 8],
            }
        else:
            r = body["canvases"][0]
            points = [
                [round(r["x"] + r["width"] * x), round(r["y"] + r["height"] * y)]
                for x, y in [(0.25, 0.3), (0.7, 0.65)]
            ]
            action = (
                {"type": "drag", "moves": [{"source": points[0], "target": points[1]}]}
                if body["question"].startswith("Drag")
                else {"type": "point", "points": points}
            )
        self.respond(
            {
                "id": "fixture-" + str(len(self.server.calls)),
                "status": "ready",
                "billing": {"charged": 2000, "currency": "USD"},
                "result": {
                    "protocol": "1",
                    "challenge_id": body["challenge_id"],
                    "coordinate_space": "full_challenge_image_0_1000",
                    "action": action,
                },
            }
        )


@pytest.fixture
def server():
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.calls = []
    server.feedback = []
    server.mode = "flow"
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server
    server.shutdown()
    server.server_close()
    thread.join()


@pytest.fixture
async def page(server):
    async with async_playwright() as runtime:
        browser = await runtime.chromium.launch(channel="chrome", headless=True)
        context = await browser.new_context(
            viewport={"width": 1100, "height": 800}, device_scale_factor=2
        )

        async def resource(route):
            name = "checkbox" if "checkbox" in route.request.url else "challenge"
            body = (
                (FIXTURES / (name + ".html")).read_text().replace("MODE", json.dumps(server.mode))
            )
            await route.fulfill(body=body, content_type="text/html")

        await context.route("https://fixture.hcaptcha.com/**", resource)
        page = await context.new_page()
        yield page
        await browser.close()


@pytest.mark.parametrize(
    "mode,scale,rounds",
    [
        ("flow", 1, 3),
        ("flow", 0.75, 3),
        ("grid_all", 0.8, 1),
        ("auto", 0.75, 3),
        ("no_visual", 1, 0),
        ("animated", 1, 1),
        ("animated", .75, 1),
    ],
)
async def test_real_chrome_full_flow(page, server, mode, scale, rounds):
    server.mode = mode
    url = f"http://127.0.0.1:{server.server_port}"
    await page.goto(url + f"?mode={mode}&scale={scale}")
    solver = HCaptchaSolver(page, "fixture", api_url=url, timeout=35)
    assert await solver.solve() in ("synthetic-token-test-only", "synthetic-token-no-visual")
    assert solver.stats["rounds"] == rounds
    assert solver.stats["charged_micro_usd"] == rounds * 2000
    assert server.feedback == ([{"success": True}] if rounds else [])
    assert not page.is_closed()


async def test_stale_prediction_is_discarded(page, server):
    server.mode = "stale"
    url = f"http://127.0.0.1:{server.server_port}"
    await page.goto(url)
    solver = HCaptchaSolver(page, "fixture", api_url=url, timeout=20)
    task = asyncio.create_task(solver.solve())
    while not server.calls:
        await asyncio.sleep(0.03)
    await page.frames[-1].evaluate("document.body.dataset.change='now'")
    assert await task == "synthetic-token-test-only"
    assert solver.stats["discarded"] == 1 and solver.stats["rounds"] == 2


async def test_change_between_clicks_stops_remaining_actions(page, server):
    server.mode = "mid_change"
    url = f"http://127.0.0.1:{server.server_port}"
    await page.goto(url)
    solver = HCaptchaSolver(page, "fixture", api_url=url, timeout=20)
    with pytest.raises(ChallengeChanged):
        await solver.solve()
    await asyncio.sleep(0.04)
    state = json.loads(await page.frames[-1].locator("body").get_attribute("data-state"))
    assert len(state["hits"]) == 1 and state["submissions"] == 0


@pytest.mark.parametrize("mode", ["animated_change", "animated_reference"])
async def test_animation_never_hides_new_scene_or_reference(page, server, mode):
    server.mode = mode
    url = f"http://127.0.0.1:{server.server_port}"
    await page.goto(url)
    solver = HCaptchaSolver(page, "fixture", api_url=url, timeout=25)
    with pytest.raises(ChallengeChanged):
        await solver.solve()
    await asyncio.sleep(.04)
    state = json.loads(await page.frames[-1].locator("body").get_attribute("data-state"))
    assert len(state["hits"]) == 1 and state["submissions"] == 0


async def test_round_limit_and_timeout(page, server):
    url = f"http://127.0.0.1:{server.server_port}"
    await page.goto(url)
    solver = HCaptchaSolver(page, "fixture", api_url=url, max_rounds=1, timeout=20)
    assert await solver.solve() is None
    assert solver.stats["reason"] == "max_rounds" and len(server.calls) == 1
    await page.goto("about:blank")
    solver = HCaptchaSolver(page, "fixture", api_url=url, timeout=0.3)
    assert await solver.solve() is None
    assert solver.stats["reason"] == "timeout"


async def test_cancel_releases_mouse(page, server):
    server.mode = "drag_cancel"
    url = f"http://127.0.0.1:{server.server_port}"
    await page.goto(url)
    solver = HCaptchaSolver(page, "fixture", api_url=url, timeout=20)
    original = page.mouse.down
    task = None

    async def down(**kwargs):
        await original(**kwargs)
        asyncio.get_running_loop().call_later(0.05, task.cancel)

    page.mouse.down = down
    task = asyncio.create_task(solver.solve())
    with pytest.raises(asyncio.CancelledError):
        await task
    assert solver.stats["reason"] == "cancelled"
    await asyncio.sleep(0.04)
    assert json.loads(await page.frames[-1].locator("body").get_attribute("data-state"))["ups"] >= 1


async def test_rejection_loading_then_new_task(page, server):
    server.mode = "rejected"
    url = f"http://127.0.0.1:{server.server_port}"
    await page.goto(url)
    solver = HCaptchaSolver(page, "fixture", api_url=url, timeout=25)
    assert await solver.solve() == "synthetic-token-test-only"
    assert len(server.calls) == 2
    assert server.calls[0]["question"] != server.calls[1]["question"]
    assert server.feedback == [{"success": False}, {"success": True}]


async def test_multiple_widgets_cannot_return_unrelated_token(page, server):
    url = f"http://127.0.0.1:{server.server_port}"
    await page.goto(url)
    await page.evaluate("""() => {
      const other=document.createElement('iframe');
      other.src='https://fixture.hcaptcha.com/checkbox#frame=checkbox&id=other';
      other.style.display='none';document.body.append(other);
      const token=document.createElement('textarea');token.name='h-captcha-response';
      token.id='h-captcha-response-other';token.value='synthetic-unrelated-token';document.body.prepend(token);
    }""")
    await page.wait_for_function("[...document.querySelectorAll('iframe')].length===3")
    for _ in range(50):
        if any("id=other" in f.url for f in page.frames):
            break
        await asyncio.sleep(0.02)
    with pytest.raises(BridgeError, match="Multiple hCaptcha"):
        await HCaptchaSolver(page, "fixture", api_url=url).solve()
    assert not server.calls
    solver = HCaptchaSolver(page, "fixture", api_url=url, widget_id="bridge", timeout=35)
    assert await solver.solve() == "synthetic-token-test-only"
    assert solver.stats["rounds"] == 3
