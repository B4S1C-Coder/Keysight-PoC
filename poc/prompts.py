import os

# Naming convention: <purpose>.<version>
prompts = {
    "dimension-extraction.v1": (
        "The attached datasheet has a package drawing for style {package}. Return the "
        "overall component dimensions: length, width (overall body width of the "
        "component, not the lead width) and height (thickness), each in inches and "
        "mm. Use `max_` only for dimensions labelled MAX, and `tolerance` for +/- "
        "values. Leave unknown fields null."
    ),
}

EXTRACTION_PROMPT_VERSION = os.environ.get("EXTRACTION_PROMPT_VERSION", "dimension-extraction.v1")

def get_extraction_prompt() -> str:
    try:
        return prompts[EXTRACTION_PROMPT_VERSION]
    except KeyError:
        raise KeyError(f"Specified EXTRACTION_PROMPT_VERSION not found.")