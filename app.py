import streamlit as st
import os
import re

# ------------------------- CONFIGURATION -------------------------------
BASE_REPORT_DIR = "category_report"

st.set_page_config(page_title="Daraz Market Analyzer", page_icon="🛒", layout="wide")

# ------------------------- CUSTOM CSS ---------------------------
# This improves the spacing and alignment of cards
st.markdown("""
<style>
    div[data-testid="stContainer"] {
        background-color: #ffffff;
        padding: 10px;
        border-radius: 10px;
    }
    .top-seller-badge {
        background-color: #d4edda;
        color: #155724;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 0.85em;
        margin-bottom: 8px;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------- PARSER ---------------------------
def parse_report_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f: content = f.read()

    data = {"search_term": "Unknown", "status": "Unknown", "url": "#", "groups": []}
    
    # Extract Metadata
    search_match = re.search(r"SEARCH TERM : (.*)", content)
    if search_match: data["search_term"] = search_match.group(1).strip()
    
    status_match = re.search(r"STATUS\s+: (.*)", content)
    if status_match: data["status"] = status_match.group(1).strip()
    
    url_match = re.search(r"URL\s+: (.*)", content)
    if url_match: data["url"] = url_match.group(1).strip()

    # Parse Groups
    group_chunks = content.split("🟦 GROUP #")[1:]
    
    for chunk in group_chunks:
        lines = chunk.strip().split("\n")
        group_data = {"top_item": {}, "similars": []}
        
        def get_val(key, line_list):
            for l in line_list:
                if key in l: return l.split(key)[1].strip()
            return ""

        try:
            # Parse Top Item
            t_name = get_val("Name:", lines)
            t_price_sku = get_val("Price:", lines).split("|")
            t_price = t_price_sku[0].strip()
            # Extract SKU safely
            t_sku = t_price_sku[1].replace("SKU:", "").strip() if len(t_price_sku) > 1 else "N/A"
            
            t_link = get_val("Link:", lines)
            t_image = get_val("Image:", lines)
            
            t_sold = "N/A"
            sold_match = re.search(r"Top Seller: (.*) sold", lines[0])
            if sold_match: t_sold = sold_match.group(1)

            group_data["top_item"] = {
                "name": t_name, "price": t_price, "sku": t_sku, 
                "link": t_link, "sold": t_sold, "image": t_image, "is_top": True
            }
        except: continue

        # Parse Similar Items
        sim_start = -1
        for i, l in enumerate(lines):
            if "Similar Items" in l: sim_start = i; break
        
        if sim_start != -1:
            current = {}
            for line in lines[sim_start+1:]:
                line = line.strip()
                if line.startswith("•"):
                    if current: group_data["similars"].append(current)
                    current = {}
                    match = re.search(r"• \[(.*?)% Match\] (.*)", line)
                    if match: current["score"] = match.group(1); current["name"] = match.group(2)
                elif "Price:" in line:
                    parts = line.split("|")
                    current["price"] = parts[0].replace("Price:", "").strip()
                    current["sold"] = parts[1].replace("Sold:", "").strip() if len(parts)>1 else "N/A"
                elif "Link:" in line: current["link"] = line.replace("Link:", "").strip()
                # No SKU/Image for similars usually, but if scraper added them, parse here
            if current: group_data["similars"].append(current)

        data["groups"].append(group_data)
    return data

# ------------------------- UI COMPONENTS ---------------------------

def render_item_card(item, unique_key):
    """Renders a single card with dynamic content."""
    
    with st.container(border=True):
        # 1. HEADER (Top Seller Badge)
        if item.get("is_top"):
            st.markdown('<div class="top-seller-badge">🏆 TOP SELLER</div>', unsafe_allow_html=True)
        else:
            st.markdown(f"<small style='color:gray'>Match: {item.get('score', 'N/A')}%</small>", unsafe_allow_html=True)
            
        # 2. IMAGE SECTION (Top Seller Only)
        img_url = item.get("image")
        has_image = img_url and img_url != "None" and len(img_url) > 10
        
        if item.get("is_top") and has_image:
            state_key = f"show_img_{unique_key}"
            if st.session_state.get(state_key, False):
                st.image(img_url, use_container_width=True)
                if st.button("Hide", key=f"btn_hide_{unique_key}"):
                    st.session_state[state_key] = False
                    st.rerun()
            else:
                if st.button("📷 Show Image", key=f"btn_show_{unique_key}"):
                    st.session_state[state_key] = True
                    st.rerun()

        # 3. TEXT DETAILS
        name = item['name']
        # TRUNCATION LOGIC: Only truncate if NOT top seller
        if not item.get("is_top"):
            if len(name) > 50: name = name[:47] + "..."
        
        if item.get("is_top"):
            st.markdown(f"**{name}**")
            # Show SKU for top seller
            st.caption(f"🆔 SKU: `{item.get('sku', 'N/A')}`")
            st.markdown(f":green[**💰 {item['price']}**]")
        else:
            st.caption(name)
            st.caption(f"💰 {item['price']}")

        st.caption(f"📦 **{item['sold']}**")
        st.link_button("View on Daraz", item['link'], use_container_width=True)

def create_dynamic_grid(items, group_id, items_per_row=5):
    """
    Simulates a Flexbox wrap by calculating rows/cols.
    This keeps Streamlit buttons functional.
    """
    # Calculate how many rows we need
    num_items = len(items)
    num_rows = (num_items + items_per_row - 1) // items_per_row

    for row_idx in range(num_rows):
        cols = st.columns(items_per_row)
        start_idx = row_idx * items_per_row
        end_idx = min(start_idx + items_per_row, num_items)
        
        for i in range(start_idx, end_idx):
            item = items[i]
            col_idx = i % items_per_row
            with cols[col_idx]:
                render_item_card(item, unique_key=f"g{group_id}_it{i}")

# ------------------------- MAIN APP ---------------------------

st.sidebar.title("🗂️ Reports")
if not os.path.exists(BASE_REPORT_DIR): st.error("No reports found."); st.stop()

dates = sorted(os.listdir(BASE_REPORT_DIR), reverse=True)
selected_date = st.sidebar.selectbox("Select Date", dates)
if selected_date:
    files = [f for f in os.listdir(os.path.join(BASE_REPORT_DIR, selected_date)) if f.endswith(".txt")]
    selected_file = st.sidebar.selectbox("Select Report", files)
    if st.sidebar.button("Refresh"): st.rerun()

if selected_date and selected_file:
    data = parse_report_file(os.path.join(BASE_REPORT_DIR, selected_date, selected_file))
    
    # === REPORT HEADER ===
    st.title(f"🔎 {data['search_term']}")
    
    # Metadata Row
    m1, m2, m3 = st.columns([2, 1, 2])
    with m1:
        # Visual styling for status
        if "Found" in data['status']:
            st.success(f"**Status:** {data['status']}")
        else:
            st.error(f"**Status:** {data['status']}")
    
    with m2:
        st.metric("Groups Found", len(data["groups"]))
        
    with m3:
        if data['url'] and data['url'] != "#":
            st.link_button("🔗 Visit Category Page", data['url'])
        else:
            st.caption("No Category URL available")
            
    st.divider()

    # === GROUPS DISPLAY ===
    for i, group in enumerate(data["groups"], 1):
        st.subheader(f"Group #{i}")
        
        # Combine items for the grid
        all_items = [group["top_item"]] + group["similars"]
        
        # Render using the dynamic grid function
        create_dynamic_grid(all_items, group_id=i, items_per_row=5)
        
        st.divider()