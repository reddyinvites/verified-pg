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
menu = st.sidebar.radio("Go to", ["➕ Add PG", "📂 Albums", "📋 Manage PGs"])

# -----------------------
# SAFE READ
# -----------------------
def get_verified_data():
    try:
        data = verified_sheet.get_all_values()
        if not data:
            return []
        headers = data[0]
        rows = data[1:]
        return [dict(zip(headers, r)) for r in rows]
    except:
        return []

# -----------------------
# ADD PG
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

    selected = st.selectbox("Select PG", ["Select PG"] + list(pg_map.keys()))

    if selected == "Select PG":
        st.stop()

    name, location = selected.split("|")

    st.text_input("Name", value=name, disabled=True)
    st.text_input("Location", value=location, disabled=True)

    verified = st.selectbox("Verified", ["Select", "Yes", "No"])

    st.info("📌 Upload best sample photos only")

    MAX_FILES = 5
    categories = ["room", "bath", "food", "dining", "storage", "outside"]

    category_inputs = {}
    video_inputs = {}

    for cat in categories:
        st.subheader(f"📸 {cat.upper()}")

        files = st.file_uploader(cat, accept_multiple_files=True, key=cat)

        if files and len(files) > MAX_FILES:
            st.error("Max 5 images")
            st.stop()

        if files:
            cols = st.columns(4)
            for i, f in enumerate(files):
                with cols[i % 4]:
                    st.image(f)

        category_inputs[cat] = files

        # 🎥 video per category
        vids = st.file_uploader(f"{cat} video (1 max)", key=f"vid_{cat}")

        video_inputs[cat] = vids

    # SAVE
    if st.button("💾 Save PG"):

        if verified == "Select":
            st.error("Select verification")
            st.stop()

        all_data = get_verified_data()

        row_index = None
        old_img = ""
        old_vid = ""

        for i, r in enumerate(all_data):
            if r.get("name") == name and r.get("location") == location:
                row_index = i + 2
                old_img = r.get("images", "")
                old_vid = r.get("videos", "")
                break

        img_data = []
        vid_data = []

        # upload images
        for cat, files in category_inputs.items():
            urls = []
            if files:
                for f in files:
                    res = cloudinary.uploader.upload(f)
                    urls.append(res["secure_url"])
            if urls:
                img_data.append(f"{cat}:{','.join(urls)}")

        # upload videos
        for cat, file in video_inputs.items():
            if file:
                res = cloudinary.uploader.upload(file, resource_type="video")
                vid_data.append(f"{cat}:{res['secure_url']}")

        def merge(a, b):
            return f"{a}|{b}" if a and b else b or a

        final_img = merge(old_img, "|".join(img_data))
        final_vid = merge(old_vid, "|".join(vid_data))

        if row_index:
            verified_sheet.update_cell(row_index, 3, verified)
            verified_sheet.update_cell(row_index, 4, final_img)
            verified_sheet.update_cell(row_index, 5, final_vid)
            st.success("Updated")
        else:
            verified_sheet.append_row([name, location, verified, final_img, final_vid])
            st.success("Added")

        st.rerun()

# -----------------------
# ALBUM VIEW
# -----------------------
if menu == "📂 Albums":

    st.header("📂 PG Albums")

    data = get_verified_data()

    for pg in data:

        st.subheader(pg.get("name"))
        st.caption(pg.get("location"))

        album = {}

        # images
        for block in str(pg.get("images", "")).split("|"):
            if ":" in block:
                cat, urls = block.split(":")
                album.setdefault(cat, []).extend(urls.split(","))

        # videos
        vid_map = {}
        for block in str(pg.get("videos", "")).split("|"):
            if ":" in block:
                cat, url = block.split(":")
                vid_map.setdefault(cat, []).append(url)

        cols = st.columns(3)

        for i, (cat, imgs) in enumerate(album.items()):
            if imgs:
                with cols[i % 3]:
                    if st.button(f"{cat.upper()} ({len(imgs)})", key=f"{cat}_{i}"):
                        st.session_state["album"] = cat
                        st.session_state["imgs"] = imgs
                        st.session_state["vids"] = vid_map.get(cat, [])

                    st.image(imgs[0])

        # open album
        if "album" in st.session_state:

            st.markdown("---")
            st.subheader(st.session_state["album"].upper())

            cols = st.columns(3)
            for i, img in enumerate(st.session_state["imgs"]):
                with cols[i % 3]:
                    st.image(img)

            if st.session_state["vids"]:
                st.markdown("### 🎥 Videos")
                for v in st.session_state["vids"]:
                    st.video(v)

            if st.button("🔙 Back"):
                st.session_state.clear()
                st.rerun()

# -----------------------
# MANAGE
# -----------------------
if menu == "📋 Manage PGs":

    st.header("Manage PGs")

    data = get_verified_data()

    for i, pg in enumerate(data):

        st.write(pg.get("name"))

        if st.button("Delete", key=i):
            verified_sheet.delete_rows(i + 2)
            st.rerun()