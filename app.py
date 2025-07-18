# Beginner Gardener AI Agent: Core Prototype (Texas-focused)
# Dependencies: streamlit, pandas, datetime, requests, PIL, fpdf, ics

import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
from PIL import Image
import io
from fpdf import FPDF
from ics import Calendar, Event

# --- Core Data ---
usda_zone_by_zip = {
    "77001": "9a",
    "78701": "8b",
    "75201": "8a",
    "79901": "8a",
    "76101": "8a"
}

variety_guide = {
    "Warm-Season": {
        "Late Summer": [
            {"name": "Clemson Spineless Okra", "link": "https://www.burpee.com/okra-clemson-spineless-prod000695.html", "image": "https://images.burpee.com/is/image/Burpee/000695?wid=150", "level": "Beginner", "organic": True, "tasks": ["Direct sow in July or early August", "Harvest when pods are 2–3 inches long"], "recurring": ["Harvest every 2–3 days"]},
            {"name": "Beauregard Sweet Potato", "link": "https://www.johnnyseeds.com/vegetables/sweet-potatoes/beauregard-sweet-potato-3250.html", "image": "https://www.johnnyseeds.com/on/demandware.static/-/Sites-jss-master/default/dwff754dd1/images/products/vegetables/03250.jpg", "level": "Intermediate", "organic": False, "tasks": ["Transplant slips in mid-summer", "Hill soil around base in August"], "recurring": ["Water every 5 days"]}
        ]
    },
    "Cold-Tolerant": {
        "Early": [
            {"name": "Bloomsdale Spinach", "link": "https://www.edenbrothers.com/products/bloomsdale-spinach-seeds", "image": "https://www.edenbrothers.com/store/media/Seeds/Spinach/Spinach_Bloomsdale_LS.jpg", "level": "Beginner", "organic": True, "tasks": ["Direct sow 6 weeks before last frost", "Thin seedlings to 3 inches"], "recurring": ["Water every 3 days"]},
            {"name": "Winterbor Kale", "link": "https://www.johnnyseeds.com/vegetables/kale/winterbor-f1-kale-seed-393.html", "image": "https://www.johnnyseeds.com/on/demandware.static/-/Sites-jss-master/default/dw419bf74d/images/products/vegetables/00393_01_winterbor.jpg", "level": "Beginner", "organic": False, "tasks": ["Sow indoors or direct-seed 4–6 weeks before frost"], "recurring": ["Fertilize every 21 days"]}
        ]
    },
    "Tomatoes": {
        "Spring": [
            {"name": "Early Girl", "link": "https://www.burpee.com/early-girl-tomato.html", "image": "https://images.burpee.com/is/image/Burpee/early-girl-tomato?wid=150", "level": "Beginner", "organic": True, "tasks": ["Start seeds indoors mid-January", "Transplant outdoors after last frost in March", "Side-dress with compost in May"], "recurring": ["Fertilize every 14 days"]},
            {"name": "Celebrity", "link": "https://bonnieplants.com/products/celebrity-tomato", "image": "https://cdn.shopify.com/s/files/1/0059/8835/2052/products/CelebrityTomatoPlant_900x.jpg", "level": "Beginner", "organic": False, "tasks": ["Start seeds indoors late January", "Harden off 10 days before transplanting", "Stake plants upon transplant"], "recurring": ["Water every 3 days"]}
        ]
    }
}

# Fetch average frost date from WeatherAPI (mock placeholder)
def get_estimated_last_frost(zip_code):
    try:
        api_key = st.secrets.get("weatherapi_key")  # Ensure this key is set in Streamlit secrets
        if not api_key:
            raise ValueError("Weather API key not found.")
        url = f"http://api.weatherapi.com/v1/forecast.json?key={api_key}&q={zip_code}&days=10"
        res = requests.get(url)
        data = res.json()
        for day in data['forecast']['forecastday']:
            date_obj = datetime.strptime(day['date'], "%Y-%m-%d")
            if day['day']['mintemp_f'] > 36:  # Conservative buffer against frost
                return date_obj
        return datetime(datetime.today().year, 3, 15)  # fallback default
    except:
        return datetime(datetime.today().year, 3, 15)  # March 15 typical in TX

