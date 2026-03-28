import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import cloudinary
import cloudinary.uploader

# -----------------------
# CLOUDINARY CONFIG
# -----------------------
cloudinary.config(
    cloud_name=st.secrets["cloudinary"]["cloud_name"],
    api_key=st.secrets["cloudinary"]["api_key"],
    api_secret=st.secrets["cloudinary"]["api_secret"]
)

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
    st.caption("No filters. Only real data.")

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

    # IMAGES
    st.subheader("📸 Images")
    for img in str(pg.get("images", "")).split(","):
        if img.strip().startswith("http"):
            st.image(img.strip())

    # VIDEOS
    st.subheader("🎥 Videos")
    for vid in str(pg.get("videos", "")).split(","):
        if vid.strip().startswith("http"):
            st.video(vid.strip())

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

    # FILE UPLOAD
    uploaded_files = st.file_uploader(
        "Upload Images / Videos",
        accept_multiple_files=True,
        type=["jpg", "png", "jpeg", "mp4"]
    )

    uploaded_urls = []

    if uploaded_files:
        for file in uploaded_files:

            result = cloudinary.uploader.upload(
                file,
                resource_type="auto"
            )

            uploaded_urls.append(result["secure_url"])

        st.success("✅ Uploaded to Cloud!")

    # SAVE
    if st.button("Save PG"):

        images = ",".join([u for u in uploaded_urls if ".mp4" not in u])
        videos = ",".join([u for u in uploaded_urls if ".mp4" in u])

        pg_sheet.append_row([
            name,
            location,
            verified,
            images,
            videos
        ])

        st.success("PG Added Successfully!")
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