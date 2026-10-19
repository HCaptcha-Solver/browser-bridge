# hCaptcha Browser Bridge

[🇺🇸 English](README.md) · [🇧🇷 Português](README.pt-BR.md) · [🇩🇪 Deutsch](README.de.md) · [🇪🇸 Español](README.es.md)

Resolve hCaptcha with our API using your own Chrome. Available for Python and Node.js.

Requires Google Chrome, Python 3.11+ or Node.js 22+.

## Configuration

Create your API key at [hcaptchasolver.org](https://hcaptchasolver.org/) and add credit to your account.

Replace `URL` in the example with the **page that displays hCaptcha**. After `solve()`, the response is available in `token`. Continue your automation at the marked line.

| Variable | Setting |
|---|---|
| `HCAPTCHA_API_KEY` | Your account API key |
| `URL` | Your page URL |
| `MAX_ROUNDS` | Maximum number of rounds: `6` |
| `TIMEOUT` | Timeout in seconds: `90` |

Clone the repository and set your key:

```bash
git clone https://github.com/HCaptcha-Solver/browser-bridge.git
cd browser-bridge
export HCAPTCHA_API_KEY="YOUR_API_KEY"
```

PowerShell: `$env:HCAPTCHA_API_KEY = "YOUR_API_KEY"`.

## Python

```bash
python -m pip install -e '.[browser]'
python -m patchright install chrome
```

Edit the URL and run: [python/examples/solve.py](python/examples/solve.py).

```bash
python python/examples/solve.py
```

```python
import asyncio, os
from patchright.async_api import async_playwright
from hcaptcha_bridge import HCaptchaSolver

URL = "https://example.com/your-page"  # Your page URL.

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="chrome", headless=False)
        try:
            page = await browser.new_page()
            await page.goto(URL)
            solver = HCaptchaSolver(page, os.environ["HCAPTCHA_API_KEY"],
                                    max_rounds=6, timeout=90)
            token = await solver.solve()
            if token:
                # Use the token or continue your automation here.
                pass
        finally:
            await browser.close()

asyncio.run(main())
```

## Node.js

```bash
npm ci
npx patchright install chrome
```

Edit the URL and run: [javascript/examples/solve.mjs](javascript/examples/solve.mjs).

```bash
node javascript/examples/solve.mjs
```

```js
import { chromium } from "patchright";
import { HCaptchaSolver } from "./javascript/index.mjs";

const URL = "https://example.com/your-page"; // Your page URL.
const browser = await chromium.launch({ channel: "chrome", headless: false });
try {
  const page = await browser.newPage();
  await page.goto(URL);
  const solver = new HCaptchaSolver(page, process.env.HCAPTCHA_API_KEY, {
    maxRounds: 6, timeout: 90,
  });
  const token = await solver.solve();
  if (token) {
    // Use the token or continue your automation here.
  }
} finally {
  await browser.close();
}
```

Already have an open page? Pass it directly to `HCaptchaSolver`; you do not need to open another browser.
