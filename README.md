# 🛒 Daraz Product Scraper with Fuzzy Matching

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![Selenium](https://img.shields.io/badge/Selenium-4.0%2B-43B02A?style=for-the-badge&logo=selenium&logoColor=white)
![Firefox](https://img.shields.io/badge/Firefox-Headless-orange?style=for-the-badge&logo=firefox-browser&logoColor=white)

A specialized web scraper that extracts product listings from **Daraz.com.bd**, sorts them by sales volume, and utilizes fuzzy logic to identify and group the most relevant products.

This tool is designed to cut through the noise of e-commerce listings by identifying the **true top-selling item** and grouping similar variations using [RapidFuzz](https://github.com/maxbachmann/RapidFuzz).

---

## 🚀 Features

* **Automated Extraction:** Scrapes product name, price, sold count, SKU, and direct links.

### 🔁 Progress Tracking
Your input CSV tracks:
- `status` (DONE / PENDING)
- `last_searched_date` (auto‑updated)

The scraper resumes incomplete runs automatically.

### 🎯 Fuzzy Matching (rapidfuzz)
Ensures accurate mapping even when Google wording differs from input category names.

* **Auto-Save:** Exports all data immediately to a local text file named after your query.

---

## 🛠️ Built With

* **Python** - Core logic
* **Selenium** - Web automation and scraping
* **RapidFuzz** - String matching and similarity scoring
* **Webdriver Manager** - Automated driver management (Firefox)

---

## 📦 Installation

Follow these steps to set up the project locally.

### 1. Clone or Download the project
Ensure you are in the project directory.

### 2. Set up a Virtual Environment

**Windows:**
```bash
python -m venv env
env\Scripts\activate
```

#### Mac/Linux:
```bash
source venv/bin/activate
```

You may also need Firefox installed:

```bash
sudo apt install firefox-esr
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

---

## ▶️ Usage

Run the scraper:

```bash
python scraper.py
```

It expects a ```category_list.csv``` with columns :

- category_name
- status
- last_searched_updated

## 📁 Input CSV Format

| Column              | Description           | 
|---------------------|-----------------------|
| category_name       | Category to search    |
| status              | `PENDING` or `DONE`   |
| last_searched_date  | Automatically updated |

keeps track of the categories seached using this file.


The script will:

- Scrape the first page of Daraz results
- See if there is an existing cateogry page for the search_term 
- If there is an existing category page -> scrap the products in that category page
- If there is no category page for the search ->  scraps the search page
- Find the top selling item  
- Fuzzy-match similar product titles  
- Display all results sorted by sold count  
- Save all output into: category_report -> date -> category.txt

---

## 📁 Output Example

```
================= TOP SELLING ITEM =================
Name: iPhone 14 Pro Max XYZ
SKU: 264620815_BD-1235152779 
Price: ৳120,000
Sold: 2.4k sold (2400)
Link: https://...

============= ITEMS SIMILAR TO TOP SELLING =============
[Similarity 94%] iPhone 14 Pro Max (Global)
...

================= ALL SORTED RESULTS =================
1. iPhone 14 Pro Max ...
2. iPhone 14 ...
...
```

---

## 🧰 Requirements

See: **requirements.txt**

---

## 📝 Notes

- Script runs in **headless** Firefox mode  
- Uses `webdriver-manager` → no need to install geckodriver manually  
- Works on Windows, macOS, and Linux  
