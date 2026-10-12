from dotenv import load_dotenv
load_dotenv()

from pathlib import Path
from poc import (
    load_pdf,
    extract,
    detect_manufacturer,
    Manufacturer,
    ExtractionResult,
    write_xlsx,
)

DATA_DIR = Path("data")

COMPONENTS = [
    (DATA_DIR / "Component_Datasheet_1.pdf", "SBC50-4-14-2"),
    (DATA_DIR / "Component_Datasheet_2.pdf", "91864A002"),
]

def main():
    for pdf_path, mpn in COMPONENTS:
        print(f"\nProcessing {pdf_path.name}...")

        try:
            doc = load_pdf(pdf_path)
            set1, set2, warnings = extract(doc, mpn, use_vision=True)

            manufacturer = detect_manufacturer(doc)
            
            manufacturer_name = {
                Manufacturer.SemiGen: "SemiGen",
                Manufacturer.McMasterCarr: "McMaster-Carr",
            }.get(manufacturer, "UNKNOWN")

            result = ExtractionResult(
                mpn=mpn,
                manufacturer=manufacturer_name,
                source_pdf=pdf_path.name,
                set1=set1,
                set2=set2,
                warnings=warnings
            )

            output_path = write_xlsx(result, out_dir=DATA_DIR)
            print(f"Saved: {output_path}")

            if warnings:
                print("Warnings:")

                for warning in warnings:
                    print(f"  - {warning}")

        except Exception as exc:
            print(f"Failed to process {pdf_path.name}: {exc}")

if __name__ == "__main__":
    main()
