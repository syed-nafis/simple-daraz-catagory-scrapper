# Daraz Product Scraper with Fuzzy Matching

This project scrapes product listings from **Daraz.com.bd** using Selenium, 
sorts them by the number of sold units, identifies the top‐selling product, 
and groups similar products using fuzzy text matching.

All output is printed to the console and saved in a `<query>.txt` file.

---

## 🔧 Features

- Scrapes product name, price, sold count, SKU, and link  
- Detects and parses "k sold" formats (e.g., 2.4k → 2400)  
- Sorts all products by highest sold count  
- Applies fuzzy matching (RapidFuzz) to group similar items  
- Outputs:
  - Top selling item  
  - Items similar to top selling  
  - Full sorted results  
- Saves everything into:  
  ```
  <search query>.txt
  ```

---

## 📦 Installation

### 1. Create a virtual environment
```bash
python -m venv venv
```

### 2. Activate the environment

#### Windows:
```bash
venv\Scripts\activate
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

---

## 📜 License

MIT License
