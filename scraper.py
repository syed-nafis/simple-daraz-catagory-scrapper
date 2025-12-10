import argparse
import csv
import os
import time
import re
import random
import sys
from datetime import datetime
from rapidfuzz import fuzz

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager

# ------------------------- CONFIGURATION -------------------------------
CSV_FILE = "category_list.csv"
BASE_REPORT_DIR = "category_report"

# ------------------------- HELPER FUNCTIONS ---------------------------

def parse_sold_count(text):
    """Convert sold count text '2.4k sold' → 2400"""
    if not text:
        return 0
    text = text.lower().replace("sold", "").strip()

    if "k" in text:
        return int(float(text.replace("k", "")) * 1000)
    else:
        return int(re.sub(r"[^\d]", "", text)) if re.search(r"\d", text) else 0

def log(text, output_lines):
    """Helper to print to console and add to output list"""
    print(text)
    output_lines.append(text)

def generate_report_mode(mode):
    """Handles the --generate-report logic"""
    if not os.path.exists(CSV_FILE):
        print(f"❌ Error: {CSV_FILE} not found!")
        return

    print(f"\n📊 GENERATING REPORT: {mode.upper()}\n" + "="*40)
    
    with open(CSV_FILE, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            status = row.get('status', '').strip().upper()
            date = row.get('last_searched_date', '').strip()
            cat = row.get('category_name', '').strip()
            
            if mode == 'searched':
                if status == 'DONE':
                    print(f"✅ {cat} (Scraped on: {date})")
                    count += 1
            elif mode == 'pending':
                if status == 'PENDING':
                    print(f"⚠️  {cat} (Failed on: {date})")
                    count += 1
                elif status == '':
                    print(f"⚪ {cat} (New/Unsearched)")
                    count += 1
        
        print("="*40)
        print(f"Total items found: {count}")
    sys.exit(0) 

def scrape_category(driver, query, save_dir):
    """
    Scrapes a single category.
    Returns True if successful, False otherwise.
    """
    output_lines = []
    file_safe_query = re.sub(r'[\\/*?:"<>|]', "", query)
    
    # State tracking for the report header
    search_status_indicator = "❌ Category Not Found (Used General Search Results)"
    
    print(f"\n--- Starting search for: {query} ---")

    # 1. Search Interaction
    try:
        search_box = driver.find_element(By.ID, "q")
        search_box.clear()
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)
        time.sleep(5)
    except Exception as e:
        print(f"❌ Error interacting with search box: {e}")
        return False

    # 2. Category Filter Logic
    try:
        sidebars = driver.find_elements(By.CLASS_NAME, "gJ98q")
        category_sidebar = None
        for sb in sidebars:
            try:
                title_ele = sb.find_element(By.CLASS_NAME, "_9xWFp")
                if "Category" in title_ele.text:
                    category_sidebar = sb
                    break
            except: continue

        if category_sidebar:
            def get_matching_category(element, search_term):
                links = element.find_elements(By.CSS_SELECTOR, "a.DMfHy")
                for link in links:
                    if link.text.strip().lower() == search_term.lower():
                        return link
                return None

            match_link = get_matching_category(category_sidebar, query)
            if not match_link:
                try:
                    view_more = category_sidebar.find_element(By.CSS_SELECTOR, ".iSqXl")
                    if "VIEW MORE" in view_more.text.upper():
                        driver.execute_script("arguments[0].click();", view_more)
                        time.sleep(2)
                        match_link = get_matching_category(category_sidebar, query)
                except: pass

            if match_link:
                print(f"✅ Found Category matching '{query}'. Navigating...")
                driver.execute_script("arguments[0].click();", match_link)
                time.sleep(5)
                # Update status since we successfully clicked the category
                search_status_indicator = "✅ Category Found (Official Category Page)"
            else:
                print(f"ℹ️ Category '{query}' not found in sidebar. Scraping search results directly.")
        else:
            print("ℹ️ Category sidebar not found. Scraping search results directly.")
    except Exception as e:
        print(f"⚠️ Minor error in category logic (continuing): {e}")

    # --- CAPTURE URL HERE (After navigation is complete) ---
    current_page_url = driver.current_url

    # --- WRITE HEADER TO OUTPUT ---
    output_lines.append("=====================================================")
    output_lines.append(f"SEARCH TERM : {query}")
    output_lines.append(f"STATUS      : {search_status_indicator}")
    output_lines.append(f"URL         : {current_page_url}")
    output_lines.append("=====================================================\n")


    # 3. Scrape Product Cards
    products = driver.find_elements(By.CSS_SELECTOR, "div[data-qa-locator='product-item']")
    results = []

    if not products:
        log(f"⚠️ No products found for '{query}'. Marking as PENDING.", output_lines)
        return False 

    log(f"Found {len(products)} products for '{query}'. Processing...", output_lines)

    for product in products:
        try: item_name = product.find_element(By.CSS_SELECTOR, ".RfADt a").text.strip()
        except: item_name = ""
        try: item_price = product.find_element(By.CSS_SELECTOR, ".aBrP0 .ooOxS").text.strip()
        except: item_price = ""
        try: sku = product.get_attribute("data-sku-simple")
        except: sku = ""
        try: 
            link = product.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
            if link.startswith("//"): link = "https:" + link
        except: link = ""
        try: 
            sold_text = product.find_element(By.CSS_SELECTOR, "._1cEkb span").text
            sold_count = parse_sold_count(sold_text)
        except: sold_text = ""; sold_count = 0

        results.append({
            "name": item_name, "price": item_price, "sku": sku,
            "link": link, "sold_text": sold_text, "sold_count": sold_count
        })

    # 4. Sort and Analyze
    if results:
        sorted_results = sorted(results, key=lambda x: x["sold_count"], reverse=True)
        TOP_ITEM = sorted_results[0]
        
        similar_items = []
        for item in sorted_results:
            score = fuzz.token_sort_ratio(TOP_ITEM["name"], item["name"])
            if score >= 75:
                similar_items.append((score, item))
        similar_items.sort(reverse=True, key=lambda x: x[0])

        log("\n================= TOP SELLING ITEM =================\n", output_lines)
        log(f"Name:  {TOP_ITEM['name']}", output_lines)
        log(f"Price: {TOP_ITEM['price']}", output_lines)
        log(f"SKU:   {TOP_ITEM['sku']}", output_lines)
        log(f"Sold:  {TOP_ITEM['sold_text']} ({TOP_ITEM['sold_count']})", output_lines)
        log(f"Link: {TOP_ITEM['link']}", output_lines)
        log("\n=====================================================\n", output_lines)

        log("============= ITEMS SIMILAR TO TOP SELLING =============\n", output_lines)
        for score, item in similar_items:
            log(f"[Similarity {score}%] {item['name']}", output_lines)
            log(f"   Price: {item['price']}", output_lines)
            log(f"   SKU:   {item['sku']}", output_lines)
            log(f"   Sold:  {item['sold_text']} ({item['sold_count']})", output_lines)
            log(f"   Link:  {item['link']}", output_lines)
            log("\n", output_lines)

        log("\n================= ALL SORTED RESULTS =================\n", output_lines)
        for i, item in enumerate(sorted_results, start=1):
            log(f"{i}. {item['name']}", output_lines)
            log(f"   Price: {item['price']}", output_lines)
            log(f"   SKU:   {item['sku']}", output_lines)
            log(f"   Sold: {item['sold_text']} ({item['sold_count']})", output_lines)
            log(f"   Link: {item['link']}", output_lines)
            log("\n", output_lines)

        filename = f"{file_safe_query}.txt"
        full_path = os.path.join(save_dir, filename)
        
        with open(full_path, "w", encoding="utf-8") as f:
            f.write("\n".join(output_lines))
        
        print(f"✅ Report saved: {full_path}")
        return True
    
    return False

