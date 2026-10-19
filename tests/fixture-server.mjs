import { createServer } from "node:http";
import { readFileSync } from "node:fs";
import { setTimeout as sleep } from "node:timers/promises";
import assert from "node:assert/strict";

export const fixture = (name) =>
  readFileSync(new URL(`./fixtures/${name}.html`, import.meta.url), "utf8");
export async function fixtureServer(mode = "flow") {
  const state = { mode, calls: [], feedback: [] };
  const server = createServer(async (req, res) => {
    if (req.method === "GET") {
      res.writeHead(200, { "Content-Type": "text/html" });
      res.end(fixture("page"));
      return;
    }
    try {
      let raw = "";
      for await (const chunk of req) raw += chunk;
      const body = JSON.parse(raw);
      const send = (value) => {
        res.writeHead(200, { "Content-Type": "application/json" });
        res.end(JSON.stringify(value));
      };
      if (req.url.endsWith("/feedback")) {
        state.feedback.push(body);
        send({ accepted: true });
        return;
      }
      assert.equal(req.url, "/v2/solutions");
      state.calls.push(body);
      assert.deepEqual(
        Object.keys(body).sort(),
        [
          "protocol",
          "question",
          "challenge_id",
          "image",
          "references",
          "canvases",
          "tiles",
        ].sort(),
      );
      assert.equal(body.references.length, 1);
      if (mode === "stale" && state.calls.length === 1) await sleep(800);
      let action;
      if (body.tiles.length)
        action = {
          type: "grid",
          indices:
            mode === "grid_all" ? [0, 1, 2, 3, 4, 5, 6, 7, 8] : [0, 4, 8],
        };
      else {
        const r = body.canvases[0];
        const points = [
          [0.25, 0.3],
          [0.7, 0.65],
        ].map(([x, y]) => [
          Math.round(r.x + r.width * x),
          Math.round(r.y + r.height * y),
        ]);
        action = body.question.startsWith("Drag")
          ? { type: "drag", moves: [{ source: points[0], target: points[1] }] }
          : { type: "point", points };
      }
      send({
        id: `fixture-${state.calls.length}`,
        status: "ready",
        billing: { charged: 2000, currency: "USD" },
        result: {
          protocol: "1",
          challenge_id: body.challenge_id,
          coordinate_space: "full_challenge_image_0_1000",
          action,
        },
      });
    } catch (error) {
      res.writeHead(500, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ error: error.message }));
    }
  });
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  return {
    ...state,
    url: `http://127.0.0.1:${server.address().port}`,
    close: () => new Promise((resolve) => server.close(resolve)),
  };
}
