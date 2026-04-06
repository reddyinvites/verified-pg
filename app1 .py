import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import cloudinary
import cloudinary.uploader

st.set_page_config(page_title="PG Admin", layout="wide")

# -----------------------
# CONFIG
# -----------------------
cloudinary.config(
    cloud_name=st.secrets["cloudinary"]["cloud_name"],
    api_key=st.secrets["cloudinary"]["api_key"],
    api_secret=st.secrets["cloudinary"]["api_secret"]
)

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

gcp_info = dict(st.secrets["gcp_service_account"])
gcp_info["private_key"] = gcp_info["private_key"].replace("\\n", "\n")

creds = Credentials.from_service_account_info(gcp_info, scopes=scope)
client = gspread.authorize(creds)

# -----------------------
# SHEETS
# -----------------------
PG_DATA_ID = "1y60dTYBKgkOi7J37jtGK4BkkmUoZF8yD4P5J3xA5q6Q"
VERIFIED_ID = "191Fg2-jLtpvziqFrUdQNV2ki1iXYe_fdTGYv3_Tm7wA"

pg_sheet = client.open_by_key(PG_DATA_ID).worksheet("Sheet1")
verified_sheet = client.open_by_key(VERIFIED_ID).worksheet("verified_pg")

# -----------------------
# LOGIN
# -----------------------
st.title("👨‍💼 Admin Panel")

password = st.text_input("Password", type="password")

if password != "1234":
    st.stop()

st.success("✅ Logged in")

# -----------------------
# SIDEBAR
# -----------------------
st.sidebar.title("☰ Menu")
menu = st.sidebar.radio("Go to", ["➕ Add PG", "📋 Manage PGs", "🖼 Gallery"])

# -----------------------
# ADD PG (GROUPED)
# -----------------------
if menu == "➕ Add PG":

    pg_rows = pg_sheet.get_all_values()

    pg_map = {}

    for row in pg_rows[1:]:
        if len(row) >= 3:
            name = row[1].strip()
            location = row[2].strip()

            key = f"{name}|{location}"

            if key not in pg_map:
                pg_map[key] = []

            pg_map[key].append(row)

    options = list(pg_map.keys())

    selected = st.selectbox("Select PG", ["Select PG"] + options)

    if selected == "Select PG":
        st.stop()

    name, location = selected.split("|")

    st.text_input("Name", value=name, disabled=True)
    st.text_input("Location", value=location, disabled=True)

    # ✅ VERIFIED FIX
    verified = st.selectbox("Verified", ["Select", "Yes", "No"], index=0)

    categories = ["room", "bath", "food", "dining", "storage", "outside"]

    category_inputs = {}

    for cat in categories:
        st.subheader(f"📸 {cat.upper()}")
        files = st.file_uploader(cat, accept_multiple_files=True, key=cat)
        category_inputs[cat] = files

    st.subheader("🎥 Videos")
    video_files = st.file_uploader("videos", accept_multiple_files=True)

    # ---------------- SAVE ----------------
    if st.button("💾 Save PG"):

        if verified == "Select":
            st.error("❌ Please select verification status")
            st.stop()

        all_data = verified_sheet.get_all_records()

        row_index = None
        existing_images = ""
        existing_videos = ""

        # 🔍 FIND EXISTING PG
        for i, row in enumerate(all_data):
            if row.get("name") == name and row.get("location") == location:
                row_index = i + 2
                existing_images = str(row.get("images", ""))
                existing_videos = str(row.get("videos", ""))
                break

        category_data = []

        # 📸 UPLOAD IMAGES
        for cat, files in category_inputs.items():
            urls = []
            if files:
                for file in files:
                    res = cloudinary.uploader.upload(file)
                    urls.append(res["secure_url"])

            if urls:
                category_data.append(f"{cat}:{','.join(urls)}")

        new_images = "|".join(category_data)

        # 🎥 UPLOAD VIDEOS
        video_urls = []
        if video_files:
            for file in video_files:
                res = cloudinary.uploader.upload(file, resource_type="video")
                video_urls.append(res["secure_url"])

        new_videos = "|".join(video_urls)

        # 🔗 MERGE FUNCTION
        def merge(old, new):
            if old and new:
                return old + "|" + new
            elif new:
                return new
            else:
                return old

        final_images = merge(existing_images, new_images)
        final_videos = merge(existing_videos, new_videos)

        # ✏️ UPDATE OR ADD
        if row_index:
            verified_sheet.update_cell(row_index, 3, verified)
            verified_sheet.update_cell(row_index, 4, final_images)
            verified_sheet.update_cell(row_index, 5, final_videos)

            st.success("🔄 PG Updated Successfully")

        else:
            verified_sheet.append_row([
                name,
                location,
                verified,
                final_images,
                final_videos
            ])

            st.success("✅ New PG Added")

        st.session_state.clear()
        st.rerun()

# -----------------------
# MANAGE PG
# -----------------------
if menu == "📋 Manage PGs":

    st.header("📋 Manage PGs")

    data = verified_sheet.get_all_records()

    for i, pg in enumerate(data):

        st.subheader(f"🏠 {pg.get('name')}")
        st.write(f"📍 {pg.get('location')}")

        if pg.get("verified") == "Yes":
            st.success("✅ Verified")
        else:
            st.warning("❌ Not Verified")

        col1, col2 = st.columns(2)

        if col1.button("❌ Delete", key=f"delete{i}"):
            verified_sheet.delete_rows(i + 2)
            st.rerun()

        if pg.get("verified") != "Yes":
            if col2.button("🔄 Verify", key=f"verify{i}"):
                verified_sheet.update_cell(i + 2, 3, "Yes")
                st.rerun()

        st.divider()

# -----------------------
# GALLERY
# -----------------------
if menu == "🖼 Gallery":

    st.header("🖼 PG Gallery")

    data = verified_sheet.get_all_records()

    for pg in data:

        st.markdown(f"## 🏠 {pg.get('name')}")
        st.caption(f"📍 {pg.get('location')}")

        images = str(pg.get("images", "")).split("|")

        for block in images:

            if ":" in block:
                try:
                    cat, urls = block.split(":", 1)
                    urls = urls.split(",")

                    st.markdown(f"### 🔹 {cat.upper()}")

                    cols = st.columns(3)

                    for i, img in enumerate(urls):
                        if img.startswith("http"):
                            cols[i % 3].image(img, use_container_width=True)

                except:
                    continue

        # 🎥 VIDEOS
        videos = str(pg.get("videos", "")).split("|")
        valid_videos = [v for v in videos if v.startswith("http")]

        if valid_videos:
            st.markdown("### 🎥 Videos")
            for v in valid_videos:
                st.video(v)

        st.markdown("---")