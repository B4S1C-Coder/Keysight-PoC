# Keysight PoC
This repository contains the solution for Keysight Technologies PoC for campus hiring 2027. Both cases Case-1 and Case-2 have been covered here. A brief about both the cases:

- Case-1: It involves extracting Component Specifications via `pdfplumber` and uses `Gemini-3-Flash-Preview` for extracting dimensions from component engineering drawings (CAD diagrams) from the provided datasheets.

- Case-2: It involves searching the provided `MPN` numbers on `mcnmaster`, and fetching the `material` and `RoHS Compliance` status.

# Setup & Running
## Setup
The following needs to be done only the first time project is setup.

1. Clone  the repo
```bash
git clone https://github.com/B4S1C-Coder/Keysight-PoC
```

2. Install dependencies
```bash
uv sync
```

3. Install playwright (chromium)
```bash
uv run playwright install chromium
```

4. Setup .env file and fill in all the required variables.
```bash
cp .env.example .env
```

>**Note**: Do not forget to fill in the .env above. You can obtain Gemini API key for free from Google AI Studio. The project can still be used without the LLM as well, but it'll only be able to handle packages whose dimensions have already been extracted, those packages are defined in [poc/package_dimensions.json](./poc/package_dimensions.json).

## Running
### Case-1
To run case-1:
```bash
uv run python case1.py
```

Results are available in [data/](./data/).

### Case-2
To run case-2:
```bash
uv run python case2.py
```
Results are available in [data/](./data/).

### Additional
This stuff is optional and mostly there for sanity checks. You can skip this entirely if you only want to run the project.

#### Connectivity with Gemini
Check initial connectivity after project and environment setup (env vars are set) via:

```bash
uv run pytest tests/test_vision_live_self_contained.py -m live -v -s
```

#### Creating a fresh input xlsx for Case-2
To create a fresh input `.xlsx` file for case-2 use:

```bash
uv run python scripts/create_table_a.py
```

The input file would be create in [data/](./data/) directory and would automatically be picked up by [case2.py](./case2.py).

#### Exporting results if running in WSL2
If you have are in WSL2 like me, then you might want to export the `.xlsx` files in [data/](./data/) in order to view them. A convenience script is provided:

1. Give the script executable permissions (only first time):
  ```bash
  chmod +x scripts/export_results.sh
  ```

2. Then whenever you need to send the .xlsx files over to windows use:
  ```bash
  ./scripts/export_results.sh
  ```

>**Note**: Make sure to edit your windows username in the script before running it and adjust the destination suitable to you.

# Assumptions & Constraints
This solution is subject to the following and assumptions and constraints:

1. **Component Datasheet Format**: Since the solution uses a deterministic pipeline to extract Attribute Sets-1 and Attribute Sets-2, any changes to the general format of the two datasheets can cause the functionality to break. Hence, the formats of the documents must remain same.

2. **Dimension Extraction via LLM**: Since the dimensions of the components are mentioned in the diagram of the component itself, which is an image and has no text layer, standard pdf parsing pipelines and OCR would not be reliable. Hence, LLMs are used for this step and the result is cached.

3. **MCN Master Policy**: The case-2 of the PoC explicitly states to search on `mcnmaster.com`, whose policies prohibit web scraping and running bots on the website (via Playwright etc.). Their API requires special approval and certificates which is beyond the scope of PoC. Hence, on inspection of network tab, an intermediate `.asp` page is fetched directly to fetch the product details.

The exact requirement of Case-2 violates the policies of `mcnmaster.com` as a result the above mentioned workaround has been implemented.