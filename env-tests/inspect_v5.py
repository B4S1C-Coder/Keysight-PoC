
import asyncio
import json
from pathlib import Path
from urllib.parse import urlencode

from playwright.async_api import async_playwright

MPN = "91864A028"
OUTPUT = Path("mcmaster_direct_response.html")


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


def find_matching_fields(data, terms=("material", "rohs", "compliance")):
    """Find matching keys or values recursively in nested JSON."""
    matches = []

    def walk(value, path="$"):
        if isinstance(value, dict):
            for key, child in value.items():
                child_path = f"{path}.{key}"

                if any(term in str(key).lower() for term in terms):
                    matches.append((child_path, child))

                walk(child, child_path)

        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, f"{path}[{index}]")

    walk(data)
    return matches


async def main() -> None:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            locale="en-US",
            viewport={"width": 1440, "height": 1000},
        )
        page = await context.new_page()

        try:
            url = build_url(MPN)
            print(f"Fetching product details for {MPN}...")

            response = await page.goto(
                url,
                wait_until="domcontentloaded",
            )

            if response is None:
                raise RuntimeError("No HTTP response received.")

            print(f"HTTP status: {response.status}")

            if response.status != 200:
                print("Response was not successful.")
                print((await response.text())[:2000])
                return

            raw_body = await response.body()
            OUTPUT.write_bytes(raw_body)

            # The endpoint body starts with a numeric prefix before JSON.
            text = raw_body.decode("utf-8-sig", errors="replace").strip()
            json_start = text.find("{")

            if json_start == -1:
                raise ValueError("No JSON object found in response.")

            data = json.loads(text[json_start:])

            print("\n=== PRODUCT ===")
            print("MPN:", data.get("PartNbrTxt", MPN))
            print("Title:", data.get("TitleTxt", "Not found"))

            react_data = data.get("ReactData") or {}
            headers = react_data.get("Headers") or {}

            print("Primary description:", headers.get("Primary", "Not found"))
            print("Secondary description:", headers.get("Secondary", "Not found"))

            print("\n=== SPECIFICATION TABLE ===")
            entries = react_data.get("TableEntries") or []

            for entry in entries:
                if not isinstance(entry, dict):
                    continue

                name = entry.get("Name", "")
                value = entry.get("Value", "")

                if name or value:
                    print(f"{name}: {value or '(no value)'}")

            print("\n=== MATERIAL / ROHS / COMPLIANCE MATCHES ===")
            matches = find_matching_fields(data)

            if not matches:
                print("No matching field names found in this response.")
            else:
                for path, value in matches:
                    print(f"{path}: {json.dumps(value, ensure_ascii=False)}")

            print(f"\nRaw response saved to: {OUTPUT.resolve()}")

        finally:
            await context.close()
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
