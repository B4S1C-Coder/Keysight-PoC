
import json
import re
from urllib.parse import urlencode

from playwright.sync_api import sync_playwright


BASE_URL = (
    "https://www.mcmaster.com/"
    "mv1791657140/WebParts/Navigate/ItmPrsnttnWebPart.aspx"
)

REQUIRED_ATTRIBUTES = {"material", "rohs compliance"}


def build_product_url(mpn: str) -> str:
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
    return f"{BASE_URL}?{urlencode(params)}"


def extract_react_data(response_text: str) -> dict:
    decoder = json.JSONDecoder()

    for match in re.finditer(r"\{", response_text):
        try:
            data, _ = decoder.raw_decode(response_text, match.start())
        except json.JSONDecodeError:
            continue

        if isinstance(data, dict) and isinstance(data.get("ReactData"), dict):
            return data["ReactData"]

    raise ValueError("Could not find product data in response.")


def fetch_attributes(page, mpn: str) -> dict[str, str]:
    response = page.goto(
        build_product_url(mpn),
        wait_until="domcontentloaded",
        timeout=60_000,
    )

    if response is None or response.status != 200:
        status = response.status if response else "no response"
        raise RuntimeError(f"McMaster returned HTTP {status} for {mpn}")

    # IMPORTANT: parse the raw endpoint response, not rendered page text.
    response_text = (page.locator("body").evaluate(
        "(element) => element.innerText"
    ) if False else None)

    response_text = response.body().decode(
        "utf-8-sig",
        errors="replace",
    )

    react_data = extract_react_data(response_text)

    attributes = {
        entry["Name"].strip().casefold(): entry["Value"].strip()
        for entry in react_data.get("TableEntries", [])
        if entry.get("Name", "").strip().casefold() in REQUIRED_ATTRIBUTES
    }

    missing = REQUIRED_ATTRIBUTES - attributes.keys()
    if missing:
        raise ValueError(
            f"Missing attributes for {mpn}: {', '.join(sorted(missing))}"
        )

    return {
        "Material": attributes["material"],
        "RoHS Compliance": attributes["rohs compliance"],
    }