# PDF Export
def export_variety_pdf(df):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.image(logo_url, x=10, y=8, w=15)
    pdf.set_font("Arial", "B", size=12)
    pdf.set_xy(30, 10)
    pdf.cell(150, 10, txt=garden_title, ln=True, align="C")
    pdf.set_font("Arial", size=10)
    pdf.set_xy(10, 20)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Seasonal Variety Guide", ln=True, align="C")
    for index, row in df.iterrows():
        line = f"{row['Crop']} ({row['Season']}) - {row['Variety']} | Level: {row['Experience Level']} | Organic: {row['Organic']}"
        pdf.multi_cell(0, 10, txt=line)
    pdf.set_y(-20)
    pdf.set_font("Arial", size=8)
    pdf.cell(0, 10, f"Generated on {datetime.today().strftime('%B %d, %Y')}", align="C")
    return pdf.output(dest='S').encode('latin1')

# iCal Export with live logic and recurring support
def export_task_ical(start_date=None, zip_code=None):
    cal = Calendar()
    if not start_date:
        start_date = datetime.today()
    frost_date = get_estimated_last_frost(zip_code) if zip_code else None
    task_offset = 0
    for crop, seasons in variety_guide.items():
        for season, varieties in seasons.items():
            for v in varieties:
                if "tasks" in v:
                    for task in v["tasks"]:
                        e = Event()
                        e.name = f"{v['name']} – {task}"
                        e.begin = start_date + timedelta(days=task_offset)
                        e.description = f"Gardening Task: {task} for {v['name']}"
                        if frost_date and "frost" in task.lower():
                            e.begin = frost_date + timedelta(days=1)
                            e.description += "\n⚠️ Scheduled after estimated last frost."
                        cal.events.add(e)
                        task_offset += 2
                if "recurring" in v:
                    for rule in v["recurring"]:
                        e = Event()
                        e.name = f"{v['name']} – {rule}"
                        e.begin = start_date + timedelta(days=task_offset)
                        e.description = f"Ongoing Task: {rule} for {v['name']}"
                        if "every" in rule:
                            try:
                                interval = int(rule.split("every ")[1].split(" ")[0])
                                for i in range(6):
                                    recur = Event()
                                    recur.name = e.name
                                    recur.begin = e.begin + timedelta(days=i * interval)
                                    recur.description = e.description
                                    cal.events.add(recur)
                            except:
                                cal.events.add(e)
                        else:
                            cal.events.add(e)
    return str(cal)

# Table Builder
def generate_variety_table():
    rows = []
    for crop, seasons in variety_guide.items():
        for season, varieties in seasons.items():
            for v in varieties:
                rows.append({
                    "Crop": crop,
                    "Season": season,
                    "Variety": v["name"],
                    "Experience Level": v["level"],
                    "Organic": "Yes" if v.get("organic") else "No",
                    "Seed Link": v["link"]
                })
    return pd.DataFrame(rows)

# --- Streamlit UI ---

# Optional: Container Gardening Guidance
st.markdown("### 🪴 Container Gardening Planner")
st.info("Don’t have space for raised beds? No problem! Select crops ideal for container growing below.")

container_crops = [v for cat in variety_guide.values() for stage in cat.values() for v in stage if v["level"] == "Beginner"]
selected_container = st.selectbox("Choose a container-friendly crop:", [v["name"] for v in container_crops])
container_details = next((v for v in container_crops if v["name"] == selected_container), None)

if container_details:
    st.image(container_details["image"], width=150)
    st.markdown(f"📦 **Ideal for Containers:** Yes")
    st.markdown(f"📋 **Tasks:**")
    for task in container_details.get("tasks", []):
        st.markdown(f"- {task}")
    if container_details.get("recurring"):
        st.markdown("♻️ **Ongoing Care:**")
        for rule in container_details["recurring"]:
            st.markdown(f"- {rule}")
    st.markdown(f"🔗 [Seed Source]({container_details['link']})")
st.markdown("### 🌾 Raised Bed Layout Planner")
layout_rows = 4
layout_cols = 6
selected_crop = st.selectbox("Select a crop to place in the garden bed:", [v["name"] for cat in variety_guide.values() for stage in cat.values() for v in stage])

# Preview selected crop with image and spacing tip (mock spacing guidance)
spacing_guide = {
    "Early Girl": "18–24 inches apart",
    "Celebrity": "24 inches apart",
    "Bloomsdale Spinach": "4–6 inches apart",
    "Winterbor Kale": "12–18 inches apart",
    "Clemson Spineless Okra": "12–18 inches apart",
    "Beauregard Sweet Potato": "12 inches apart"
}

