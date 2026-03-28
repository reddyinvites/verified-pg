import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# -----------------------
# GOOGLE SHEETS SETUP
# -----------------------
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

gcp_info = dict(st.secrets["gcp_service_account"])
gcp_info["private_key"] = gcp_info["private_key"].replace("\\n", "\n")

creds = Credentials.from_service_account_info(gcp_info, scopes=scope)
client = gspread.authorize(creds)

# ✅ YOUR SHEET ID
sheet = client.open_by_key("191Fg2-jLtpvziqFrUdQNV2ki1iXYe_fdTGYv3_Tm7wA")
pg_sheet = sheet.sheet1

# -----------------------
# SESSION
# -----------------------
if "page" not in st.session_state:
    st.session_state.page = "home"

# -----------------------
# HOME
# -----------------------
if st.session_state.page == "home":

    st.title("🏠 Verified PGs")
    st.caption("No filters. No fake photos. Only reality.")

    data = pg_sheet.get_all_records()

    for pg in data:

        st.subheader(pg["name"])
        st.write(f"📍 {pg['location']}")

        if pg["verified"] == "Yes":
            st.success("✅ Verified by Us")
        else:
            st.warning("Not Verified")

        if st.button(f"View Details - {pg['name']}"):
            st.session_state.selected_pg = pg
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

    pg = st.session_state.selected_pg

    st.title(pg["name"])
    st.write(f"📍 {pg['location']}")

    if pg["verified"] == "Yes":
        st.success("✅ Verified by Us")

    # -----------------------
    # IMAGES (SAFE)
    # -----------------------
    st.subheader("📸 Images")

    images = str(pg.get("images", "")).split(",")

    for img in images:
        img = img.strip()

        if img.startswith("http"):
            try:
                st.image(img)
            except:
                st.warning("⚠️ Invalid image skipped")

    # -----------------------
    # VIDEOS (SAFE)
    # -----------------------
    st.subheader("🎥 Videos")

    videos = str(pg.get("videos", "")).split(",")

    for vid in videos:
        vid = vid.strip()

        if vid.startswith("http"):
            try:
                st.video(vid)
            except:
                st.warning("⚠️ Invalid video skipped")

    if st.button("⬅ Back"):
        st.session_state.page = "home"
        st.rerun()

# -----------------------
# ADMIN
# -----------------------
elif st.session_state.page == "admin":

    st.title("👨‍💼 Admin Dashboard")

    password = st.text_input("Password", type="password")

    if password != "1234":
        st.stop()

    st.success("Logged in")

    # LOGOUT
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

    images = st.text_input(
        "Image URLs (comma separated)",
        placeholder="https://image1, https://image2"
    )

    videos = st.text_input(
        "Video URLs (comma separated)",
        placeholder="https://video1, https://video2"
    )

    if st.button("Save PG"):

        pg_sheet.append_row([
            name,
            location,
            verified,
            images,
            videos
        ])

        st.success("PG Added!")
        st.rerun()

    st.divider()

    # -----------------------
    # MANAGE PGs
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

        # DELETE
        if col1.button("❌ Delete", key=f"d{i}"):
            pg_sheet.delete_rows(row_index)
            st.rerun()

        # TOGGLE VERIFY
        if col2.button("🔄 Toggle Verify", key=f"t{i}"):

            new_status = "No" if pg["verified"] == "Yes" else "Yes"

            pg_sheet.update_cell(row_index, 3, new_status)

            st.success(f"Updated to {new_status}")
            st.rerun()

        st.divider()