import json
from urllib.parse import urlencode
from playwright.sync_api import sync_playwright

BASE_URL = (
    "https://www.mcmaster.com/"
    "mv1791657140/WebParts/Navigate/ItmPrsnttnWebPart.aspx"
)

REQUIRED_ATTRIBUTES = {"material", "rohs compliance"}


def build_product_url(mpn: str) -> str:
    """Build the McMaster product-detail URL for an MPN."""
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
            [
                {
                    "type": "ORDERINGMASTERPARTNUMBER",
                    "selectionType": "SELECTION",
                    "values": {
                        "entities": mpn,
                        "preselectedComponentPartNumber": "",
                    },
                }
            ],
            separators=(",", ":"),
        ),
        "screenDensity": "1.25",
        "useEs6": "true",
        "features": (
            "enableetorightclick,enablepresentationcrumb,"
            "enablerewriteetoeventchain,rtrvcadviarps,"
            "showaionpd,sortsequencedpfattributevaluesfirst,"
            "enablebreadcrumbs"
        ),
    }
    return f"{BASE_URL}?{urlencode(params)}"

def extract_react_data(response_text: str) -> dict:
    """ Find JSON object containing product data """
    decoder = json.JSONDecoder()

    for index, char in enumerate(response_text):
        if char != "{":
            continue

        try:
            data, _ = decoder.raw_decode(response_text, index)
        except json.JSONDecodeError:
            continue

        if isinstance(data, dict):
            react_data = data.get("ReactData")

            if isinstance(react_data, dict):
                return react_data

    raise ValueError("Could not find product data in response.")

def fetch_attributes(page, mpn: str) -> dict[str, str]:
    """ Find material and rohs compliance. """
    response = page.goto(
        build_product_url(mpn),
        wait_until="domcontentloaded",
        timeout=60_000
    )

    if response is None or response.status != 200:
        status = response.status if response else "no response"
        raise RuntimeError(f"received HTTP {status} for {mpn}")

    response_text = page.locator("body").inner_text()
    react_data = extract_react_data(response_text)

    attributes = {
        entry["Name"].strip().casefold(): entry["Value"].strip()
        for entry in react_data.get("TableEntries", [])
        if entry.get("Name", "").strip().casefold()
        in REQUIRED_ATTRIBUTES
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

