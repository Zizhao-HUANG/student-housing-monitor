import asyncio
import re
from playwright.async_api import async_playwright
from datetime import datetime

async def check_lokaviz(url: str, residence_name: str = "Lokaviz") -> dict:
    """
    Checks Lokaviz for new listings posted today.
    """
    result = {
        "name": "Lokaviz",
        "residence_name": residence_name,
        "url": url,
        "status": "暂无房源",
        "details": "今天没有发布新的房源。"
    }
    today_str = datetime.now().strftime('%d/%m/%Y')

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(url, timeout=60000)
            await page.wait_for_load_state('networkidle', timeout=20000)

            listings = await page.locator(".liste-logements > ul > li").all()

            today_listings_count = 0
            details_list = []
            found_dates = []

            for listing in listings:
                date_text_element = await listing.query_selector(".logement-parution")
                if date_text_element:
                    date_text = (await date_text_element.inner_text()).strip()
                    # A more robust regex to find the date
                    match = re.search(r'(\d{2}/\d{2}/\d{4})', date_text)
                    if match:
                        found_date = match.group(1)
                        if len(found_dates) < 5: # Store first 5 dates for debugging
                            found_dates.append(found_date)

                        if found_date == today_str:
                            today_listings_count += 1

                            ref_element = await listing.query_selector(".logement-ref")
                            ref = (await ref_element.inner_text()).strip() if ref_element else "N/A"

                            title_element = await listing.query_selector(".logement-titre a")
                            title = (await title_element.inner_text()).strip() if title_element else "N/A"

                            price_element = await listing.query_selector(".loyer-valeur")
                            price = (await price_element.inner_text()).strip() if price_element else "N/A"

                            details_list.append(f"- {ref}: {title} ({price})")

            if today_listings_count > 0:
                result["status"] = "有空房"
                result["details"] = f"今天有 {today_listings_count} 个新房源:\n" + "\n".join(details_list)
            else:
                details = f"在 {len(listings)} 个房源中, 没有找到今天 ({today_str}) 发布的。"
                if found_dates:
                    # Use set to show unique dates, which is more informative
                    unique_dates = sorted(list(set(found_dates)), reverse=True)
                    details += "\n找到的最近日期: " + ", ".join(unique_dates)
                result["details"] = details

            await browser.close()
    except Exception as e:
        result["status"] = "检查失败"
        result["details"] = f"抓取时发生错误: {str(e)}"

    return result

async def check_adele(url: str, residence_name: str = "Adele") -> dict:
    """
    Checks the Adele website for availability by looking for content in the availabilities section.
    This function is more resilient to slow loading and UI changes.
    """
    result = {
        "name": "Adele",
        "residence_name": residence_name,
        "url": url,
        "status": "状态未知",
        "details": "未能明确判断房源状态。"
    }
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            # Go to the page and wait for it to be reasonably loaded.
            await page.goto(url, timeout=90000)
            await page.wait_for_load_state('networkidle', timeout=30000)

            availabilities_container_selector = "div#availabilities"
            availability_container = page.locator(availabilities_container_selector)

            # Wait for up to 10 seconds for the availability container to be attached to the DOM.
            try:
                await availability_container.wait_for(timeout=10000)
            except Exception:
                # This is not a critical error, the container might just not be there.
                pass

            if await availability_container.is_visible():
                apartment_selector = f"{availabilities_container_selector} > div[class^='bloc']"
                apartments = await page.locator(apartment_selector).all()

                if len(apartments) > 0:
                    result["status"] = "有空房"
                    result["details"] = f"找到了 {len(apartments)} 个可用的房源。"
                else:
                    result["status"] = "暂无房源"
                    result["details"] = "可用性区域为空，可能表示没有可用房源。"
            else:
                # If the availability section isn't visible, check the body for keywords.
                body_text = await page.locator("body").inner_text()
                if "aucun logement disponible" in body_text.lower() or "residence is already full" in body_text.lower():
                     result["status"] = "暂无房源"
                     result["details"] = "页面提示目前没有可用的房源。"
                else:
                     result["status"] = "状态未知"
                     result["details"] = "在可用性区域未找到房源，也没有明确的“已满”消息。请手动检查。"

            await browser.close()
    except Exception as e:
        # Catch timeout errors during page load and other general errors.
        if "Timeout" in str(e):
            result["status"] = "检查失败"
            result["details"] = f"页面加载超时或关键资源未能在规定时间内加载. 错误: {str(e)}"
        else:
            result["status"] = "检查失败"
            result["details"] = f"抓取时发生未知错误: {str(e)}"

    return result

