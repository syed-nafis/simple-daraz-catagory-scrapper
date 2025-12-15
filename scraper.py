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
CSV_FIELDNAMES = ['category_name', 'status', 'last_searched_date']

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

def update_or_create_csv(category_name, status, date_str):
    """
    Handles Feature #2: Checks if CSV exists.
    - If no: Creates it and adds the entry.
    - If yes: Appends new entry or updates existing one.
    """
    rows = []
    found = False

    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            if reader.fieldnames:
                for row in reader:
                    clean_row = {k.strip(): v.strip() for k, v in row.items()}
                    if clean_row.get('category_name', '').lower() == category_name.lower():
                        clean_row['status'] = status
                        clean_row['last_searched_date'] = date_str
                        found = True
                    rows.append(clean_row)

    if not found:
        rows.append({
            'category_name': category_name,
            'status': status,
            'last_searched_date': date_str
        })

    with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    
    action = "Updated" if found else "Created new"
    print(f"💾 CSV Record {action}: {category_name} | {status}")

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

def scrape_page_items(driver):
    """Helper to extract items from the current page view."""
    products = driver.find_elements(By.CSS_SELECTOR, "div[data-qa-locator='product-item']")
    page_results = []
    
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

        # --- FIX: BETTER IMAGE EXTRACTION ---
        try:
            img_element = product.find_element(By.CSS_SELECTOR, ".picture-wrapper img")
            img_url = img_element.get_attribute("src")
            
            # Check if it's a Base64 placeholder (usually starts with "data:image")
            if img_url and "data:image" in img_url:
                # Try to get the real URL from 'data-src' (common for lazy loading)
                real_url = img_element.get_attribute("data-src")
                if real_url:
                    img_url = real_url
                    
            # Normalize URL
            if img_url and img_url.startswith("//"):
                img_url = "https:" + img_url
                
        except: 
            img_url = ""

        # Only add valid items with names
        if item_name:
            page_results.append({
                "name": item_name, "price": item_price, "sku": sku,
                "link": link, "sold_text": sold_text, "sold_count": sold_count,
                "image": img_url
            })
            
    return page_results

