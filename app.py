# Beginner Gardener AI – Full Corrected Version
# Streamlit deployment-ready app.py

import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
from PIL import Image
import io
from fpdf import FPDF  # Reverted import to match fpdf2 module structure
from ics import Calendar, Event
import matplotlib.pyplot as plt
import qrcode
from pdf2image import convert_from_bytes

# USDA zone lookup (simplified)
usda_zone_by_zip = {
    "77001": "9a",
    "78701": "8b",
    "75201": "8a",
    "79901": "8a",
    "76101": "8a"
}

spacing_guide = {
    "Early Girl": "18–24 inches",
    "Bloomsdale Spinach": "4–6 inches"
}

container_guide = {
    "Early Girl": "5-gallon pot",
    "Bloomsdale Spinach": "6-inch pot"
}

variety_guide = {
    "Tomatoes": {
        "Spring": [
            {"name": "Early Girl", "level": "Beginner", "link": "https://burpee.com", "organic": True,
             "image": "https://images.burpee.com/is/image/Burpee/early-girl-tomato?wid=150",
             "tasks": ["Start indoors in January", "Transplant after frost"],
             "recurring": ["Fertilize every 2 weeks"]}
        ]
    },
    "Cold-Tolerant": {
        "Early": [
            {"name": "Bloomsdale Spinach", "level": "Beginner", "link": "https://edenbrothers.com",
             "organic": True, "image": "https://www.edenbrothers.com/store/media/Seeds/Spinach/Spinach_Bloomsdale_LS.jpg",
             "tasks": ["Direct sow before last frost"], "recurring": ["Water every 3 days"]}
        ]
    }
}

companion_guide = {
    "Early Girl": ["Basil", "Marigold"],
    "Bloomsdale Spinach": ["Radish"]
}

def get_estimated_last_frost(zip_code):
    return datetime(datetime.today().year, 3, 15)

def export_task_ical(start_date, zip_code):
    cal = Calendar()
    task_offset = 0
    for cat in variety_guide.values():
        for stage in cat.values():
            for v in stage:
                for task in v.get("tasks", []):
                    e = Event()
                    e.name = f"{v['name']} – {task}"
                    e.begin = start_date + timedelta(days=task_offset)
                    cal.events.add(e)
                    task_offset += 2
                for r in v.get("recurring", []):
                    for i in range(6):
                        recur = Event()
                        recur.name = f"{v['name']} – {r}"
                        recur.begin = start_date + timedelta(days=task_offset + i*7)
                        cal.events.add(recur)
    return str(cal)

def export_pdf(layout_df, ical_url):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt="Garden Bed Layout", ln=True, align="C")
    for i, row in layout_df.iterrows():
        row_line = ' | '.join([cell if cell else "[Empty]" for cell in row])
        pdf.multi_cell(0, 8, txt=row_line)
        for cell in row:
            if cell:
                pdf.multi_cell(0, 6, txt=f"🌱 {cell}")
                for cat in variety_guide.values():
                    for stage in cat.values():
                        for v in stage:
                            if v['name'] == cell:
                                for t in v.get("tasks", [])[:2]:
                                    pdf.multi_cell(0, 6, txt=f"• {t}")
                                for r in v.get("recurring", [])[:1]:
                                    pdf.multi_cell(0, 6, txt=f"⟳ {r}")
                if cell in companion_guide:
                    pdf.multi_cell(0, 6, txt=f"🌼 Companion: {', '.join(companion_guide[cell])}")
    qr = qrcode.make(ical_url)
    buf = io.BytesIO()
    qr.save(buf)
    buf.seek(0)
    pdf.image(buf, x=80, w=50)
    pdf.set_y(-20)
    pdf.set_font("Arial", size=8)
    pdf.cell(0, 10, f"Generated {datetime.today().strftime('%Y-%m-%d')}", align="C")
    return pdf.output(dest='S').encode('latin1')

st.set_page_config(page_title="Beginner Gardener AI", layout="wide")
st.title("🌿 Beginner Gardener AI")

zip_input = st.text_input("Enter ZIP code:", "77001")
custom_start = st.date_input("Select calendar start date:", datetime.today())
frost_estimate = get_estimated_last_frost(zip_input)
if custom_start < frost_estimate:
    st.warning("Selected date is before last frost. Adjusting...")
    custom_start = frost_estimate + timedelta(days=1)

st.markdown(f"**Estimated Last Frost:** {frost_estimate.strftime('%B %d, %Y')}")

# CONTAINER CROPS
st.subheader("🪴 Container Crops")
selected_container = st.selectbox("Choose container crop:", [v["name"] for cat in variety_guide.values() for stage in cat.values() for v in stage])
for cat in variety_guide.values():
    for stage in cat.values():
        for v in stage:
            if v["name"] == selected_container:
                st.image(v["image"], width=100)
                st.markdown(f"**Spacing:** {spacing_guide.get(v['name'], 'N/A')}")
                st.markdown("**Tasks:**")
                for t in v.get("tasks", []):
                    st.markdown(f"- {t}")
                for r in v.get("recurring", []):
                    st.markdown(f"♻️ {r}")
                st.markdown(f"🔗 [Source]({v['link']})")

# RAISED BED
st.subheader("🧱 Raised Bed Planner")
layout_rows, layout_cols = 4, 6
if "bed_layout" not in st.session_state:
    st.session_state.bed_layout = [["" for _ in range(layout_cols)] for _ in range(layout_rows)]

selected_crop = st.selectbox("Select a crop for bed:", [v["name"] for cat in variety_guide.values() for stage in cat.values() for v in stage])
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

ical_data = export_task_ical(custom_start, zip_input)
st.download_button("📅 Download iCal", data=ical_data, file_name="gardening_tasks.ics")

pdf_data = export_pdf(bed_df, "https://example.com/gardening_tasks.ics")
with st.expander("🔍 Preview PDF"):
    preview_images = convert_from_bytes(pdf_data)
    for img in preview_images:
        st.image(img, caption="Layout Preview", use_column_width=True)

st.download_button("📄 Download PDF", data=pdf_data, file_name="garden_layout.pdf", mime="application/pdf")

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
            ax.text(j+0.5, i+0.5, crop[:10], ha='center', va='center', fontsize=6)
plt.tight_layout()
buffer = io.BytesIO()
plt.savefig(buffer, format='png')
buffer.seek(0)
st.download_button("🖼️ Download PNG", data=buffer, file_name="bed_layout.png", mime="image/png")

