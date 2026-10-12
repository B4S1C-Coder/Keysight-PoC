
import asyncio
import json

from playwright.async_api import async_playwright

MPN = "91864A028"
URL = f"https://www.mcmaster.com/{MPN}/"

ENDPOINTS = (
    "ProductContent.aspx",
    "ProductOrderInfo.aspx",
    "ItmPrsnttnWebPart.aspx",
)


async def inspect_response(response):
    if "mcmaster.com" not in response.url:
        return

    if not any(endpoint.lower() in response.url.lower()
               for endpoint in ENDPOINTS):
        return

    request = response.request

    print(f"\n{'=' * 80}")
    print(f"HTTP {response.status} {request.method}")
    print("URL:", response.url)
    print("Resource type:", request.resource_type)
    print("Content type:", response.headers.get("content-type"))
    print("Initiator frame:", request.frame.url)

    # Print only non-sensitive request metadata.
    print("Request headers:")
    headers = await request.all_headers()
    for key in ("accept", "content-type", "referer", "origin"):
        if key in headers:
            print(f"  {key}: {headers[key]}")

    try:
        body = await response.text()
    except Exception as exc:
        print("Could not read response body:", exc)
        return

    if response.status == 403:
        print("\n403 response body (first 3000 characters):")
        print(body[:3000])
    elif "ProductOrderInfo.aspx".lower() in response.url.lower():
        print("\nOrder metadata:")
        try:
            print(json.dumps(json.loads(body), indent=2)[:5000])
        except json.JSONDecodeError:
            print(body[:3000])
    elif "ProductContent.aspx".lower() in response.url.lower():
        print("\nProduct content (first 3000 characters):")
        print(body[:3000])


async def main():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        page.set_default_timeout(15_000)

        page.on(
            "response",
            lambda response: asyncio.create_task(
                inspect_response(response)
            ),
        )

        try:
            print("Navigating to:", URL)
            response = await page.goto(
                URL,
                wait_until="domcontentloaded",
            )

            print("\nInitial HTTP status:",
                  response.status if response else "unknown")
            print("Final URL:", page.url)
            print("Browser user agent:",
                  await page.evaluate("navigator.userAgent"))
            print("Language:",
                  await page.evaluate("navigator.language"))
            print("Platform:",
                  await page.evaluate("navigator.platform"))

            # Let normal page requests finish.
            await page.wait_for_timeout(5000)

            print("\nRendered page text:")
            print((await page.locator("body").inner_text())[:6000])

            screenshot = "mcmaster_investigation.png"
            await page.screenshot(
                path=screenshot,
                full_page=True,
            )
            print(f"\nScreenshot saved: {screenshot}")

        finally:
            await context.close()
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
