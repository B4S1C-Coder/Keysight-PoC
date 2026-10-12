
import asyncio
import json
import re
from urllib.parse import urlencode

from playwright.async_api import async_playwright

MPN = "91864A028"


def build_url(mpn: str) -> str:
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


def extract_json_with_react_data(text: str) -> dict:
    """Find and decode the JSON object containing ReactData."""
    decoder = json.JSONDecoder()

    # Skip any leading numeric prefix, then try each JSON object.
    for match in re.finditer(r"\{", text):
        try:
            obj, _ = decoder.raw_decode(text, match.start())
        except json.JSONDecodeError:
            continue

        if isinstance(obj, dict) and isinstance(obj.get("ReactData"), dict):
            return obj

    raise ValueError("Could not find a JSON object containing ReactData.")


async def main() -> None:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page(
            locale="en-US",
            viewport={"width": 1440, "height": 1000},
        )

        try:
            print(f"Fetching MPN: {MPN}")
            response = await page.goto(
                build_url(MPN),
                wait_until="domcontentloaded",
            )

            if response is None:
                raise RuntimeError("No HTTP response received.")

            print(f"HTTP status: {response.status}")

            if response.status != 200:
                print((await response.text())[:2000])
                return

            # Read the raw endpoint response, not rendered page text.
            text = (await response.body()).decode(
                "utf-8-sig",
                errors="replace",
            )

            product = extract_json_with_react_data(text)
            react_data = product["ReactData"]

            print("\n=== PRODUCT ===")
            print("MPN:", product.get("PartNbrTxt", MPN))
            print("Title:", product.get("TitleTxt", ""))

            headers = react_data.get("Headers", {})
            print("Primary:", headers.get("Primary", ""))
            print("Secondary:", headers.get("Secondary", ""))

            print("\n=== REQUIRED ATTRIBUTES ===")
            entries = react_data.get("TableEntries", [])
            wanted = {"material", "rohs compliance"}

            found = set()

            for entry in entries:
                name = entry.get("Name", "").strip()
                value = entry.get("Value", "").strip()

                if name.casefold() in wanted:
                    print(f"{name}: {value}")
                    found.add(name.casefold())

            for field in sorted(wanted - found):
                print(f"{field.title()}: NOT FOUND")

            print("\n=== ALL SPECIFICATIONS ===")
            for entry in entries:
                name = entry.get("Name", "").strip()
                value = entry.get("Value", "").strip()

                if name and value:
                    print(f"{name}: {value}")

            # Product descriptions may also contain material information.
            print("\n=== DESCRIPTION ===")
            for copy in react_data.get("Copies", []):
                clean_copy = re.sub(r"<[^>]+>", "", copy)
                clean_copy = re.sub(r"\s+", " ", clean_copy)
                print(clean_copy)

        finally:
            await page.close()
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
