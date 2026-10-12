
import asyncio
import json
from pathlib import Path

from playwright.async_api import async_playwright

MPN = "91864A028"
OUTPUT = Path("mcmaster_direct_response.html")


def build_url(mpn: str) -> str:
    from urllib.parse import urlencode
    import json

    params = {
        "partnbrtxt": mpn,
        "componentpartnbrtxt": "",
        "possiblecompnbrtxt": "",
        "attrcompitmids": "",
        "attrnm": "",
        "attrval": "",
        "cntnridtxt": "MainContent",
        "proddtllnkclickedInd": "false",
        "printprsnttnInd": "false",
        "cssAlias": "undefined",
        "clientNavigationEvents": json.dumps(
            [{
                "type": "ORDERINGMASTERPARTNUMBER",
                "selectionType": "SELECTION",
                "values": {
                    "entities": mpn,
                    "preselectedComponentPartNumber": "",
                },
            }],
            separators=(",", ":"),
        ),
        "screenDensity": "1.25",
        "useEs6": "true",
        "features": (
            "enableetorightclick,enablepresentationcrumb,"
            "enablerewriteetoeventchain,rtrvcadviarps,showaionpd,"
            "sortsequencedpfattributevaluesfirst,enablebreadcrumbs"
        ),
    }

    return (
        "https://www.mcmaster.com/mv1791657140/"
        "WebParts/Navigate/ItmPrsnttnWebPart.aspx?"
        + urlencode(params)
    )


async def main() -> None:
    url = build_url(MPN)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            locale="en-US",
            viewport={"width": 1440, "height": 1000},
        )
        page = await context.new_page()

        try:
            print("MPN:", MPN)
            print("URL:", url)

            response = await page.goto(
                url,
                wait_until="domcontentloaded",
            )

            print("\nHTTP status:",
                  response.status if response else "No response")
            print("Final URL:", page.url)
            print("Content type:",
                  response.headers.get("content-type")
                  if response else "Unknown")

            # Save the actual response body for inspection.
            if response:
                body = await response.body()
                OUTPUT.write_bytes(body)
                print("Response saved to:", OUTPUT.resolve())
                print("Response size:", len(body), "bytes")

            print("\nRendered text:")
            print((await page.locator("body").inner_text())[:8000])

            print("\nPage title:", await page.title())

            await page.screenshot(
                path="mcmaster_direct_result.png",
                full_page=True,
            )

            if response and response.status == 200:
                print(
                    "\nSUCCESS: HTTP 200. Inspect the saved response "
                    "to see whether it contains the required attributes."
                )
            elif response and response.status == 403:
                print(
                    "\nHTTP 403: direct navigation is still denied "
                    "in this browser context."
                )

            await asyncio.to_thread(
                input, "\nPress Enter to close the browser..."
            )

        finally:
            await context.close()
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