selected_details = next((v for cat in variety_guide.values() for stage in cat.values() for v in stage if v["name"] == selected_crop), None)
if selected_details:
    st.image(selected_details["image"], width=150)
    spacing = spacing_guide.get(selected_crop, "Spacing info not available")
    st.markdown(f"📏 **Recommended Spacing:** {spacing}")

if "bed_layout" not in st.session_state:
    st.session_state.bed_layout = [["" for _ in range(layout_cols)] for _ in range(layout_rows)]

for i in range(layout_rows):
    cols = st.columns(layout_cols)
    for j in range(layout_cols):
        label = st.session_state.bed_layout[i][j] if st.session_state.bed_layout[i][j] else "[Empty]"
        if cols[j].button(label, key=f"bed_{i}_{j}"):
            st.session_state.bed_layout[i][j] = selected_crop

if st.button("🧹 Clear Layout"):
    st.session_state.bed_layout = [["" for _ in range(layout_cols)] for _ in range(layout_rows)]

bed_df = pd.DataFrame(st.session_state.bed_layout)
st.dataframe(bed_df)
st.download_button("📥 Download Bed Layout (CSV)", data=bed_df.to_csv(index=False), file_name="garden_bed_layout.csv")

# PNG Export (Visual Layout)
import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(layout_cols, layout_rows))
ax.set_xlim(0, layout_cols)
ax.set_ylim(0, layout_rows)
ax.set_xticks(range(layout_cols+1))
ax.set_yticks(range(layout_rows+1))
ax.grid(True)
ax.invert_yaxis()

for i in range(layout_rows):
    for j in range(layout_cols):
        crop = st.session_state.bed_layout[i][j]
        if crop:
            ax.text(j+0.5, i+0.5, crop[:10], ha='center', va='center', fontsize=6, wrap=True)

plt.tight_layout()
buffer = io.BytesIO()
plt.savefig(buffer, format='png')
buffer.seek(0)
st.download_button("🖼️ Download Bed Layout (PNG)", data=buffer, file_name="garden_bed_layout.png", mime="image/png")

# PDF Export with QR Code to iCal
from fpdf import FPDF
import qrcode

def export_bed_layout_pdf_qr(layout_df, ical_url):
    garden_title = "Jamie's Backyard Garden"
    logo_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3f/Leaf_green.svg/2048px-Leaf_green.svg.png"
    companion_guide = {
        "Early Girl": ["Basil", "Marigold"],
        "Celebrity": ["Chives", "Nasturtium"],
        "Bloomsdale Spinach": ["Radish", "Strawberry"],
        "Winterbor Kale": ["Beets", "Celery"],
        "Clemson Spineless Okra": ["Peppers", "Melons"],
        "Beauregard Sweet Potato": ["Beans", "Thyme"]
    }
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt="Garden Bed Layout", ln=True, align="C")
    pdf.ln(4)

    for i, row in layout_df.iterrows():
        row_line = ' | '.join([cell if cell else "[Empty]" for cell in row])
        pdf.multi_cell(0, 8, txt=row_line, align="L")

        # Add task summaries under the row
        for cell in row:
            if cell:
                pdf.set_font("Arial", size=10)
                pdf.multi_cell(0, 6, txt=f"🌱 {cell}", align="L")
                for cat in variety_guide.values():
                    for stage in cat.values():
                        for v in stage:
                            if v['name'] == cell:
                                if v.get("tasks"):
                                    for t in v["tasks"][:2]:
                                        pdf.multi_cell(0, 6, txt=f"  • {t}", align="L")
                                if v.get("recurring"):
                                    for r in v["recurring"][:1]:
                                        pdf.multi_cell(0, 6, txt=f"  ⟳ {r}", align="L")
                if companion_guide.get(cell):
                    comp = ", ".join(companion_guide[cell])
                    pdf.multi_cell(0, 6, txt=f"  🌼 Companion Plants: {comp}", align="L")
                for cat in variety_guide.values():
                    for stage in cat.values():
                        for v in stage:
                            if v['name'] == cell:
                                if v.get("tasks"):
                                    for t in v["tasks"][:2]:
                                        pdf.multi_cell(0, 6, txt=f"  • {t}", align="L")
        pdf.multi_cell(0, 8, txt=row_line, align="L")

    pdf.ln(5)
    pdf.set_font("Arial", style="B", size=10)
    pdf.cell(200, 8, txt="Scan to import garden calendar:", ln=True)

    qr = qrcode.make(ical_url)
    buf = io.BytesIO()
    qr.save(buf)
    buf.seek(0)
    pdf.image(buf, x=80, w=50)

    return pdf.output(dest='S').encode('latin1')

