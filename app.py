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

# ✅ CONNECT TO pg_data → Sheet1
sheet = client.open("pg_data")
pg_sheet = sheet.worksheet("Sheet1")

# -----------------------
# SESSION
# -----------------------
if "page" not in st.session_state:
    st.session_state.page = "home"

# -----------------------
# SAFE DATA FETCH
# -----------------------
def get_pg_data():
    try:
        data_raw = pg_sheet.get_all_values()

        if not data_raw or len(data_raw) < 2:
            return []

        headers = data_raw[0]
        rows = data_raw[1:]

        # ✅ REMOVE EMPTY ROWS
        rows = [r for r in rows if any(cell.strip() for cell in r)]

        return [dict(zip(headers, row)) for row in rows]

    except Exception:
        return []

# -----------------------
# HOME PAGE
# -----------------------
if st.session_state.page == "home":

    st.title("🏠 Verified PGs")
    st.caption("Filters kaadu… reality chupistham")

    data = get_pg_data()

    if not data:
        st.warning("No PG data available")

    for i, pg in enumerate(data):

        st.subheader(pg.get("name", "N/A"))
        st.write(f"📍 {pg.get('location', 'N/A')}")

        if pg.get("verified") == "Yes":
            st.success("✅ Verified by Us")
        else:
            st.warning("Not Verified")

        if st.button(f"View {pg.get('name','PG')}", key=f"view_{i}"):
            st.session_state.pg = pg
            st.session_state.page = "detail"
            st.rerun()

        st.divider()

    if st.button("👨‍💼 Admin"):
        st.session_state.page = "admin"
        st.rerun()

# -----------------------
# DETAIL PAGE
# -----------------------
elif st.session_state.page == "detail":

    pg = st.session_state.pg

    st.title(pg.get("name", "PG"))
    st.write(f"📍 {pg.get('location', '')}")

    if pg.get("verified") == "Yes":
        st.success("✅ Verified by Us")
        st.caption("⚠ No Filters • No Editing • Real Capture")

    raw = str(pg.get("images", ""))
    sections = raw.split("|")
    sections += [""] * (6 - len(sections))

    room = sections[0].split(",")
    bathroom = sections[1].split(",")
    food = sections[2].split(",")
    dining = sections[3].split(",")
    storage = sections[4].split(",")
    outside = sections[5].split(",")

    def show_section(title, items):
        if items and items[0] != "":
            st.subheader(title)
            cols = st.columns(2)
            for i, img in enumerate(items):
                if img.startswith("http"):
                    cols[i % 2].image(img, use_container_width=True)

    show_section("🏠 Room Reality", room)
    show_section("🚿 Bathroom Reality", bathroom)
    show_section("🍛 Food Reality", food)
    show_section("🍽️ Dining Area", dining)
    show_section("🧳 Storage Space", storage)
    show_section("📍 Outside View", outside)

    st.subheader("🎥 Real Videos")

    for vid in str(pg.get("videos", "")).split(","):
        if vid.startswith("http"):
            st.video(vid)

    st.info("👉 What you see = what you get. No surprises.")

    if st.button("⬅ Back"):
        st.session_state.page = "home"
        st.rerun()

# -----------------------
# ADMIN PANEL
# -----------------------
elif st.session_state.page == "admin":

    st.title("👨‍💼 Admin Dashboard")

    password = st.text_input("Password", type="password")

    if password != "1234":
        st.stop()

    st.success("Logged in")

    if st.button("🚪 Logout"):
        st.session_state.clear()
        st.session_state.page = "home"
        st.rerun()

    st.divider()

    # ADD PG
    st.subheader("➕ Add PG")

    name = st.text_input("PG Name")
    location = st.text_input("Location")
    verified = st.selectbox("Verified", ["Yes", "No"])

    def upload_section(title, key):
        st.subheader(title)
        return st.file_uploader(
            title,
            accept_multiple_files=True,
            type=["jpg", "png", "jpeg"],
            key=key
        )

    room_files = upload_section("🏠 Room", "room")
    bath_files = upload_section("🚿 Bathroom", "bath")
    food_files = upload_section("🍛 Food", "food")
    dining_files = upload_section("🍽️ Dining", "dining")
    storage_files = upload_section("🧳 Storage", "storage")
    outside_files = upload_section("📍 Outside", "outside")

    video_files = st.file_uploader(
        "🎥 Videos",
        accept_multiple_files=True,
        type=["mp4"]
    )

    def upload_files(files):
        urls = []
        if files:
            for file in files:
                res = cloudinary.uploader.upload(file)
                urls.append(res["secure_url"])
        return urls

    def upload_videos(files):
        urls = []
        if files:
            for file in files:
                res = cloudinary.uploader.upload(file, resource_type="video")
                urls.append(res["secure_url"])
        return urls

    if st.button("Save PG"):

        image_string = "|".join([
            ",".join(upload_files(room_files)),
            ",".join(upload_files(bath_files)),
            ",".join(upload_files(food_files)),
            ",".join(upload_files(dining_files)),
            ",".join(upload_files(storage_files)),
            ",".join(upload_files(outside_files))
        ])

        video_string = ",".join(upload_videos(video_files))

        pg_sheet.append_row([
            name,
            location,
            verified,
            image_string,
            video_string
        ])

        st.success("✅ PG Added")
        st.rerun()

    st.divider()

    # MANAGE PGs
    st.subheader("📋 Manage PGs")

    data_raw = pg_sheet.get_all_values()

    if len(data_raw) < 2:
        headers = data_raw[0] if data_raw else []
        rows = []
    else:
        headers = data_raw[0]
        rows = data_raw[1:]

    # ✅ REMOVE EMPTY ROWS
    rows = [r for r in rows if any(cell.strip() for cell in r)]

    for i in range(len(rows)):

        pg = dict(zip(headers, rows[i]))

        st.write(f"🏠 {pg.get('name')} - {pg.get('location')}")
        st.write(f"Verified: {pg.get('verified')}")

        col1, col2 = st.columns(2)

        # ✅ DELETE FIX
        if col1.button("❌ Delete", key=f"del_{i}"):
            pg_sheet.delete_rows(i + 2)
            st.success("Deleted!")
            st.rerun()

        # ✅ TOGGLE FIX
        if col2.button("🔄 Toggle Verify", key=f"toggle_{i}"):

            new_status = "No" if pg.get("verified") == "Yes" else "Yes"
            pg_sheet.update_cell(i + 2, 3, new_status)
            st.rerun()

        st.divider()