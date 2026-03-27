import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import uuid

# -----------------------
# SESSION
# -----------------------
if "page" not in st.session_state:
    st.session_state.page = "home"

if "selected_pg" not in st.session_state:
    st.session_state.selected_pg = None

if "admin_logged" not in st.session_state:
    st.session_state.admin_logged = False

# -----------------------
# GOOGLE SHEETS
# -----------------------
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

gcp_info = dict(st.secrets["gcp_service_account"])
gcp_info["private_key"] = gcp_info["private_key"].replace("\\n", "\n")

creds = Credentials.from_service_account_info(gcp_info, scopes=scope)
client = gspread.authorize(creds)

sheet = client.open_by_key("YOUR_SHEET_ID")
pg_sheet = sheet.sheet1

# -----------------------
# HOME
# -----------------------
if st.session_state.page == "home":

    st.title("🏠 Verified PGs")
    st.write("No filters. No fake photos. Only reality.")

    data = pg_sheet.get_all_records()

    for i, pg in enumerate(data):

        st.subheader(pg["name"])
        st.write(f"📍 {pg['location']}")

        if pg.get("verified") == "Yes":
            st.success("✅ Verified by Us")

        if st.button("View Details", key=f"view{i}"):
            st.session_state.selected_pg = pg
            st.session_state.page = "detail"
            st.rerun()

        st.divider()

    col1, col2 = st.columns(2)

    if col1.button("👤 User"):
        st.session_state.page = "home"

    if col2.button("👨‍💼 Admin"):
        st.session_state.page = "admin"
        st.rerun()

# -----------------------
# PG DETAIL PAGE
# -----------------------
elif st.session_state.page == "detail":

    pg = st.session_state.selected_pg

    st.title(pg["name"])
    st.write(f"📍 {pg['location']}")

    st.success("✅ Verified by Us")

    # IMAGES
    st.subheader("📸 Real Images")
    images = pg.get("images", "").split(",")

    for img in images:
        if img:
            st.image(img)

    # VIDEOS
    st.subheader("🎥 Video")
    videos = pg.get("videos", "").split(",")

    for vid in videos:
        if vid:
            st.video(vid)

    st.markdown("""
    ✔ Real room  
    ✔ Bathroom reality  
    ✔ Food  
    ✔ Dining  
    ✔ Storage  
    ✔ Outside view  
    """)

    if st.button("⬅ Back"):
        st.session_state.page = "home"
        st.rerun()

# -----------------------
# ADMIN PANEL
# -----------------------
elif st.session_state.page == "admin":

    st.title("👨‍💼 Admin Dashboard")

    password = st.text_input("Password", type="password")

    if password == "1234":
        st.session_state.admin_logged = True

    if not st.session_state.admin_logged:
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

    # IMAGE UPLOAD
    uploaded_images = st.file_uploader(
        "Upload Images",
        accept_multiple_files=True,
        type=["jpg", "png", "jpeg"]
    )

    # VIDEO UPLOAD
    uploaded_videos = st.file_uploader(
        "Upload Videos",
        accept_multiple_files=True,
        type=["mp4"]
    )

    if st.button("Save PG"):

        image_urls = []
        video_urls = []

        # 🔥 TEMP STORAGE (Streamlit Cloud)
        for img in uploaded_images:
            path = f"images/{uuid.uuid4()}.png"
            with open(path, "wb") as f:
                f.write(img.read())
            image_urls.append(path)

        for vid in uploaded_videos:
            path = f"videos/{uuid.uuid4()}.mp4"
            with open(path, "wb") as f:
                f.write(vid.read())
            video_urls.append(path)

        pg_sheet.append_row([
            name,
            location,
            verified,
            ",".join(image_urls),
            ",".join(video_urls)
        ])

        st.success("PG Added!")
        st.rerun()

    st.divider()

    # -----------------------
    # MANAGE PG
    # -----------------------
    st.subheader("📋 Manage PGs")

    data = pg_sheet.get_all_records()

    for i, pg in enumerate(data):

        st.write(f"{pg['name']} - {pg['location']}")

        col1, col2 = st.columns(2)

        if col1.button("❌ Delete", key=f"d{i}"):
            pg_sheet.delete_rows(i + 2)
            st.rerun()

        if col2.button("Toggle Verify", key=f"v{i}"):
            new = "No" if pg["verified"] == "Yes" else "Yes"
            pg_sheet.update_cell(i + 2, 3, new)
            st.rerun()

        st.divider()