ical_download_url = "https://example.com/gardening_tasks.ics"  # Placeholder or replace with real hosted link
pdf_qr = export_bed_layout_pdf_qr(bed_df, ical_download_url)

with st.expander("🔍 Preview Bed Layout PDF"):
    from pdf2image import convert_from_bytes
    preview_images = convert_from_bytes(pdf_qr)
    for img in preview_images:
        st.image(img, caption="PDF Preview", use_column_width=True)

st.download_button("📄 Export Bed Layout (PDF + QR)", data=pdf_qr, file_name="garden_bed_layout_qr.pdf", mime="application/pdf"), file_name="garden_bed_layout.csv")
st.markdown("### 🧾 Seasonal Variety Guide (Printable)")
level_filter = st.selectbox("Filter by experience level:", ["All", "Beginner", "Intermediate", "Advanced"])
organic_filter = st.checkbox("Show only organic varieties")
zip_input = st.text_input("Enter ZIP for climate-aware planning:", "77001")
custom_start = st.date_input("📅 Choose Start Date for Task Calendar Export:", datetime.today())

frost_estimate = get_estimated_last_frost(zip_input)
st.markdown(f"📍 **Estimated Last Frost Date for ZIP {zip_input}:** `{frost_estimate.strftime('%B %d, %Y')}`")
if frost_estimate > datetime.combine(custom_start, datetime.min.time()):
    st.warning("⚠️ Your selected start date is before the estimated last frost. The calendar export will begin the day after the frost date.")
    custom_start = frost_estimate + timedelta(days=1)
    st.info("🌱 Consider planting early cold-tolerant crops such as spinach, kale, radish, and arugula. These can often be direct-seeded before the last frost date with proper care.")

variety_df = generate_variety_table()
if level_filter != "All":
    variety_df = variety_df[variety_df["Experience Level"] == level_filter]
if organic_filter:
    variety_df = variety_df[variety_df["Organic"] == "Yes"]

st.dataframe(variety_df)
csv_data = variety_df.to_csv(index=False).encode('utf-8')
pdf_data = export_variety_pdf(variety_df)
ical_data = export_task_ical(start_date=custom_start, zip_code=zip_input)

st.download_button("📥 Download CSV Variety Guide", data=csv_data, file_name="variety_guide.csv", mime="text/csv")
st.download_button("📄 Download PDF Variety Guide", data=pdf_data, file_name="variety_guide.pdf", mime="application/pdf")
st.download_button("📅 Export iCal Task Calendar", data=ical_data, file_name="gardening_tasks.ics", mime="text/calendar")

# Mini Export Buttons
st.markdown("### 🌿 Mini Schedule Exports")
mini_df_cold = generate_variety_table().query("Crop == 'Cold-Tolerant'")
mini_df_warm = generate_variety_table().query("Crop == 'Warm-Season'")
mini_csv_cold = mini_df_cold.to_csv(index=False).encode('utf-8')
mini_csv_warm = mini_df_warm.to_csv(index=False).encode('utf-8')
mini_pdf_cold = export_variety_pdf(mini_df_cold)
mini_pdf_warm = export_variety_pdf(mini_df_warm)

col1, col2 = st.columns(2)
with col1:
    st.download_button("❄️ Cold-Tolerant Schedule (CSV)", data=mini_csv_cold, file_name="cold_tolerant_schedule.csv", mime="text/csv")
    st.download_button("❄️ Cold-Tolerant Schedule (PDF)", data=mini_pdf_cold, file_name="cold_tolerant_schedule.pdf", mime="application/pdf")
with col2:
    st.download_button("🔥 Warm-Season Schedule (CSV)", data=mini_csv_warm, file_name="warm_season_schedule.csv", mime="text/csv")
    st.download_button("🔥 Warm-Season Schedule (PDF)", data=mini_pdf_warm, file_name="warm_season_schedule.pdf", mime="application/pdf")

