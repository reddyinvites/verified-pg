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
# MENU
# -----------------------
menu = st.sidebar.radio("Menu", ["➕ Add PG", "📂 Albums", "📋 Manage"])

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

    options = list(set([f"{r[1]}|{r[2]}" for r in pg_rows[1:] if len(r) >= 3]))

    selected = st.selectbox("Select PG", ["Select"] + options)

    if selected == "Select":
        st.stop()

    name, location = selected.split("|")

    st.text_input("Name", value=name, disabled=True)
    st.text_input("Location", value=location, disabled=True)

    verified = st.selectbox("Verified", ["Select", "Yes", "No"])

    categories = ["room", "bath", "food", "dining", "storage", "outside"]

    img_inputs = {}
    vid_inputs = {}

    for cat in categories:
        st.subheader(cat.upper())

        imgs = st.file_uploader(cat, accept_multiple_files=True, key=cat)
        img_inputs[cat] = imgs

        vid = st.file_uploader(f"{cat} video", key=f"v_{cat}")
        vid_inputs[cat] = vid

    if st.button("Save"):

        if verified == "Select":
            st.error("Select verification")
            st.stop()

        data = get_verified_data()

        row_index = None
        old_img = ""
        old_vid = ""

        for i, r in enumerate(data):
            if r.get("name") == name:
                row_index = i + 2
                old_img = r.get("images", "")
                old_vid = r.get("videos", "")
                break

        img_data = []
        vid_data = []

        # upload images
        for cat, files in img_inputs.items():
            urls = []
            if files:
                for f in files:
                    res = cloudinary.uploader.upload(f)
                    urls.append(res["secure_url"])
            if urls:
                img_data.append(f"{cat}:{','.join(urls)}")

        # upload videos
        for cat, file in vid_inputs.items():
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
        else:
            verified_sheet.append_row([name, location, verified, final_img, final_vid])

        st.success("Saved")
        st.rerun()

# -----------------------
# ALBUMS
# -----------------------
if menu == "📂 Albums":

    st.header("📂 PG Albums")

    data = get_verified_data()

    for pg in data:

        st.subheader(pg.get("name"))
        st.caption(pg.get("location"))

        album = {}
        videos = {}

        # SAFE IMAGE PARSE
        for block in str(pg.get("images", "")).split("|"):

            if not block.strip():
                continue

            parts = block.split(":", 1)

            if len(parts) != 2:
                continue

            cat, urls = parts
            urls = [u for u in urls.split(",") if u.startswith("http")]

            album.setdefault(cat, []).extend(urls)

        # SAFE VIDEO PARSE
        for block in str(pg.get("videos", "")).split("|"):

            if not block.strip():
                continue

            parts = block.split(":", 1)

            if len(parts) != 2:
                continue

            cat, url = parts

            if url.startswith("http"):
                videos.setdefault(cat, []).append(url)

        cols = st.columns(3)

        for i, (cat, imgs) in enumerate(album.items()):
            if imgs:
                with cols[i % 3]:
                    if st.button(f"{cat.upper()} ({len(imgs)})", key=f"{cat}_{i}"):

                        st.session_state["cat"] = cat
                        st.session_state["imgs"] = imgs
                        st.session_state["vids"] = videos.get(cat, [])

                    st.image(imgs[0])

        # OPEN ALBUM
        if "cat" in st.session_state:

            st.markdown("---")
            st.subheader(st.session_state["cat"].upper())

            cols = st.columns(3)

            for i, img in enumerate(st.session_state["imgs"]):
                with cols[i % 3]:
                    st.image(img)

            if st.session_state["vids"]:
                st.markdown("🎥 Videos")
                for v in st.session_state["vids"]:
                    st.video(v)

            if st.button("Back"):
                st.session_state.clear()
                st.rerun()

# -----------------------
# MANAGE
# -----------------------
if menu == "📋 Manage":

    data = get_verified_data()

    for i, pg in enumerate(data):
        st.write(pg.get("name"))

        if st.button("Delete", key=i):
            verified_sheet.delete_rows(i + 2)
            st.rerun()