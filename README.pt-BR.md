# hCaptcha Browser Bridge

[🇺🇸 English](README.md) · [🇧🇷 Português](README.pt-BR.md) · [🇩🇪 Deutsch](README.de.md) · [🇪🇸 Español](README.es.md)

Resolva hCaptcha com nossa API usando seu próprio Chrome. Disponível para Python e Node.js.

Requer Google Chrome, Python 3.11+ ou Node.js 22+.

## Configuração

Crie sua chave de API em [hcaptchasolver.org](https://hcaptchasolver.org/) e adicione saldo à conta.

Troque `URL` no exemplo pela **página que exibe o hCaptcha**. Depois de `solve()`, a resposta fica na variável `token`. Continue sua automação na linha indicada.

| Variável | Configuração |
|---|---|
| `HCAPTCHA_API_KEY` | Chave de API da sua conta |
| `URL` | URL da sua página |
| `MAX_ROUNDS` | Máximo de rodadas: `6` |
| `TIMEOUT` | Tempo limite em segundos: `90` |

Clone o repositório e configure sua chave:

```bash
git clone https://github.com/HCaptcha-Solver/browser-bridge.git
cd browser-bridge
export HCAPTCHA_API_KEY="YOUR_API_KEY"
```

PowerShell: `$env:HCAPTCHA_API_KEY = "SUA_CHAVE"`.

## Python

```bash
python -m pip install -e '.[browser]'
python -m patchright install chrome
```

Edite a URL e execute: [python/examples/solve.py](python/examples/solve.py).

```bash
python python/examples/solve.py
```

```python
import asyncio, os
from patchright.async_api import async_playwright
from hcaptcha_bridge import HCaptchaSolver

URL = "https://example.com/your-page"  # URL da sua página.

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
                # Use o token ou continue sua automação aqui.
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

Edite a URL e execute: [javascript/examples/solve.mjs](javascript/examples/solve.mjs).

```bash
node javascript/examples/solve.mjs
```

```js
import { chromium } from "patchright";
import { HCaptchaSolver } from "./javascript/index.mjs";

const URL = "https://example.com/your-page"; // URL da sua página.
const browser = await chromium.launch({ channel: "chrome", headless: false });
try {
  const page = await browser.newPage();
  await page.goto(URL);
  const solver = new HCaptchaSolver(page, process.env.HCAPTCHA_API_KEY, {
    maxRounds: 6, timeout: 90,
  });
  const token = await solver.solve();
  if (token) {
    // Use o token ou continue sua automação aqui.
  }
} finally {
  await browser.close();
}
```

Já tem uma página aberta? Passe-a diretamente para `HCaptchaSolver`; não precisa abrir outro navegador.
