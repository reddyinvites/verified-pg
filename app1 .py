import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import cloudinary
import cloudinary.uploader

st.set_page_config(page_title="PG Admin", layout="wide")

# ---------------- CONFIG ----------------
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

PG_DATA_ID = "1y60dTYBKgkOi7J37jtGK4BkkmUoZF8yD4P5J3xA5q6Q"
VERIFIED_ID = "191Fg2-jLtpvziqFrUdQNV2ki1iXYe_fdTGYv3_Tm7wA"

pg_sheet = client.open_by_key(PG_DATA_ID).worksheet("Sheet1")
verified_sheet = client.open_by_key(VERIFIED_ID).worksheet("verified_pg")

# ---------------- LOGIN ----------------
st.title("👨‍💼 Admin Panel")

password = st.text_input("Password", type="password")
if password != "1234":
    st.stop()

st.success("✅ Logged in")

menu = st.sidebar.radio("Menu", ["➕ Add PG", "📂 Gallery", "📋 Manage"])

# ---------------- SAFE READ ----------------
def get_data():
    try:
        data = verified_sheet.get_all_values()
        if not data:
            return []
        headers = data[0]
        return [dict(zip(headers, r)) for r in data[1:]]
    except:
        return []

# ---------------- ADD PG ----------------
if menu == "➕ Add PG":

    rows = pg_sheet.get_all_values()
    options = list(set([f"{r[1]}|{r[2]}" for r in rows[1:] if len(r) >= 3]))

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

    MAX_IMAGES = 6
    MAX_VIDEOS_PER_CAT = 2

    for cat in categories:
        st.subheader(cat.upper())

        imgs = st.file_uploader(cat, accept_multiple_files=True, key=cat)

        if imgs and len(imgs) > MAX_IMAGES:
            st.error(f"Max {MAX_IMAGES} images allowed")
            st.stop()

        img_inputs[cat] = imgs

        vids = st.file_uploader(f"{cat} videos", accept_multiple_files=True, key=f"v_{cat}")

        if vids and len(vids) > MAX_VIDEOS_PER_CAT:
            st.error("Max 2 videos per category")
            st.stop()

        vid_inputs[cat] = vids

    if st.button("Save"):

        if verified == "Select":
            st.error("Select verification")
            st.stop()

        data = get_data()

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

        # Upload images
        for cat, files in img_inputs.items():
            urls = []
            if files:
                for f in files:
                    res = cloudinary.uploader.upload(f)
                    urls.append(res["secure_url"])
            if urls:
                img_data.append(f"{cat}:{','.join(urls)}")

        # Upload videos
        for cat, files in vid_inputs.items():
            if files:
                urls = []
                for f in files:
                    res = cloudinary.uploader.upload(f, resource_type="video")
                    urls.append(res["secure_url"])
                if urls:
                    vid_data.append(f"{cat}:{','.join(urls)}")

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

# ---------------- GALLERY ----------------
if menu == "📂 Gallery":

    st.header("📂 PG Gallery")

    data = get_data()

    view = st.selectbox("View Mode", ["📂 Albums View", "🖼 All Photos View"])

    for pg in data:

        st.subheader(pg.get("name"))
        st.caption(pg.get("location"))

        images_raw = str(pg.get("images", "")).split("|")
        videos_raw = str(pg.get("videos", "")).split("|")

        # -------- ALL PHOTOS VIEW --------
        if view == "🖼 All Photos View":

            all_imgs = []

            for block in images_raw:
                parts = block.split(":", 1)
                if len(parts) == 2:
                    for u in parts[1].split(","):
                        if u.startswith("http"):
                            all_imgs.append(u)

            all_imgs = list(dict.fromkeys(all_imgs))

            cols = st.columns(3)
            for i, img in enumerate(all_imgs):
                with cols[i % 3]:
                    st.image(img, use_container_width=True)

        # -------- ALBUM VIEW --------
        else:

            album = {}
            videos = {}

            for block in images_raw:
                parts = block.split(":", 1)
                if len(parts) == 2:
                    cat, urls = parts
                    album.setdefault(cat, []).extend([u for u in urls.split(",") if u.startswith("http")])

            for block in videos_raw:
                parts = block.split(":", 1)
                if len(parts) == 2:
                    cat, urls = parts
                    videos.setdefault(cat, []).extend([u for u in urls.split(",") if u.startswith("http")])

            categories_list = list(album.keys())

            cols = st.columns(3)

            for i, (cat, imgs) in enumerate(album.items()):
                if imgs:
                    with cols[i % 3]:

                        if st.button(f"{cat.upper()} ({len(imgs)})", key=f"{cat}_{i}"):

                            st.session_state["view_mode"] = "album"
                            st.session_state["current_index"] = i
                            st.session_state["categories"] = categories_list
                            st.session_state["album"] = album
                            st.session_state["videos"] = videos

                        st.image(imgs[0], use_container_width=True)

            # -------- OPEN ALBUM --------
            if st.session_state.get("view_mode") == "album":

                cats = st.session_state["categories"]
                idx = st.session_state["current_index"]

                cat = cats[idx]
                imgs = st.session_state["album"].get(cat, [])
                vids = st.session_state["videos"].get(cat, [])

                st.markdown("---")
                st.subheader(f"📸 {cat.upper()}")

                cols = st.columns(3)
                for i, img in enumerate(imgs):
                    with cols[i % 3]:
                        st.image(img, use_container_width=True)

                if vids:
                    st.markdown("### 🎥 Videos")
                    for v in vids:
                        st.video(v)

                col1, col2, col3 = st.columns(3)

                with col1:
                    if st.button("⬅ Back"):
                        st.session_state.clear()
                        st.rerun()

                with col2:
                    if idx > 0:
                        if st.button("⬅ Previous"):
                            st.session_state["current_index"] -= 1
                            st.rerun()

                with col3:
                    if idx < len(cats) - 1:
                        if st.button("Next ➡"):
                            st.session_state["current_index"] += 1
                            st.rerun()

# ---------------- MANAGE ----------------
if menu == "📋 Manage":

    data = get_data()

    for i, pg in enumerate(data):
        st.write(pg.get("name"))

        if st.button("Delete", key=i):
            verified_sheet.delete_rows(i + 2)
            st.rerun()