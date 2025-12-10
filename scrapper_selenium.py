from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
import time
import re

from rapidfuzz import fuzz


def parse_sold_count(text):
    """Convert sold count text '2.4k sold' → 2400"""
    if not text:
        return 0
    text = text.lower().replace("sold", "").strip()

    if "k" in text:
        return int(float(text.replace("k", "")) * 1000)
    else:
        return int(re.sub(r"[^\d]", "", text)) if re.search(r"\d", text) else 0


# ------------------------- Selenium Setup ------------------------------
options = Options()
options.add_argument("--width=1200")
options.add_argument("--height=900")
options.add_argument("--headless") # Commented out so you can see the category click happen

driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)

driver.get("https://www.daraz.com.bd/")
time.sleep(3)

# ------------------------- Search Input -------------------------------
query = input("Enter product search query: ")

# sanitize filename
file_safe_query = re.sub(r'[\\/*?:"<>|]', "", query)

search_box = driver.find_element(By.ID, "q")
search_box.clear()
search_box.send_keys(query)
search_box.send_keys(Keys.RETURN)

print("Searching...")
time.sleep(5)


# ------------------------- Category Filter Logic -----------------------
# New functionality: Check sidebar for category matching the search query
try:
    print("Checking Category Sidebar...")
    
    # 1. Find the specific "Category" sidebar widget
    # There are multiple widgets with class 'gJ98q', we need the one titled "Category"
    sidebars = driver.find_elements(By.CLASS_NAME, "gJ98q")
    category_sidebar = None
    
    for sb in sidebars:
        try:
            # Check the title of the widget
            title_ele = sb.find_element(By.CLASS_NAME, "_9xWFp")
            if "Category" in title_ele.text:
                category_sidebar = sb
                break
        except:
            continue

    if category_sidebar:
        # Helper function to look for link in the sidebar element
        def get_matching_category(element, search_term):
            links = element.find_elements(By.CSS_SELECTOR, "a.DMfHy")
            for link in links:
                if link.text.strip().lower() == search_term.lower():
                    return link
            return None

        # 2. Check visible categories first
        match_link = get_matching_category(category_sidebar, query)

        # 3. If not found, look for "VIEW MORE" and expand
        if not match_link:
            try:
                # The 'View More' button usually has class 'iSqXl'
                view_more = category_sidebar.find_element(By.CSS_SELECTOR, ".iSqXl")
                if "VIEW MORE" in view_more.text.upper():
                    print("Category not found in top list. Clicking 'VIEW MORE'...")
                    # Javascript click is often more reliable for these overlay elements
                    driver.execute_script("arguments[0].click();", view_more)
                    time.sleep(2) # Wait for list to expand
                    
                    # Check again in the expanded list
                    match_link = get_matching_category(category_sidebar, query)
            except:
                # View more button might not exist if list is short
                pass

        # 4. Action: Click if found, or stay if not
        if match_link:
            print(f"✅ Found Category matching '{query}'. Navigating to category page...")
            driver.execute_script("arguments[0].click();", match_link)
            time.sleep(5) # Wait for the new category page to load
        else:
            print(f"❌ Category '{query}' not found. Scraping current search results.")

    else:
        print("Category sidebar not found. Proceeding with search page.")

except Exception as e:
    print(f"⚠️ Error in category logic: {e}")
    print("Proceeding to scrape current page...")


# ------------------------- Scrape Product Cards ------------------------
products = driver.find_elements(By.CSS_SELECTOR, "div[data-qa-locator='product-item']")

results = []
output_lines = []   # collect all printed lines


def log(text):
    """Print AND store in output"""
    print(text)
    output_lines.append(text)


if not products:
    log("No products found. (Page might not have loaded or check selectors)")
else:
    log(f"Found {len(products)} products. Processing...")

for product in products:
    try:
        item_name = product.find_element(By.CSS_SELECTOR, ".RfADt a").text.strip()
    except:
        item_name = ""

    try:
        item_price = product.find_element(By.CSS_SELECTOR, ".aBrP0 .ooOxS").text.strip()
    except:
        item_price = ""

    try:
        sku = product.get_attribute("data-sku-simple")
    except:
        sku = ""

    try:
        link = product.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
        if link.startswith("//"):
            link = "https:" + link
    except:
        link = ""

    try:
        sold_text = product.find_element(By.CSS_SELECTOR, "._1cEkb span").text
        sold_count = parse_sold_count(sold_text)
    except:
        sold_text = ""
        sold_count = 0

    results.append({
        "name": item_name,
        "price": item_price,
        "sku": sku,
        "link": link,
        "sold_text": sold_text,
        "sold_count": sold_count
    })


# ------------------------- Sort by Sold Count ---------------------------
# Check if we have results before processing
if results:
    sorted_results = sorted(results, key=lambda x: x["sold_count"], reverse=True)


    # ----------------------- FUZZY MATCH GROUP ------------------------------

    TOP_ITEM = sorted_results[0]
    top_name = TOP_ITEM["name"]

    similar_items = []
    THRESHOLD = 75

    for item in sorted_results:
        score = fuzz.token_sort_ratio(top_name, item["name"])
        if score >= THRESHOLD:
            similar_items.append((score, item))

    similar_items.sort(reverse=True, key=lambda x: x[0])


    # ------------------------- Display Results -----------------------------

    log("\n================= TOP SELLING ITEM =================\n")
    log(f"Name:  {TOP_ITEM['name']}")
    log(f"Price: {TOP_ITEM['price']}")
    log(f"SKU: {TOP_ITEM['sku']}")
    log(f"Sold:  {TOP_ITEM['sold_text']} ({TOP_ITEM['sold_count']})")
    log(f"Link: {TOP_ITEM['link']}")
    log("\n=====================================================\n")

    log("============= ITEMS SIMILAR TO TOP SELLING =============\n")

    for score, item in similar_items:
        log(f"[Similarity {score}%] {item['name']}")
        log(f"   Price: {item['price']}")
        log(f"   Sold:  {item['sold_text']} ({item['sold_count']})")
        log(f"   Link:  {item['link']}")
        #log("--------------------------------------------------------")
        log("\n")


    # ----------------------- FULL SORTED PRODUCT LIST -----------------------

    log("\n================= ALL SORTED RESULTS =================\n")

    for i, item in enumerate(sorted_results, start=1):
        log(f"{i}. {item['name']}")
        log(f"   Price: {item['price']}")
        log(f"   SKU: {item['sku']}")
        log(f"   Sold: {item['sold_text']} ({item['sold_count']})")
        log(f"   Link: {item['link']}")
        #log("----------------------------------------------------")
        log("\n")

else:
    log("No results to sort or display.")

driver.quit()


# ------------------------- SAVE OUTPUT TO TEXT FILE -------------------------

filename = f"{file_safe_query}.txt"

with open(filename, "w", encoding="utf-8") as f:
    f.write("\n".join(output_lines))

print(f"\n\n✅ Output saved to: {filename}")