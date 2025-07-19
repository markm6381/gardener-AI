# Beginner Gardener AI – Fully Rebuilt and Deployable on Streamlit Cloud

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import qrcode
import io
from datetime import datetime

st.set_page_config(page_title="Beginner Gardener AI", layout="wide")
st.title("🌿 Beginner Gardener AI Planner")

# Frost date lookup fallback
def get_estimated_last_frost(zip_code):
    return datetime(datetime.today().year, 3, 15)

# Sample data
spacing_guide = {
    "Tomato": "18–24 in",
    "Spinach": "6 in",
    "Okra": "12–18 in"
}

container_guide = {
    "Tomato": "5-gallon pot",
    "Spinach": "6-inch pot",
    "Okra": "5-gallon pot"
}

companion_guide = {
    "Tomato": ["Basil", "Marigold"],
    "Spinach": ["Radish"],
    "Okra": ["Peppers"]
}

variety_guide = {
    "Warm-Season": {
        "Summer": [
            {"name": "Tomato", "level": "Beginner", "image": "https://via.placeholder.com/100", "organic": True,
             "tasks": ["Start indoors in Jan", "Transplant after frost"], "recurring": ["Fertilize every 2 weeks"]},
            {"name": "Okra", "level": "Beginner", "image": "https://via.placeholder.com/100", "organic": False,
             "tasks": ["Direct sow after frost"], "recurring": ["Harvest every 2–3 days"]}
        ]
    },
    "Cold-Tolerant": {
        "Early": [
            {"name": "Spinach", "level": "Beginner", "image": "https://via.placeholder.com/100", "organic": True,
             "tasks": ["Direct sow in cool soil"], "recurring": ["Water every 3 days"]}
        ]
    }
}

# Garden layout
layout_rows, layout_cols = 4, 6
if "bed_layout" not in st.session_state:
    st.session_state.bed_layout = [["" for _ in range(layout_cols)] for _ in range(layout_rows)]

selected_crop = st.selectbox("Select a crop to place:", [v["name"] for cat in variety_guide.values() for stage in cat.values() for v in stage])

for i in range(layout_rows):
    cols = st.columns(layout_cols)
    for j in range(layout_cols):
        label = st.session_state.bed_layout[i][j] or "[Empty]"
        if cols[j].button(label, key=f"bed_{i}_{j}"):
            st.session_state.bed_layout[i][j] = selected_crop

if st.button("🧹 Clear Layout"):
    st.session_state.bed_layout = [["" for _ in range(layout_cols)] for _ in range(layout_rows)]

bed_df = pd.DataFrame(st.session_state.bed_layout)
st.dataframe(bed_df)

# --- Seasonal Crop Preview with Filters ---

level_filter = st.selectbox("Filter by experience level:", ["All", "Beginner"])
organic_filter = st.checkbox("Only show organic varieties")

st.subheader("🌿 Seasonal Crop Preview")
current_month = datetime.today().month
season = "Spring" if current_month in [1, 2, 3, 4, 5] else "Summer" if current_month in [6, 7, 8] else "Fall"

for crop_group, stages in variety_guide.items():
    for stage_name, crops in stages.items():
        if season.lower() in stage_name.lower():
            st.markdown(f"### {crop_group} – {stage_name}")
            for v in crops:
                if organic_filter and not v.get("organic"):
                    continue
                if level_filter != "All" and v.get("level") != level_filter:
                    continue

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
    

# Container crops
st.subheader("🪴 Container Gardening")
selected_container = st.selectbox("Choose container crop:", list(container_guide.keys()))
spacing = spacing_guide.get(selected_container, "N/A")
container_size = container_guide.get(selected_container, "N/A")
companions = companion_guide.get(selected_container, [])

st.markdown(f"📦 **Container Size:** {container_size}")
st.markdown(f"📏 **Spacing:** {spacing}")
st.markdown(f"🌼 **Companions:** {', '.join(companions)}")

for cat in variety_guide.values():
    for stage in cat.values():
        for v in stage:
            if v["name"] == selected_container:
                st.image(v["image"], width=100)
                st.markdown("**Tasks:**")
                for t in v.get("tasks", []):
                    st.markdown(f"- {t}")
                st.markdown("**Recurring Care:**")
                for r in v.get("recurring", []):
                    st.markdown(f"♻️ {r}")

# Export garden layout as PNG
fig, ax = plt.subplots(figsize=(layout_cols, layout_rows))
ax.set_xlim(0, layout_cols)
ax.set_ylim(0, layout_rows)
ax.set_xticks(range(layout_cols + 1))
ax.set_yticks(range(layout_rows + 1))
ax.grid(True)
ax.invert_yaxis()

for i in range(layout_rows):
    for j in range(layout_cols):
        crop = st.session_state.bed_layout[i][j]
        if crop:
            ax.text(j + 0.5, i + 0.5, crop[:10], ha="center", va="center", fontsize=6)

plt.tight_layout()
buffer = io.BytesIO()
plt.savefig(buffer, format="png")
buffer.seek(0)

st.download_button("🖼️ Download Garden Layout (PNG)", data=buffer, file_name="bed_layout.png", mime="image/png")

st.info("✅ Planner ready for deployment on Streamlit Cloud.")

# --- Mini Export Buttons ---
st.subheader("📋 Export Crops as CSV")
data_rows = []
for group, stages in variety_guide.items():
    for stage, crops in stages.items():
        for v in crops:
            if organic_filter and not v.get("organic"):
                continue
            if level_filter != "All" and v.get("level") != level_filter:
                continue
            data_rows.append({
                "Crop": v["name"],
                "Group": group,
                "Season": stage,
                "Organic": "Yes" if v["organic"] else "No",
                "Level": v["level"]
            })

if data_rows:
    df_export = pd.DataFrame(data_rows)
    csv = df_export.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Download Crop List (CSV)", data=csv, file_name="crops_filtered.csv", mime="text/csv")