async def check_crous(url: str, residence_name: str = "CROUS") -> dict:
    """
    Checks the CROUS website for listings in Strasbourg.
    """
    result = {
        "name": "CROUS",
        "residence_name": residence_name,
        "url": url,
        "status": "暂无房源",
        "details": "未在默认列表中找到斯特拉斯堡 (Strasbourg) 的房源。"
    }
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.set_viewport_size({"width": 1920, "height": 1080})

            await page.goto(url, timeout=60000)
            await page.wait_for_load_state('networkidle', timeout=20000)

            body_text = await page.locator("body").inner_text()

            if "strasbourg" in body_text.lower():
                result["status"] = "有空房"
                result["details"] = "在列表中找到了位于斯特拉斯堡 (Strasbourg) 的房源！"

            await browser.close()
    except Exception as e:
        result["status"] = "检查失败"
        result["details"] = f"抓取时发生错误: {str(e)}"

    return result

async def check_estudines(url: str, residence_name: str = "Les Estudines") -> dict:
    """
    Checks the Les Estudines website for availability.
    """
    result = {
        "name": "Les Estudines",
        "residence_name": residence_name,
        "url": url,
        "status": "状态未知",
        "details": "未能明确判断房源状态。"
    }
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(url, timeout=60000)
            await page.wait_for_load_state('networkidle', timeout=20000)

            body_text = await page.locator("body").inner_text()

            if "The residence is already full" in body_text:
                result["status"] = "暂无房源"
                result["details"] = "页面明确提示“The residence is already full”."
            elif "Pre-Book" in body_text or "Pre-book accommodation" in body_text:
                result["status"] = "有空房"
                result["details"] = "页面上存在“Pre-Book”或“Pre-book accommodation”按钮。"

            await browser.close()
    except Exception as e:
        result["status"] = "检查失败"
        result["details"] = f"抓取时发生错误: {str(e)}"

    return result

async def check_nexity(url: str, residence_name: str = "Nexity Studéa") -> dict:
    """
    This site is protected by strong anti-bot measures (CloudFront).
    Scraping is not feasible with the current tools.
    """
    return {
        "name": "Nexity Studéa",
        "residence_name": residence_name,
        "url": url,
        "status": "检查失败",
        "details": "该网站受CloudFront高级反机器人技术保护，无法进行抓取。"
    }

async def check_nemea(url: str, residence_name: str = "Nemea Appart'Etud") -> dict:
    """
    Checks the Nemea Appart'Etud website for availability.
    """
    result = {
        "name": "Nemea Appart'Etud",
        "residence_name": residence_name,
        "url": url,
        "status": "有空房", # Assume available unless proven otherwise
        "details": "未找到“Disponibilité non garantie”字样，可能存在房源。"
    }
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(url, timeout=60000)
            await page.wait_for_load_state('networkidle', timeout=20000)

            body_text = await page.locator("body").inner_text()

            if "Disponibilité non garantie" in body_text:
                result["status"] = "暂无房源"
                result["details"] = "页面明确提示“Disponibilité non garantie”."

            await browser.close()
    except Exception as e:
        result["status"] = "检查失败"
        result["details"] = f"抓取时发生错误: {str(e)}"

    return result

if __name__ == '__main__':
    pass
