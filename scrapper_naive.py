import requests

def parse_sold_count(text):
    """
    Converts text like '83 sold' or '2.4k sold' into an integer.
    Returns 0 for N/A or invalid formats.
    """
    if not text or text == "N/A":
        return 0

    value = text.lower().replace("sold", "").strip()

    # Handle K (thousands)
    if "k" in value:
        try:
            return int(float(value.replace("k", "").strip()) * 1000)
        except:
            return 0

    # Normal integers
    try:
        return int(value)
    except:
        return 0

def scrape_daraz(search_term):
    url = "https://www.daraz.com.bd/catalog/"
    params = {
        "_keyori": "ss",
        "ajax": "true",
        "from": "input",
        "q": search_term
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "Accept": "application/json, text/plain, */*",
        "Referer": f"https://www.daraz.com.bd/catalog/?q={search_term}"
    }

    print(f"[+] Fetching: {url}/?q={search_term}\n")

    response = requests.get(url, params=params, headers=headers)

    # Debug: uncomment to inspect raw response if needed
    # print(response.text[:500])

    try:
        data = response.json()
    except Exception:
        print("[-] Failed to parse JSON. Server returned unexpected content.")
        return []

    # Extract product list
    items = data.get("mods", {}).get("listItems", [])

    print(f"[+] {len(items)} products found.\n")

    results = []
    for item in items:
        title = item.get("name", "N/A")
        price = item.get("priceShow") or item.get("price") or "N/A"
        sold = item.get("itemSoldCntShow", "N/A")

        # Convert sold text into a number
        sold_count = parse_sold_count(sold)


        # Product link (always missing https:)
        raw_link = item.get("itemUrl", "")
        product_url = "https:" + raw_link if raw_link.startswith("//") else raw_link

        image_url = item.get("image", "N/A")
        sku = item.get("skuId", "N/A")

        results.append({
            "title": title,
            "price": price,
            "sold_count": sold_count,
            "url": product_url,
            "image": image_url,
            "sku": sku
        })
    
    # Sort by numeric sold count (highest first)
    results.sort(key=lambda x: x["sold_count"], reverse=True)

    return results


if __name__ == "__main__":
    search_term = input("Search term: ")
    products = scrape_daraz(search_term)

    for p in products:
        print(p)
        print("-" * 40)

    
