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
options.add_argument("--headless")

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

time.sleep(5)


# ------------------------- Scrape Product Cards ------------------------
products = driver.find_elements(By.CSS_SELECTOR, "div[data-qa-locator='product-item']")

results = []
output_lines = []   # collect all printed lines


def log(text):
    """Print AND store in output"""
    print(text)
    output_lines.append(text)


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
log(f"SKU: {item['sku']}")
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


driver.quit()


# ------------------------- SAVE OUTPUT TO TEXT FILE -------------------------

filename = f"{file_safe_query}.txt"

with open(filename, "w", encoding="utf-8") as f:
    f.write("\n".join(output_lines))

print(f"\n\n✅ Output saved to: {filename}")
