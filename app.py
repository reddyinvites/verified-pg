import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import cloudinary
import cloudinary.uploader

# -----------------------
# CONFIG
# -----------------------
st.set_page_config(page_title="Verified PGs", layout="wide")

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
sheet = client.open_by_key("1y60dTYBKgkOi7J37jtGK4BkkmUoZF8yD4P5J3xA5q6Q")
pg_sheet = sheet.sheet1

verified_sheet = client.open("verified_pg").sheet1

# -----------------------
# SESSION
# -----------------------
if "page" not in st.session_state:
    st.session_state.page = "home"

# -----------------------
# SYNC VERIFIED
# -----------------------
def sync_verified_pg():
    try:
        data = pg_sheet.get_all_values()
        if len(data) < 2:
            return

        headers = data[0]
        rows = data[1:]

        verified_sheet.clear()
        verified_sheet.append_row(headers)

        for row in rows:
            if len(row) >= 3 and row[2].strip() == "Yes":
                verified_sheet.append_row(row)

    except Exception as e:
        st.warning(f"Sync error: {e}")

# -----------------------
# HOME
# -----------------------
if st.session_state.page == "home":

    st.title("🏠 Verified PGs")

    try:
        data = verified_sheet.get_all_records()
    except:
        data = []

    for i, pg in enumerate(data):

        name = pg.get("name", "")
        location = pg.get("location", "")

        st.subheader(f"🏠 {name}")
        st.write(f"📍 {location}")

        if st.button(f"View {name}", key=f"view_{i}"):
            st.session_state.pg = pg
            st.session_state.page = "detail"
            st.rerun()

        st.divider()

    if st.button("👨‍💼 Admin"):
        st.session_state.page = "admin"
        st.rerun()

# -----------------------
# DETAIL
# -----------------------
elif st.session_state.page == "detail":

    pg = st.session_state.pg

    st.title(pg.get("name", "PG"))
    st.write(f"📍 {pg.get('location', '')}")

    if pg.get("verified") == "Yes":
        st.success("✅ Verified by Us")

    # images
    raw = str(pg.get("images", ""))
    sections = raw.split("|")
    sections += [""] * (6 - len(sections))

    titles = ["🏠 Room", "🚿 Bathroom", "🍛 Food", "🍽️ Dining", "🧳 Storage", "📍 Outside"]

    for idx, sec in enumerate(sections):
        imgs = sec.split(",")
        if imgs and imgs[0]:
            st.subheader(titles[idx])
            cols = st.columns(2)
            for i, img in enumerate(imgs):
                if img.startswith("http"):
                    cols[i % 2].image(img, use_container_width=True)

    # videos
    for vid in str(pg.get("videos", "")).split(","):
        if vid.startswith("http"):
            st.video(vid)

    if st.button("⬅ Back"):
        st.session_state.page = "home"
        st.rerun()

# -----------------------
# ADMIN
# -----------------------
elif st.session_state.page == "admin":

    st.title("👨‍💼 Admin")

    if st.text_input("Password", type="password") != "1234":
        st.stop()

    st.success("Logged in")

    if st.button("Logout"):
        st.session_state.clear()
        st.session_state.page = "home"
        st.rerun()

    # -----------------------
    # ADD PG
    # -----------------------
    st.subheader("Add PG")

    name = st.text_input("Name")
    location = st.text_input("Location")
    verified = st.selectbox("Verified", ["Yes", "No"])

    def uploader(key):
        return st.file_uploader(key, accept_multiple_files=True, key=key)

    room = uploader("room")
    bath = uploader("bath")
    food = uploader("food")
    dining = uploader("dining")
    storage = uploader("storage")
    outside = uploader("outside")
    videos = st.file_uploader("videos", accept_multiple_files=True)

    # -----------------------
    # SAVE (FIXED)
    # -----------------------
    if st.button("Save PG"):

        if not name.strip() or not location.strip():
            st.error("Enter name & location")
            st.stop()

        # STEP 1: SAVE BASIC DATA
        pg_sheet.append_row([name, location, verified, "", ""])
        row_index = len(pg_sheet.get_all_values())

        # STEP 2: UPLOAD
        def upload(files, video=False):
            urls = []
            if files:
                for f in files:
                    try:
                        res = cloudinary.uploader.upload(
                            f, resource_type="video" if video else "image"
                        )
                        urls.append(res["secure_url"])
                    except:
                        pass
            return ",".join(urls)

        image_string = "|".join([
            upload(room),
            upload(bath),
            upload(food),
            upload(dining),
            upload(storage),
            upload(outside)
        ])

        video_string = upload(videos, True)

        # STEP 3: UPDATE SHEET
        pg_sheet.update_cell(row_index, 4, image_string)
        pg_sheet.update_cell(row_index, 5, video_string)

        # STEP 4: SYNC VERIFIED
        sync_verified_pg()

        st.success("✅ Saved Successfully!")
        st.rerun()

    # -----------------------
    # MANAGE PGs
    # -----------------------
    st.subheader("📋 Manage PGs")

    data = pg_sheet.get_all_values()
    rows = data[1:]

    for i, row in enumerate(rows):

        if len(row) < 3 or not row[0].strip():
            continue

        name = row[0]
        location = row[1]
        verified = row[2]

        st.markdown(f"### 🏠 {name}")
        st.write(f"📍 {location}")

        if verified == "Yes":
            st.success("✅ Verified")
        else:
            st.warning("❌ Not Verified")

        col1, col2 = st.columns(2)

        if col1.button("❌ Delete", key=f"d{i}"):
            pg_sheet.delete_rows(i + 2)
            sync_verified_pg()
            st.rerun()

        if col2.button("🔄 Toggle Verify", key=f"t{i}"):

            new = "No" if verified == "Yes" else "Yes"
            pg_sheet.update_cell(i + 2, 3, new)

            sync_verified_pg()
            st.rerun()

        st.divider()