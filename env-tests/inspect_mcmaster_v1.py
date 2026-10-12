
import asyncio
import os

from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()

EMAIL = os.environ["MCMASTER_EMAIL"]
PASSWORD = os.environ["MCMASTER_PASSWORD"]


async def main():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        page.set_default_timeout(10_000)

        await page.goto(
            "https://www.mcmaster.com/",
            wait_until="domcontentloaded",
        )
        await page.wait_for_timeout(3000)

        print("Home URL:", page.url)

        # The screenshot shows Log in at the top-right.
        login = page.get_by_text("Log in", exact=True).last
        print("Login matches:", await login.count())

        await login.click()
        await page.wait_for_timeout(1500)

        print("After clicking login:", page.url)
        print("Visible dialogs:", await page.locator(
            '[role="dialog"]'
        ).count())

        print("Visible inputs:", await page.locator(
            "input:visible"
        ).evaluate_all("""
            els => els.map(e => ({
                name: e.name,
                type: e.type,
                placeholder: e.placeholder,
                ariaLabel: e.getAttribute('aria-label')
            }))
        """))

        print("Page text after login click:")
        print((await page.locator("body").inner_text())[:5000])

        # Find the actual email field, if one is present.
        email_field = page.locator(
            'input[type="email"]:visible, '
            'input[autocomplete="email"]:visible'
        ).first

        if await email_field.count() == 0:
            print(
                "\nNo email field found yet. Inspect the browser "
                "and complete any intermediate login step manually."
            )
            await asyncio.to_thread(
                input, "Press Enter when ready to continue..."
            )
        else:
            await email_field.fill(EMAIL)

        # Re-evaluate because the login flow may have changed.
        password_field = page.locator(
            'input[type="password"]:visible'
        ).first

        if await password_field.count():
            await password_field.fill(PASSWORD)
            print(
                "\nPassword filled. Inspect the page and submit "
                "the form manually if needed."
            )
        else:
            print("Password field not present on this step.")

        await asyncio.to_thread(
            input, "Finish login in the browser, then press Enter..."
        )

        print("\nURL after login:", page.url)
        print("Page text:")
        print((await page.locator("body").inner_text())[:5000])

        await page.screenshot(
            path="mcmaster_login_result.png",
            full_page=True,
        )

        # Save only after you have confirmed successful authentication.
        await context.storage_state(path="mcmaster_session.json")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
