
import asyncio
import json

from playwright.async_api import async_playwright

MPN = "91864A028"
BASE_URL = "https://www.mcmaster.com"


async def main():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)

        # Fresh context: no login, cookies, or saved session.
        context = await browser.new_context()
        page = await context.new_page()
        page.set_default_timeout(15_000)

        async def inspect_response(response):
            url = response.url

            if any(term in url.lower() for term in (
                "websrcheng",
                "productcontent",
                "productorderinfo",
                "itmprsnttnwebpart",
            )):
                print(f"\nHTTP {response.status}: {url}")

                if response.status == 403:
                    try:
                        body = await response.text()
                        print("403 response body:")
                        print(body[:4000])
                    except Exception as exc:
                        print("Could not read 403 body:", exc)

                elif "productorderinfo" in url.lower():
                    try:
                        print("Order metadata:")
                        print((await response.text())[:4000])
                    except Exception as exc:
                        print("Could not read metadata:", exc)

        page.on(
            "response",
            lambda response: asyncio.create_task(
                inspect_response(response)
            ),
        )

        try:
            print("Navigating to product:", MPN)
            response = await page.goto(
                f"{BASE_URL}/{MPN}/",
                wait_until="domcontentloaded",
            )

            print("Initial status:", response.status if response else None)
            print("Final URL:", page.url)
            print(
                "Browser user agent:",
                await page.evaluate("navigator.userAgent"),
            )

            # Allow the page's normal JavaScript requests to finish.
            await page.wait_for_timeout(5000)

            print("\nRendered page text:")
            print((await page.locator("body").inner_text())[:8000])

            await page.screenshot(
                path="mcmaster_investigation.png",
                full_page=True,
            )

            print("\nScreenshot saved: mcmaster_investigation.png")

        finally:
            await context.close()
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
