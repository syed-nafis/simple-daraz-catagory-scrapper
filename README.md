# 🛒 Daraz Product Scraper with Fuzzy Matching

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![Selenium](https://img.shields.io/badge/Selenium-4.0%2B-43B02A?style=for-the-badge&logo=selenium&logoColor=white)
![Firefox](https://img.shields.io/badge/Firefox-Headless-orange?style=for-the-badge&logo=firefox-browser&logoColor=white)

A specialized web scraper for **Daraz.com.bd** that:

- Searches a term or category
- Scrapes product listings from the search or category page
- Sorts products by **sold count**
- Uses **fuzzy matching** to group items similar to the top-selling product
- Stores progress in a CSV file for **batch runs and retrying failed categories**

---

## 🚀 Key Features

- **Interactive Mode (default)**  
  Run a single search from the terminal and generate a detailed text report.

- **Batch Mode (CSV-driven)**  
  Use `category_list.csv` to manage many categories:
  - Run the next *N* new categories
  - Retry all `PENDING` categories

- **Fuzzy Matching (RapidFuzz)**  
  Groups products whose titles are similar to the **top-selling product**, using token-based fuzzy matching.

- **Progress Tracking in CSV**
  - `category_name`
  - `status` (`PENDING` / `DONE`)
  - `last_searched_date`

- **Clean Text Reports**
  - Top-selling item
  - Items similar to the top-selling one
  - All items sorted by sold volume

---

## 🛠️ Tech Stack

- **Python 3.8+**
- **Selenium** – driving Firefox in headless mode
- **RapidFuzz** – fuzzy string similarity
- **webdriver-manager** – automatic geckodriver installation
- **Firefox (headless)**

---

## Basic Scraper Flow
- Scrape the first page of Daraz results.
- See if there is an existing cateogry page for the search_term 
- If there is an existing category page -> scrap the products in that category page
- If there is no category page for the search ->  scraps the search page
- Find the top selling item  
- Fuzzy-match similar product titles  
- Display all results sorted by sold count  
- Save all output into: category_report -> date -> category.txt

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
python -m venv env
source env/bin/activate
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

## 📁 Input CSV Format

| Column              | Description                              | 
|---------------------|------------------------------------------|
| category_name       | Search term / category to scrape         |
| status              | `PENDING` or `DONE` (empty for new rows) |
| last_searched_date  | Automatically updated ```yyyy-mm-dd```   |

The file is automatically created/updated by the script:

- If the category is new → a row is created
- If it already exists → the row is updated
---

## ▶️ Usage
There are two ways to run the scraper: **Interactive Mode** (default) or **Batch Mode**.

### 1. Interactive Mode (Single Search)
Run the script without arguments to search for a single item.

```bash
python scraper.py
```

Flow: (if you do not have a category_list.csv -> this will create one for you)
- Prompts you: Please enter a search query
- Opens Daraz homepage
- Searches for the given term
- Tries to click the Category in the sidebar (if found), otherwise uses the search results page
- Scrapes product cards
- Writes report to:
```text
category_report/<YYYY-MM-DD>/<search_query>.txt
```
- Updates or creates an entry in ```category_list.csv```.

### 2. Batch Mode (Bulk Processing)
Process multiple categories in batches defined in ```category_list.csv```.
It expects a ```category_list.csv``` with columns :
- category_name
- status
- last_searched_date
Run the scraper: (for 5 new categories)

```bash
python scraper.py --next-items 5
```

Flow:
- Loads ```category_list.csv```
- Optionally asks if you want to retry ```PENDING``` categories first
- Selects up to ```N``` new (```status == ""```) categories after any pending retries
- Runs each one, updating:
  - ```status``` → ```DONE``` or ```PENDING```
  - ```last_searched_date``` → today’s date

### Retry only PENDING categories

```bash
python scraper.py --retry-pending-categories
```

Behavior:
- Only processes categories where status == ```"PENDING"```.

### 3. Generate CSV Reports
Generate a simple console summary from ```category_list.csv```:

### All completed ( ```DONE```) categories

```bash
python scraper.py --generate-report searched
```

### All completed ( ```PENDING``` ) categories

```bash
python scraper.py --generate-report pending
```

---

### 📁 Output Files
Reports are stored under:
```text
category_report/<YYYY-MM-DD>/<query>.txt
```
Each report contains:
- Search term, status (category page vs search results), and final URL
- Top Selling Item
- Items Similar to Top Selling (fuzzy match)
- All Sorted Results (by sold count, descending)

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
