# hCaptcha Browser Bridge

[🇺🇸 English](README.md) · [🇧🇷 Português](README.pt-BR.md) · [🇩🇪 Deutsch](README.de.md) · [🇪🇸 Español](README.es.md)

Resuelve hCaptcha con nuestra API usando tu propio Chrome. Disponible para Python y Node.js.

Requiere Google Chrome, Python 3.11+ o Node.js 22+.

## Configuración

Crea tu clave de API en [hcaptchasolver.org](https://hcaptchasolver.org/) y añade saldo a tu cuenta.

Cambia `URL` en el ejemplo por la **página que muestra hCaptcha**. Después de `solve()`, la respuesta queda en `token`. Continúa tu automatización en la línea indicada.

| Variable | Configuración |
|---|---|
| `HCAPTCHA_API_KEY` | Clave de API de tu cuenta |
| `URL` | URL de tu página |
| `MAX_ROUNDS` | Máximo de rondas: `6` |
| `TIMEOUT` | Tiempo límite en segundos: `90` |

Clona el repositorio y configura tu clave:

```bash
git clone https://github.com/HCaptcha-Solver/browser-bridge.git
cd browser-bridge
export HCAPTCHA_API_KEY="YOUR_API_KEY"
```

PowerShell: `$env:HCAPTCHA_API_KEY = "TU_CLAVE"`.

## Python

```bash
python -m pip install -e '.[browser]'
python -m patchright install chrome
```

Edita la URL y ejecuta: [python/examples/solve.py](python/examples/solve.py).

```bash
python python/examples/solve.py
```

```python
import asyncio, os
from patchright.async_api import async_playwright
from hcaptcha_bridge import HCaptchaSolver

URL = "https://example.com/your-page"  # URL de tu página.

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
                # Usa el token o continúa tu automatización aquí.
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

Edita la URL y ejecuta: [javascript/examples/solve.mjs](javascript/examples/solve.mjs).

```bash
node javascript/examples/solve.mjs
```

```js
import { chromium } from "patchright";
import { HCaptchaSolver } from "./javascript/index.mjs";

const URL = "https://example.com/your-page"; // URL de tu página.
const browser = await chromium.launch({ channel: "chrome", headless: false });
try {
  const page = await browser.newPage();
  await page.goto(URL);
  const solver = new HCaptchaSolver(page, process.env.HCAPTCHA_API_KEY, {
    maxRounds: 6, timeout: 90,
  });
  const token = await solver.solve();
  if (token) {
    // Usa el token o continúa tu automatización aquí.
  }
} finally {
  await browser.close();
}
```

¿Ya tienes una página abierta? Pásala directamente a `HCaptchaSolver`; no necesitas abrir otro navegador.