# Monthly Crop Tasks View
st.markdown(f"### 🌿 {datetime.now().strftime('%B')} Crop Varieties")
season = "Spring" if datetime.now().month in [12,1,2,3] else "Summer" if datetime.now().month in [4,5,6,7] else "Fall"
for crop, seasons in variety_guide.items():
    if crop == "Cold-Tolerant" and frost_estimate > datetime.combine(datetime.today(), datetime.min.time()):
        st.markdown("**❄️ Cold-Tolerant Options (Pre-Frost):**")
        for v in seasons.get("Early", []):
            if organic_filter and not v.get("organic"):
                continue
            if level_filter != "All" and v["level"] != level_filter:
                continue
            cols = st.columns([1, 4])
            with cols[0]:
                st.image(v["image"], width=80)
            with cols[1]:
                st.markdown(f"[{v['name']}]({v['link']})", help="Click to view supplier page for this variety")
                st.markdown(f"Experience: *{v['level']}*  ")
                if v.get("organic"):
                    st.markdown("🌱 **Organic Certified**")
                if v.get("tasks"):
                    st.markdown("🗓️ **Cold Season Tasks:**")
                    for task in v["tasks"]:
                        st.markdown(f"- {task}")
                if v.get("recurring"):
                    st.markdown("♻️ **Ongoing Care:**")
                    for rule in v["recurring"]:
                        st.markdown(f"- {rule}")
    elif season in seasons:
        st.markdown(f"**{crop}**")
        for v in seasons[season]:
            if organic_filter and not v.get("organic"):
                continue
            if level_filter != "All" and v["level"] != level_filter:
                continue
            cols = st.columns([1, 4])
            with cols[0]:
                st.image(v["image"], width=80)
            with cols[1]:
                st.markdown(f"[{v['name']}]({v['link']})", help="Click to view supplier page for this variety")
                st.markdown(f"Experience: *{v['level']}*  ")
                if v.get("organic"):
                    st.markdown("🌱 **Organic Certified**")
                if v.get("tasks"):
                    st.markdown("🗓️ **Monthly Tasks:**")
                    for task in v["tasks"]:
                        st.markdown(f"- {task}")
                if v.get("recurring"):
                    st.markdown("♻️ **Ongoing Care:**")
                    for rule in v["recurring"]:
                        st.markdown(f"- {rule}")
    elif crop == "Warm-Season" and datetime.now().month >= 7:
        st.markdown("**🔥 Warm-Season Options (Late Summer):**")
        for v in seasons.get("Late Summer", []):
            if organic_filter and not v.get("organic"):
                continue
            if level_filter != "All" and v["level"] != level_filter:
                continue
            cols = st.columns([1, 4])
            with cols[0]:
                st.image(v["image"], width=80)
            with cols[1]:
                st.markdown(f"[{v['name']}]({v['link']})", help="Click to view supplier page for this variety")
                st.markdown(f"Experience: *{v['level']}*  ")
                if v.get("organic"):
                    st.markdown("🌱 **Organic Certified**")
                if v.get("tasks"):
                    st.markdown("🗓️ **Hot Season Tasks:**")
                    for task in v["tasks"]:
                        st.markdown(f"- {task}")
                if v.get("recurring"):
                    st.markdown("♻️ **Ongoing Care:**")
                    for rule in v["recurring"]:
                        st.markdown(f"- {rule}")
        st.markdown(f"**{crop}**")
        for v in seasons[season]:
            if organic_filter and not v.get("organic"):
                continue
            if level_filter != "All" and v["level"] != level_filter:
                continue
            cols = st.columns([1, 4])
            with cols[0]:
                st.image(v["image"], width=80)
            with cols[1]:
                st.markdown(f"[{v['name']}]({v['link']})", help="Click to view supplier page for this variety")
                st.markdown(f"Experience: *{v['level']}*  ")
                if v.get("organic"):
                    st.markdown("🌱 **Organic Certified**")
                if v.get("tasks"):
                    st.markdown("🗓️ **Monthly Tasks:**")
                    for task in v["tasks"]:
                        st.markdown(f"- {task}")
                if v.get("recurring"):
                    st.markdown("♻️ **Ongoing Care:**")
                    for rule in v["recurring"]:
                        st.markdown(f"- {rule}")
