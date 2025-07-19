# Beginner Gardener AI – Reconstructed from Scratch (Part 1 of 4)

import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
from PIL import Image
import io
from fpdf import FPDF  # Ensure this matches fpdf2==2.7.6 in requirements.txt
from ics import Calendar, Event
import matplotlib.pyplot as plt
import qrcode
from pdf2image import convert_from_bytes

st.set_page_config(page_title="Beginner Gardener AI", layout="wide")
st.title("🌿 Beginner Gardener AI Planner")

# Sample spacing and companion guide
def get_spacing():
    return {
        "Tomato": "18–24 in",
        "Spinach": "6 in",
        "Okra": "12–18 in"
    }

def get_companions():
    return {
        "Tomato": ["Basil", "Marigold"],
        "Spinach": ["Radish"],
        "Okra": ["Peppers"]
    }

# USDA zip to frost estimate
def get_estimated_last_frost(zip_code):
    return datetime(datetime.today().year, 3, 15)

spacing_guide = get_spacing()
companion_guide = get_companions()

# Part 2: Crop Data and Layout Planner

container_guide = {
    "Tomato": "5-gallon pot",
    "Spinach": "6-inch pot",
    "Okra": "5-gallon pot"
}

variety_guide = {
    "Warm-Season": {
        "Summer": [
            {"name": "Tomato", "link": "https://example.com/tomato", "image": "https://via.placeholder.com/100", "level": "Beginner", "organic": True,
             "tasks": ["Start seeds indoors in Jan", "Transplant after frost"], "recurring": ["Fertilize every 2 weeks"]},
            {"name": "Okra", "link": "https://example.com/okra", "image": "https://via.placeholder.com/100", "level": "Beginner", "organic": False,
             "tasks": ["Direct sow after frost"], "recurring": ["Harvest every 2–3 days"]}
        ]
    },
    "Cold-Tolerant": {
        "Early": [
            {"name": "Spinach", "link": "https://example.com/spinach", "image": "https://via.placeholder.com/100", "level": "Beginner", "organic": True,
             "tasks": ["Direct sow in cool soil"], "recurring": ["Water every 3 days"]}
        ]
    }
}

layout_rows, layout_cols = 4, 6
if "bed_layout" not in st.session_state:
    st.session_state.bed_layout = [["" for _ in range(layout_cols)] for _ in range(layout_rows)]

selected_crop = st.selectbox("Select a crop to place:", [v["name"] for cat in variety_guide.values() for stage in cat.values() for v in stage])

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

# Container Gardening Display
st.subheader("🪴 Container Gardening")
selected_container = st.selectbox("Choose a container crop:", list(container_guide.keys()))
if selected_container:
    spacing = spacing_guide.get(selected_container, "N/A")
    container_size = container_guide.get(selected_container, "N/A")
    companions = companion_guide.get(selected_container, [])
    st.markdown(f"📦 **Recommended Container Size:** {container_size}")
    st.markdown(f"📏 **Spacing:** {spacing}")
    st.markdown(f"🌼 **Companion Plants:** {', '.join(companions)}")
    for cat in variety_guide.values():
        for stage in cat.values():
            for v in stage:
                if v["name"] == selected_container:
                    st.image(v["image"], width=100)
                    st.markdown("**Tasks:**")
                    for task in v.get("tasks", []):
                        st.markdown(f"- {task}")
                    st.markdown("**Recurring Care:**")
                    for care in v.get("recurring", []):
                        st.markdown(f"♻️ {care}")
                    st.markdown(f"🔗 [Seed Source]({v['link']})")

# Calendar and Export Buttons
ical_data = Calendar()
for cat in variety_guide.values():
    for stage in cat.values():
        for v in stage:
            for task in v.get("tasks", []):
                e = Event()
                e.name = f"{v['name']} – {task}"
                e.begin = datetime.today() + timedelta(days=1)
                ical_data.events.add(e)
ical_str = str(ical_data)
st.download_button("📅 Download Calendar (.ics)", data=ical_str, file_name="garden_schedule.ics")

# PDF Export
class GardenPDF(FPDF):
    def header(self):
        self.set_font("Arial", 'B', 12)
        self.cell(0, 10, "Garden Layout Summary", ln=True, align="C")

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", 'I', 8)
        self.cell(0, 10, f"Generated {datetime.today().strftime('%Y-%m-%d')}", 0, 0, 'C')

pdf = GardenPDF()
pdf.add_page()
pdf.set_font("Arial", size=10)
for i, row in bed_df.iterrows():
    text = ' | '.join([cell if cell else "[Empty]" for cell in row])
    pdf.multi_cell(0, 8, txt=text)
pdf_bytes = pdf.output(dest='S').encode('latin1')
st.download_button("📄 Download Garden PDF", data=pdf_bytes, file_name="bed_layout.pdf", mime="application/pdf")

# Part 4: Seasonal Display and README Guidance

# Seasonal variety display
st.subheader("🌱 Crop Preview by Season")
current_month = datetime.today().month
season = "Spring" if current_month in [1, 2, 3, 4, 5] else "Summer" if current_month in [6, 7, 8] else "Fall"

for crop_group, stages in variety_guide.items():
    for stage, crops in stages.items():
        if (season.lower() in stage.lower()) or (crop_group == "Cold-Tolerant" and season == "Spring"):
            st.markdown(f"### {crop_group} – {stage}")
            for v in crops:
                with st.expander(v["name"]):
                    st.image(v["image"], width=100)
                    st.markdown(f"**Experience Level:** {v['level']}")
                    st.markdown(f"**Organic:** {'Yes' if v['organic'] else 'No'}")
                    st.markdown("**Tasks:**")
                    for t in v.get("tasks", []):
                        st.markdown(f"- {t}")
                    st.markdown("**Recurring Care:**")
                    for r in v.get("recurring", []):
                        st.markdown(f"♻️ {r}")
                    st.markdown(f"🔗 [Seed Link]({v['link']})")

# Final tip
st.info("✅ You’ve reached the end of the planner. Be sure to download your layout and calendar before exiting!")
fig, ax = plt.subplots(figsize=(layout_cols, layout_rows))
ax.set_xlim(0, layout_cols)
ax.set_ylim(0, layout_rows)
ax.set_xticks(range(layout_cols+1))
ax.set_yticks(range(layout_rows+1))
ax.grid(True)
ax.invert_yaxis()
for i in range(layout_rows):
    for j in range(layout_cols):
        label = st.session_state.bed_layout[i][j]
        if label:
            ax.text(j+0.5, i+0.5, label[:10], ha='center', va='center', fontsize=6)
plt.tight_layout()
img_buf = io.BytesIO()
plt.savefig(img_buf, format='png')
img_buf.seek(0)
st.download_button("🖼️ Download Garden Layout (PNG)", data=img_buf, file_name="layout.png", mime="image/png")


