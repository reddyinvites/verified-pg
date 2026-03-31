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

# MAIN SHEET
sheet = client.open_by_key("1y60dTYBKgkOi7J37jtGK4BkkmUoZF8yD4P5J3xA5q6Q")
pg_sheet = sheet.sheet1

# VERIFIED SHEET
verified_sheet = client.open("verified_pg").sheet1

# -----------------------
# SESSION
# -----------------------
if "page" not in st.session_state:
    st.session_state.page = "home"

# -----------------------
# SAFE DATA
# -----------------------
def get_pg_data():
    try:
        data_raw = pg_sheet.get_all_values()

        if not data_raw or len(data_raw) < 2:
            return []

        headers = data_raw[0]
        rows = data_raw[1:]
        rows = [r for r in rows if len(r) >= 3 and r[0].strip()]

        return [dict(zip(headers, row)) for row in rows]

    except:
        return []

# -----------------------
# HOME
# -----------------------
if st.session_state.page == "home":

    st.title("🏠 Verified PGs")
    st.caption("Filters kaadu… reality chupistham")

    data = get_pg_data()

    for i, pg in enumerate(data):

        name = pg.get("name", "")
        location = pg.get("location", "")
        verified = pg.get("verified", "")

        st.subheader(name)
        st.write(f"📍 {location}")

        if verified == "Yes":
            st.success("✅ Verified by Us")
        else:
            st.warning("Not Verified")

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
        st.caption("⚠ No Filters • No Editing • Real Capture")

    raw = str(pg.get("images", ""))
    sections = raw.split("|")
    sections += [""] * (6 - len(sections))

    def show_section(title, items):
        if items and items[0]:
            st.subheader(title)
            cols = st.columns(2)
            for i, img in enumerate(items):
                if img.startswith("http"):
                    cols[i % 2].image(img, use_container_width=True)

    show_section("🏠 Room", sections[0].split(","))
    show_section("🚿 Bathroom", sections[1].split(","))
    show_section("🍛 Food", sections[2].split(","))
    show_section("🍽️ Dining", sections[3].split(","))
    show_section("🧳 Storage", sections[4].split(","))
    show_section("📍 Outside", sections[5].split(","))

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

    # ADD PG
    st.subheader("Add PG")

    name = st.text_input("Name")
    location = st.text_input("Location")
    verified = st.selectbox("Verified", ["Yes", "No"])

    def upload(key):
        return st.file_uploader(key, accept_multiple_files=True, key=key)

    room = upload("room")
    bath = upload("bath")
    food = upload("food")
    dining = upload("dining")
    storage = upload("storage")
    outside = upload("outside")

    videos = st.file_uploader("videos", accept_multiple_files=True)

    def up(files, video=False):
        urls = []
        if files:
            for f in files:
                res = cloudinary.uploader.upload(
                    f, resource_type="video" if video else "image"
                )
                urls.append(res["secure_url"])
        return urls

    # ✅ FIXED SAVE
    if st.button("Save PG"):

        if not name.strip() or not location.strip():
            st.error("Enter name & location")
            st.stop()

        def safe_join(files):
            return ",".join(up(files)) if files else ""

        image_string = "|".join([
            safe_join(room),
            safe_join(bath),
            safe_join(food),
            safe_join(dining),
            safe_join(storage),
            safe_join(outside)
        ])

        video_string = ",".join(up(videos, True)) if videos else ""

        new_row = [""] * 5
        new_row[0] = name.strip()
        new_row[1] = location.strip()
        new_row[2] = verified
        new_row[3] = image_string
        new_row[4] = video_string

        pg_sheet.append_row(new_row)

        if verified == "Yes":
            verified_sheet.append_row(new_row)

        st.success("Saved correctly ✅")
        st.rerun()

    # -----------------------
    # MANAGE PGs
    # -----------------------
    st.subheader("📋 Manage PGs")

    data_raw = pg_sheet.get_all_values()

    headers = data_raw[0] if data_raw else []
    rows = data_raw[1:] if len(data_raw) > 1 else []

    rows = [r for r in rows if len(r) >= 3 and r[0].strip()]

    for i in range(len(rows)):

        row = rows[i]

        name = row[0].strip() if len(row) > 0 else ""
        location = row[1].strip() if len(row) > 1 else ""
        verified = row[2].strip() if len(row) > 2 else "No"

        if not name:
            continue

        st.markdown(f"### 🏠 {name}")
        st.write(f"📍 {location}")

        if verified == "Yes":
            st.success("✅ Verified")
        else:
            st.warning("❌ Not Verified")

        col1, col2 = st.columns(2)

        if col1.button("❌ Delete", key=f"del_{i}"):
            pg_sheet.delete_rows(i + 2)
            st.rerun()

        if col2.button("🔄 Toggle Verify", key=f"toggle_{i}"):

            new_status = "No" if verified == "Yes" else "Yes"
            pg_sheet.update_cell(i + 2, 3, new_status)

            rows[i][2] = new_status

            if new_status == "Yes":
                verified_sheet.append_row(row)

            st.success(f"Now: {new_status}")
            st.rerun()

        st.divider()