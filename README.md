# 🛒 Daraz Product Scraper with Fuzzy Matching

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![Selenium](https://img.shields.io/badge/Selenium-4.0%2B-43B02A?style=for-the-badge&logo=selenium&logoColor=white)
![Firefox](https://img.shields.io/badge/Firefox-Headless-orange?style=for-the-badge&logo=firefox-browser&logoColor=white)

A specialized web scraper that extracts product listings from **Daraz.com.bd**, sorts them by sales volume, and utilizes fuzzy logic to identify and group the most relevant products.

This tool is designed to cut through the noise of e-commerce listings by identifying the **true top-selling item** and grouping similar variations using [RapidFuzz](https://github.com/maxbachmann/RapidFuzz).

---

## 🚀 Features

* **Automated Extraction:** Scrapes product name, price, sold count, SKU, and direct links.
* **Smart Parsing:** Automatically detects and converts "k sold" formats (e.g., `2.4k` → `2400`) for accurate sorting.
* **Sales Ranking:** Sorts the entire product list by the highest number of units sold.
* **Fuzzy Matching:** Uses string similarity algorithms to identify items similar to the top-seller.
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

Enter a product search term:

```
Enter product search query: iphone 14 pro max
```

The script will:

- Scrape the first page of Daraz results  
- Find the top selling item  
- Fuzzy-match similar product titles  
- Display all results sorted by sold count  
- Save all output into:

```
iphone 14 pro max.txt
```

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
