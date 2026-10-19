import { chromium } from "patchright";
import { HCaptchaSolver } from "../index.mjs";

const API_KEY = process.env.HCAPTCHA_API_KEY;
const URL = "https://example.com/your-page"; // Replace with the page containing hCaptcha.
const MAX_ROUNDS = 6;
const TIMEOUT = 90; // Seconds.

if (!API_KEY) throw new Error("Set HCAPTCHA_API_KEY.");
if (URL === "https://example.com/your-page") {
  throw new Error("Replace URL with the page containing hCaptcha.");
}
const browser = await chromium.launch({ channel: "chrome", headless: false });
try {
  const page = await browser.newPage();
  await page.goto(URL, { waitUntil: "domcontentloaded" });
  // Your navigation or form filling can go here.
  const solver = new HCaptchaSolver(page, API_KEY, { maxRounds: MAX_ROUNDS, timeout: TIMEOUT });
  const token = await solver.solve();
  if (!token) throw new Error("No token received. Check solver.stats for the reason.");

  // Use `token` here, or continue your automation on this page.
  console.log("Token received.");
} finally {
  await browser.close();
}
