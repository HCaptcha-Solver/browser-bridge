import test from "node:test";
import assert from "node:assert/strict";
import { setTimeout as sleep } from "node:timers/promises";
import { chromium } from "patchright";
import {
  HCaptchaSolver,
  BridgeError,
  ChallengeChanged,
} from "../javascript/index.mjs";
import { ApiClient, ApiError, retryDelay, origin } from "../javascript/api.mjs";
import { validateAction } from "../javascript/geometry.mjs";
import { fixture, fixtureServer } from "./fixture-server.mjs";

const geo = {
  canvases: [{ x: 10, y: 10, width: 980, height: 980 }],
  tiles: Array(9).fill({}),
};
test("validate full action before any movement", () => {
  assert.deepEqual(
    validateAction({ type: "point", points: [[250, 450]], indices: [99] }, geo),
    { type: "point", points: [[250, 450]] },
  );
  for (const invalid of [
    "https:",
    "https://x:bad",
    "http://public.example",
    "https://key@api.example",
    "https://api.example/path",
  ])
    assert.throws(() => origin(invalid));
  for (const action of [
    { type: "point", points: [[250, 450]] },
    { type: "grid", indices: [0, 4, 8] },
    { type: "drag", moves: [{ source: [200, 200], target: [700, 700] }] },
  ])
    assert.deepEqual(validateAction(action, geo), action);
  for (const action of [
    null,
    { type: "rotate" },
    { type: "grid", indices: [0, 0] },
    { type: "grid", indices: [true] },
    {
      type: "point",
      points: [
        [500, 500],
        [500, 500],
      ],
    },
    { type: "point", points: [[0, 500]] },
    { type: "point", points: [[999, 500]] },
    { type: "point", points: [[NaN, 500]] },
    { type: "drag", moves: [{ source: [200, 200], target: [200, 200] }] },
  ])
    assert.throws(() => validateAction(action, geo), BridgeError);
});
test("429 retry preserves body, idempotency key and API origin", async () => {
  const seen = [];
  const api = new ApiClient("fixture", "http://localhost", {
    send: async (url, options) => {
      seen.push({ url, ...options });
      return new Response(
        JSON.stringify(
          seen.length === 1 ? { error: "rate_limited" } : { status: "ready" },
        ),
        {
          status: seen.length === 1 ? 429 : 200,
          headers: { "Retry-After": "1" },
        },
      );
    },
  });
  await api.solve(
    { challenge_id: "test" },
    "same-operation",
    AbortSignal.timeout(10000),
  );
  assert.equal(seen.length, 2);
  assert.equal(seen[0].url, "http://localhost/v2/solutions");
  assert.equal(seen[0].body, seen[1].body);
  assert.equal(
    seen[0].headers["Idempotency-Key"],
    seen[1].headers["Idempotency-Key"],
  );
  assert.equal(retryDelay("2"), 2000);
  assert.equal(retryDelay("invalid"), 1000);
});
test("auth, billing, validation and redirect errors are not retried", async () => {
  for (const status of [301, 401, 402, 403, 422]) {
    let calls = 0;
    const api = new ApiClient("fixture", "http://localhost", {
      send: async () => {
        calls++;
        return new Response('{"error":"fixture"}', { status });
      },
    });
    await assert.rejects(
      api.solve({}, "idem", AbortSignal.timeout(1000)),
      ApiError,
    );
    assert.equal(calls, 1);
  }
});
async function browserFixture(t, mode = "flow", scale = 1) {
  const server = await fixtureServer(mode);
  const browser = await chromium.launch({ channel: "chrome", headless: true });
  t.after(async () => {
    await browser.close();
    await server.close();
  });
  const context = await browser.newContext({
    viewport: { width: 1100, height: 800 },
    deviceScaleFactor: 2,
  });
  await context.route("https://fixture.hcaptcha.com/**", (route) =>
    route.fulfill({
      contentType: "text/html",
      body: fixture(
        route.request().url().includes("checkbox") ? "checkbox" : "challenge",
      ).replace("MODE", JSON.stringify(mode)),
    }),
  );
  const page = await context.newPage();
  await page.goto(`${server.url}?mode=${mode}&scale=${scale}`);
  return {
    server,
    page,
    solver: new HCaptchaSolver(page, "fixture", {
      apiUrl: server.url,
      timeout: 35,
    }),
  };
}
for (const [mode, scale, rounds] of [
  ["flow", 1, 3],
  ["flow", 0.75, 3],
  ["grid_all", 0.8, 1],
  ["auto", 0.75, 3],
  ["no_visual", 1, 0],
]) {
  test(`real Chrome: ${mode}, scale ${scale}`, async (t) => {
    const { server, page, solver } = await browserFixture(t, mode, scale);
    assert.ok(
      ["synthetic-token-test-only", "synthetic-token-no-visual"].includes(
        await solver.solve(),
      ),
    );
    assert.equal(solver.stats.rounds, rounds);
    assert.equal(solver.stats.charged_micro_usd, rounds * 2000);
    assert.deepEqual(server.feedback, rounds ? [{ success: true }] : []);
    assert.equal(page.isClosed(), false);
  });
}
test("discard stale prediction and infer new image", async (t) => {
  const { server, page, solver } = await browserFixture(t, "stale");
  const solving = solver.solve();
  let failed;
  solving.catch((error) => {
    failed = error;
  });
  const deadline = Date.now() + 10000;
  while (!server.calls.length) {
    if (failed) throw failed;
    assert.ok(Date.now() < deadline, "fixture API request did not arrive");
    await sleep(30);
  }
  await page.frames().at(-1).evaluate("document.body.dataset.change='now'");
  assert.equal(await solving, "synthetic-token-test-only");
  assert.equal(solver.stats.discarded, 1);
  assert.equal(solver.stats.rounds, 2);
});
test("stop remaining clicks when the challenge changes", async (t) => {
  const { page, solver } = await browserFixture(t, "mid_change");
  await assert.rejects(solver.solve(), ChallengeChanged);
  await sleep(40);
  const state = JSON.parse(
    await page.frames().at(-1).locator("body").getAttribute("data-state"),
  );
  assert.equal(state.hits.length, 1);
  assert.equal(state.submissions, 0);
});
test("round and overall timeout budgets", async (t) => {
  const { page, server } = await browserFixture(t);
  const solver = new HCaptchaSolver(page, "fixture", {
    apiUrl: server.url,
    maxRounds: 1,
    timeout: 20,
  });
  assert.equal(await solver.solve(), null);
  assert.equal(solver.stats.reason, "max_rounds");
  assert.equal(server.calls.length, 1);
  await page.goto("about:blank");
  const empty = new HCaptchaSolver(page, "fixture", {
    apiUrl: server.url,
    timeout: 0.3,
  });
  assert.equal(await empty.solve(), null);
  assert.equal(empty.stats.reason, "timeout");
});
test("cancellation during drag releases mouse and keeps page open", async (t) => {
  const { page, solver } = await browserFixture(t, "drag_cancel");
  const controller = new AbortController(),
    original = page.mouse.down.bind(page.mouse);
  page.mouse.down = async (options) => {
    await original(options);
    setTimeout(() => controller.abort(), 50);
  };
  await assert.rejects(solver.solve({ signal: controller.signal }));
  assert.equal(solver.stats.reason, "cancelled");
  assert.equal(page.isClosed(), false);
  await sleep(40);
  assert.ok(
    JSON.parse(
      await page.frames().at(-1).locator("body").getAttribute("data-state"),
    ).ups >= 1,
  );
});

