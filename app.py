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

sheet = client.open_by_key("191Fg2-jLtpvziqFrUdQNV2ki1iXYe_fdTGYv3_Tm7wA")
pg_sheet = sheet.sheet1

# -----------------------
# SESSION
# -----------------------
if "page" not in st.session_state:
    st.session_state.page = "home"

# -----------------------
# HOME PAGE
# -----------------------
if st.session_state.page == "home":

    st.title("🏠 Verified PGs")
    st.caption("Filters kaadu… reality chupistham")

    data = pg_sheet.get_all_records()

    for pg in data:

        st.subheader(pg["name"])
        st.write(f"📍 {pg['location']}")

        if pg["verified"] == "Yes":
            st.success("✅ Verified by Us")
        else:
            st.warning("Not Verified")

        if st.button(f"View {pg['name']}"):
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

    st.title(pg["name"])
    st.write(f"📍 {pg['location']}")

    if pg["verified"] == "Yes":
        st.success("✅ Verified by Us")
        st.caption("⚠ No Filters • No Editing • Real Capture")

    # -----------------------
    # PARSE CATEGORY IMAGES
    # Format:
    # room1,room2|bath1|food1|dining1|storage1|outside1
    # -----------------------
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

    # -----------------------
    # DISPLAY SECTIONS
    # -----------------------
    show_section("🏠 Room Reality", room)
    show_section("🚿 Bathroom Reality", bathroom)
    show_section("🍛 Food Reality", food)
    show_section("🍽️ Dining Area", dining)
    show_section("🧳 Storage Space", storage)
    show_section("📍 Outside View", outside)

    # -----------------------
    # VIDEOS
    # -----------------------
    st.subheader("🎥 Real Videos")

    for vid in str(pg.get("videos", "")).split(","):
        if vid.startswith("http"):
            st.video(vid)

    # TRUST MESSAGE
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

    # -----------------------
    # ADD PG
    # -----------------------
    st.subheader("➕ Add PG")

    name = st.text_input("PG Name")
    location = st.text_input("Location")
    verified = st.selectbox("Verified", ["Yes", "No"])

    # CATEGORY UPLOADS
    def upload_section(title, key):
        st.subheader(title)
        return st.file_uploader(
            f"{title} Upload",
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
        "🎥 Upload Videos",
        accept_multiple_files=True,
        type=["mp4"],
        key="video"
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

        room_urls = upload_files(room_files)
        bath_urls = upload_files(bath_files)
        food_urls = upload_files(food_files)
        dining_urls = upload_files(dining_files)
        storage_urls = upload_files(storage_files)
        outside_urls = upload_files(outside_files)

        video_urls = upload_videos(video_files)

        # CREATE STRUCTURE
        image_string = "|".join([
            ",".join(room_urls),
            ",".join(bath_urls),
            ",".join(food_urls),
            ",".join(dining_urls),
            ",".join(storage_urls),
            ",".join(outside_urls)
        ])

        pg_sheet.append_row([
            name,
            location,
            verified,
            image_string,
            ",".join(video_urls)
        ])

        st.success("✅ PG Added Successfully!")
        st.rerun()

    st.divider()

    # -----------------------
    # MANAGE PG
    # -----------------------
    st.subheader("📋 Manage PGs")

    data = pg_sheet.get_all_values()
    headers = data[0]
    rows = data[1:]

    for i in range(len(rows)):

        row_index = i + 2
        pg = dict(zip(headers, rows[i]))

        st.write(f"🏠 {pg['name']} - {pg['location']}")
        st.write(f"Verified: {pg['verified']}")

        col1, col2 = st.columns(2)

        if col1.button("❌ Delete", key=f"d{i}"):
            pg_sheet.delete_rows(row_index)
            st.rerun()

        if col2.button("🔄 Toggle Verify", key=f"t{i}"):

            new_status = "No" if pg["verified"] == "Yes" else "Yes"
            pg_sheet.update_cell(row_index, 3, new_status)
            st.rerun()

        st.divider()