# ------------------------- MAIN EXECUTION ---------------------------

def main():
    parser = argparse.ArgumentParser(description="Daraz Category Scraper")
    
    # Arguments
    parser.add_argument("--next-items", type=int, help="Number of NEW categories to process")
    parser.add_argument("--retry-pending-categories", action="store_true", help="Retry all failed (PENDING) categories only")
    parser.add_argument("--generate-report", type=str, choices=['searched', 'pending'], help="Generate a simple text report")

    args = parser.parse_args()

    # 1. Handle Report Generation (Exits after printing)
    if args.generate_report:
        generate_report_mode(args.generate_report)

    # 2. Check for missing run arguments
    if not args.next_items and not args.retry_pending_categories:
        print("❌ Error: You must provide either '--next-items [N]' or '--retry-pending-categories'")
        return

    # 3. Load CSV
    if not os.path.exists(CSV_FILE):
        print(f"❌ Error: {CSV_FILE} not found!")
        return

    categories = []
    with open(CSV_FILE, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = [x.strip() for x in reader.fieldnames] 
        for row in reader:
            clean_row = {k.strip(): v.strip() for k, v in row.items()}
            categories.append(clean_row)

    # 4. Filter Targets based on logic
    targets = []        # List of category names
    target_indices = [] # Indices in the original list to update later
    
    # Identify lists
    pending_indices = [i for i, c in enumerate(categories) if c.get('status') == 'PENDING']
    new_indices = [i for i, c in enumerate(categories) if c.get('status') == '']

    if args.retry_pending_categories:
        # Retry ONLY pending
        print(f"🔄 Retrying {len(pending_indices)} PENDING categories...")
        target_indices = pending_indices

    elif args.next_items:
        # Logic: Check pending first
        final_indices = []
        
        if pending_indices:
            print(f"⚠️ Found {len(pending_indices)} categories marked as 'PENDING' (Failed previously).")
            user_input = input("❓ Do you want to retry these pending items first? (y/n): ").strip().lower()
            
            if user_input == 'y':
                print("👍 Adding pending items to the queue.")
                final_indices.extend(pending_indices)
            else:
                print("⏭️ Skipping pending items.")

        # Add new items (limit to N)
        count_needed = args.next_items
        selected_new = new_indices[:count_needed]
        final_indices.extend(selected_new)
        
        target_indices = final_indices
        print(f"📌 Queued: {len(target_indices)} items (Pending: {len(final_indices)-len(selected_new)} | New: {len(selected_new)})")

    if not target_indices:
        print("🎉 No categories found to process based on your criteria!")
        return

    # 5. Setup Directory & Browser
    today_str = datetime.now().strftime("%Y-%m-%d")
    today_dir = os.path.join(BASE_REPORT_DIR, today_str)
    os.makedirs(today_dir, exist_ok=True)
    
    options = Options()
    options.add_argument("--width=1200")
    options.add_argument("--height=900")
    options.add_argument("--headless") 
    
    print("\n🔌 Starting Browser...")
    driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)
    
    try:
        driver.get("https://www.daraz.com.bd/")
        time.sleep(3)

        # 6. Loop Loop Loop
        for list_idx in target_indices:
            cat_data = categories[list_idx]
            category_name = cat_data['category_name']
            
            try:
                success = scrape_category(driver, category_name, today_dir)
                
                # Update Memory & File
                categories[list_idx]['last_searched_date'] = today_str
                
                if success:
                    categories[list_idx]['status'] = 'DONE'
                    print(f"✅ Success: {category_name} marked as DONE.")
                else:
                    categories[list_idx]['status'] = 'PENDING'
                    print(f"⚠️ Failed: {category_name} marked as PENDING.")

                # Write to CSV immediately
                with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(categories)

            except Exception as e:
                print(f"❌ Critical error scraping '{category_name}': {e}")
                # Mark as PENDING on crash
                categories[list_idx]['status'] = 'PENDING'
                categories[list_idx]['last_searched_date'] = today_str
                
                with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(categories)
            
            # Delay between items
            delay = random.randint(5, 10)
            print(f"⏳ Waiting {delay}s...")
            time.sleep(delay)

    finally:
        print("🔌 Closing Browser...")
        driver.quit()

if __name__ == "__main__":
    main()