test("rejection, loading and new task with an error banner", async (t) => {
  const { solver, server } = await browserFixture(t, "rejected");
  assert.equal(await solver.solve(), "synthetic-token-test-only");
  assert.equal(server.calls.length, 2);
  assert.notEqual(server.calls[0].question, server.calls[1].question);
  assert.deepEqual(server.feedback, [{ success: false }, { success: true }]);
});
test("multiple widgets cannot return an unrelated hidden token", async (t) => {
  const { page, server, solver } = await browserFixture(t);
  await page.evaluate(() => {
    const other = document.createElement("iframe");
    other.src = "https://fixture.hcaptcha.com/checkbox#frame=checkbox&id=other";
    other.style.display = "none";
    document.body.append(other);
    const token = document.createElement("textarea");
    token.name = "h-captcha-response";
    token.id = "h-captcha-response-other";
    token.value = "synthetic-unrelated-token";
    document.body.prepend(token);
  });
  for (
    let i = 0;
    i < 50 && !page.frames().some((f) => f.url().includes("id=other"));
    i++
  )
    await sleep(20);
  await assert.rejects(solver.solve(), /Multiple hCaptcha/);
  assert.equal(server.calls.length, 0);
  const selected = new HCaptchaSolver(page, "fixture", {
    apiUrl: server.url,
    widgetId: "bridge",
    timeout: 35,
  });
  assert.equal(await selected.solve(), "synthetic-token-test-only");
  assert.equal(selected.stats.rounds, 3);
});
