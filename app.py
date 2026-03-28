import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

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
# GOOGLE SHEETS (FIXED)
# -----------------------
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

gcp_info = dict(st.secrets["gcp_service_account"])
gcp_info["private_key"] = gcp_info["private_key"].replace("\\n", "\n")

creds = Credentials.from_service_account_info(gcp_info, scopes=scope)
client = gspread.authorize(creds)

# ✅ YOUR REAL SHEET ID
sheet = client.open_by_key("191Fg2-jLtpvziqFrUdQNV2ki1iXYe_fdTGYv3_Tm7wA")

pg_sheet = sheet.sheet1

# -----------------------
# HOME PAGE
# -----------------------
if st.session_state.page == "home":

    st.title("🏠 Verified PGs")
    st.write("No filters. No fake photos. Only reality.")

    data = pg_sheet.get_all_records()

    for i, pg in enumerate(data):

        st.subheader(pg.get("name", "No Name"))
        st.write(f"📍 {pg.get('location', '')}")

        if pg.get("verified") == "Yes":
            st.success("✅ Verified by Us")

        if st.button("View Details", key=f"view{i}"):
            st.session_state.selected_pg = pg
            st.session_state.page = "detail"
            st.rerun()

        st.divider()

    col1, col2 = st.columns(2)

    if col2.button("👨‍💼 Admin"):
        st.session_state.page = "admin"
        st.rerun()

# -----------------------
# DETAIL PAGE
# -----------------------
elif st.session_state.page == "detail":

    pg = st.session_state.selected_pg

    st.title(pg.get("name", "PG"))
    st.write(f"📍 {pg.get('location', '')}")

    st.success("✅ Verified by Us")

    # IMAGES
    st.subheader("📸 Images")
    images = pg.get("images", "").split(",")

    for img in images:
        if img:
            st.image(img)

    # VIDEOS
    st.subheader("🎥 Videos")
    videos = pg.get("videos", "").split(",")

    for vid in videos:
        if vid:
            st.video(vid)

    st.markdown("""
    ✔ Real room  
    ✔ Bathroom  
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

    # ADD PG
    st.subheader("➕ Add PG")

    name = st.text_input("PG Name")
    location = st.text_input("Location")
    verified = st.selectbox("Verified", ["Yes", "No"])
    images = st.text_input("Image URLs (comma separated)")
    videos = st.text_input("Video URLs (comma separated)")

    if st.button("Save PG"):
        if name and location:
            pg_sheet.append_row([
                name,
                location,
                verified,
                images,
                videos
            ])
            st.success("PG Added!")
            st.rerun()
        else:
            st.error("Fill all fields")

    st.divider()

    # MANAGE
    st.subheader("📋 Manage PGs")

    data = pg_sheet.get_all_records()

    for i, pg in enumerate(data):

        st.write(f"{pg.get('name')} - {pg.get('location')}")

        col1, col2 = st.columns(2)

        if col1.button("❌ Delete", key=f"d{i}"):
            pg_sheet.delete_rows(i + 2)
            st.rerun()

        if col2.button("Toggle Verify", key=f"v{i}"):
            new = "No" if pg.get("verified") == "Yes" else "Yes"
            pg_sheet.update_cell(i + 2, 3, new)
            st.rerun()

        st.divider()