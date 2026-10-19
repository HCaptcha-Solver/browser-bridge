# hCaptcha Browser Bridge

[🇺🇸 English](README.md) · [🇧🇷 Português](README.pt-BR.md) · [🇩🇪 Deutsch](README.de.md) · [🇪🇸 Español](README.es.md)

Lösen Sie hCaptcha mit unserer API in Ihrem eigenen Chrome. Verfügbar für Python und Node.js.

Benötigt Google Chrome, Python 3.11+ oder Node.js 22+.

## Konfiguration

Erstellen Sie Ihren API-Schlüssel auf [hcaptchasolver.org](https://hcaptchasolver.org/) und laden Sie Guthaben auf.

Ersetzen Sie `URL` im Beispiel durch die **Seite, auf der hCaptcha angezeigt wird**. Nach `solve()` steht die Antwort in `token`. Setzen Sie Ihre Automatisierung an der markierten Stelle fort.

| Variable | Einstellung |
|---|---|
| `HCAPTCHA_API_KEY` | API-Schlüssel Ihres Kontos |
| `URL` | URL Ihrer Seite |
| `MAX_ROUNDS` | Maximale Anzahl der Runden: `6` |
| `TIMEOUT` | Zeitlimit in Sekunden: `90` |

Klonen Sie das Repository und setzen Sie Ihren Schlüssel:

```bash
git clone https://github.com/HCaptcha-Solver/browser-bridge.git
cd browser-bridge
export HCAPTCHA_API_KEY="YOUR_API_KEY"
```

PowerShell: `$env:HCAPTCHA_API_KEY = "IHR_SCHLUESSEL"`.

## Python

```bash
python -m pip install -e '.[browser]'
python -m patchright install chrome
```

URL anpassen und ausführen: [python/examples/solve.py](python/examples/solve.py).

```bash
python python/examples/solve.py
```

```python
import asyncio, os
from patchright.async_api import async_playwright
from hcaptcha_bridge import HCaptchaSolver

URL = "https://example.com/your-page"  # URL Ihrer Seite.

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
                # Hier das Token verwenden oder Ihre Automatisierung fortsetzen.
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

URL anpassen und ausführen: [javascript/examples/solve.mjs](javascript/examples/solve.mjs).

```bash
node javascript/examples/solve.mjs
```

```js
import { chromium } from "patchright";
import { HCaptchaSolver } from "./javascript/index.mjs";

const URL = "https://example.com/your-page"; // URL Ihrer Seite.
const browser = await chromium.launch({ channel: "chrome", headless: false });
try {
  const page = await browser.newPage();
  await page.goto(URL);
  const solver = new HCaptchaSolver(page, process.env.HCAPTCHA_API_KEY, {
    maxRounds: 6, timeout: 90,
  });
  const token = await solver.solve();
  if (token) {
    // Hier das Token verwenden oder Ihre Automatisierung fortsetzen.
  }
} finally {
  await browser.close();
}
```

Bereits eine Seite geöffnet? Übergeben Sie sie direkt an `HCaptchaSolver`; ein weiterer Browser ist nicht erforderlich.