def scrape_category(driver, query, save_dir):
    """
    Scrapes a single category (Page 1 & 2).
    Returns True if successful, False otherwise.
    """
    output_lines = []
    file_safe_query = re.sub(r'[\\/*?:"<>|]', "", query)
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
                search_status_indicator = "✅ Category Found (Official Category Page)"
            else:
                print(f"ℹ️ Category '{query}' not found in sidebar. Scraping search results directly.")
        else:
            print("ℹ️ Category sidebar not found. Scraping search results directly.")
    except Exception as e:
        print(f"⚠️ Minor error in category logic (continuing): {e}")

    # --- CAPTURE URL HERE ---
    current_page_url = driver.current_url

    # --- WRITE HEADER TO OUTPUT ---
    output_lines.append("=====================================================")
    output_lines.append(f"SEARCH TERM : {query}")
    output_lines.append(f"STATUS      : {search_status_indicator}")
    output_lines.append(f"URL         : {current_page_url}")
    output_lines.append("=====================================================\n")

    # 3. Scrape Product Cards (PAGE 1)
    print("📥 Scraping Page 1...")
    all_results = scrape_page_items(driver)
    
    if not all_results:
        log(f"⚠️ No products found for '{query}'. Marking as PENDING.", output_lines)
        return False 
    
    log(f"   -> Found {len(all_results)} items on Page 1.", output_lines)

    # 4. Scrape Product Cards (PAGE 2) - NEW LOGIC
    try:
        # Locating the '2' pagination button specifically
        page_two_btn = driver.find_elements(By.CSS_SELECTOR, "li[title='2'] a")
        
        if page_two_btn:
            print("➡️ Navigating to Page 2...")
            driver.execute_script("arguments[0].click();", page_two_btn[0])
            time.sleep(6) # Wait for load
            
            page_2_results = scrape_page_items(driver)
            log(f"   -> Found {len(page_2_results)} items on Page 2.", output_lines)
            
            all_results.extend(page_2_results)
        else:
            print("ℹ️ No Page 2 found (less than 40 results).")
            
    except Exception as e:
        print(f"⚠️ Error navigating to Page 2: {e}")

    # 5. Sort and Analyze (New Grouping Logic)
    if all_results:
        # Sort ALL results by sold count first
        sorted_results = sorted(all_results, key=lambda x: x["sold_count"], reverse=True)
        
        # --- NEW ALGORITHM: GROUPING WITHOUT OVERLAP ---
        grouped_groups = []
        
        # We use a set of indices to keep track of items already assigned to a group
        processed_indices = set()
        
        # Loop to find up to 10 groups
        for i in range(len(sorted_results)):
            if len(grouped_groups) >= 10:
                break
                
            if i in processed_indices:
                continue
            
            # This item becomes the "Top Seller" for this new group
            top_item = sorted_results[i]
            processed_indices.add(i)
            
            current_group = {
                "top": top_item,
                "similars": []
            }
            
            # Scan for similar items in the remainder of the list
            for j in range(i + 1, len(sorted_results)):
                if j in processed_indices:
                    continue
                
                candidate = sorted_results[j]
                score = fuzz.token_sort_ratio(top_item["name"], candidate["name"])
                
                if score >= 90:
                    current_group["similars"].append({
                        "item": candidate,
                        "score": score
                    })
                    processed_indices.add(j)
            
            grouped_groups.append(current_group)

        # --- WRITE REPORT ---
        log(f"\nAnalyzed {len(all_results)} total items. Found {len(grouped_groups)} distinct top-selling groups.\n", output_lines)

        for idx, group in enumerate(grouped_groups, 1):
            top = group["top"]
            log(f"🟦 GROUP #{idx} (Top Seller: {top['sold_count']} sold)", output_lines)
            log(f"   Name:  {top['name']}", output_lines)
            log(f"   Price: {top['price']} | SKU: {top['sku']}", output_lines)
            log(f"   Link:  {top['link']}", output_lines)
            log(f"   Image: {top['image']}", output_lines)
            
            if group["similars"]:
                log(f"   --- {len(group['similars'])} Similar Items (Non-Overlapping) ---", output_lines)
                for sim in group["similars"]:
                    item = sim["item"]
                    log(f"   • [{sim['score']}% Match] {item['name']}", output_lines)
                    log(f"     Price: {item['price']} | Sold: {item['sold_text']}", output_lines)
                    log(f"     Link:  {item['link']}", output_lines)
            else:
                log("   --- No similar items found in top results ---", output_lines)
            
            log("\n" + "-"*40 + "\n", output_lines)

        # Save File
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

    # Shared Resources
    today_str = datetime.now().strftime("%Y-%m-%d")
    today_dir = os.path.join(BASE_REPORT_DIR, today_str)
    os.makedirs(today_dir, exist_ok=True)
    
    options = Options()
    options.add_argument("--width=1200")
    options.add_argument("--height=900")
    options.add_argument("--headless") 

    # 1. Report Mode
    if args.generate_report:
        generate_report_mode(args.generate_report)

    # 2. Determine Mode
    is_batch_mode = args.next_items or args.retry_pending_categories

    if not is_batch_mode:
        # === INTERACTIVE MODE ===
        print("\n👋 Entering Interactive Mode")
        user_query = input("🔎 Please enter a search query: ").strip()
        
        if not user_query:
            print("❌ Empty query. Exiting.")
            return

        print("\n🔌 Starting Browser...")
        driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)
        
        try:
            driver.get("https://www.daraz.com.bd/")
            time.sleep(3)
            
            success = scrape_category(driver, user_query, today_dir)
            status = 'DONE' if success else 'PENDING'
            update_or_create_csv(user_query, status, today_str)
            
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            print("🔌 Closing Browser...")
            driver.quit()

    else:
        # === BATCH MODE ===
        if not os.path.exists(CSV_FILE):
            print(f"❌ Error: {CSV_FILE} not found! Run without arguments first to create one.")
            return

        categories = []
        with open(CSV_FILE, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                clean_row = {k.strip(): v.strip() for k, v in row.items()}
                categories.append(clean_row)

        target_indices = []
        pending_indices = [i for i, c in enumerate(categories) if c.get('status') == 'PENDING']
        new_indices = [i for i, c in enumerate(categories) if c.get('status') == '']

        if args.retry_pending_categories:
            print(f"🔄 Retrying {len(pending_indices)} PENDING categories...")
            target_indices = pending_indices

        elif args.next_items:
            final_indices = []
            if pending_indices:
                print(f"⚠️ Found {len(pending_indices)} categories marked as 'PENDING'.")
                user_input = input("❓ Do you want to retry these pending items first? (y/n): ").strip().lower()
                if user_input == 'y':
                    final_indices.extend(pending_indices)
            
            count_needed = args.next_items
            selected_new = new_indices[:count_needed]
            final_indices.extend(selected_new)
            target_indices = final_indices
            print(f"📌 Queued: {len(target_indices)} items")

        if not target_indices:
            print("🎉 No categories found to process!")
            return

        print("\n🔌 Starting Browser (Batch Mode)...")
        driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)

        try:
            driver.get("https://www.daraz.com.bd/")
            time.sleep(3)

            for list_idx in target_indices:
                cat_data = categories[list_idx]
                category_name = cat_data['category_name']
                
                try:
                    success = scrape_category(driver, category_name, today_dir)
                    
                    categories[list_idx]['last_searched_date'] = today_str
                    categories[list_idx]['status'] = 'DONE' if success else 'PENDING'
                    
                    if success: print(f"✅ {category_name} -> DONE")
                    else: print(f"⚠️ {category_name} -> PENDING")

                    with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
                        writer.writeheader()
                        writer.writerows(categories)

                except Exception as e:
                    print(f"❌ Critical error scraping '{category_name}': {e}")
                    categories[list_idx]['status'] = 'PENDING'
                    with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
                        writer.writeheader()
                        writer.writerows(categories)
                
                delay = random.randint(5, 10)
                print(f"⏳ Waiting {delay}s...")
                time.sleep(delay)

        finally:
            print("🔌 Closing Browser...")
            driver.quit()

if __name__ == "__main__":
    main()