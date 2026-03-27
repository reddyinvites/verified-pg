import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Verified PGs", layout="wide")

# =========================
# GOOGLE CONNECT
# =========================
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

gcp_info = dict(st.secrets["gcp_service_account"])
gcp_info["private_key"] = gcp_info["private_key"].replace("\\n", "\n")

creds = Credentials.from_service_account_info(gcp_info, scopes=scope)
client = gspread.authorize(creds)

sheet = client.open_by_key("1y60dTYBKgkOi7J37jtGK4BkkmUoZF8yD4P5J3xA5q6Q")
pg_sheet = sheet.sheet1

pg_data = pg_sheet.get_all_records()

# =========================
# HEADER
# =========================
st.title("🏠 Verified PGs")
st.subheader("No filters. No fake photos. Only reality.")

st.divider()

# =========================
# LISTINGS
# =========================
if not pg_data:
    st.warning("No PGs available")
    st.stop()

for pg in pg_data:

    with st.container():

        col1, col2 = st.columns([1,2])

        # IMAGE (use sample or from sheet later)
        with col1:
            st.image("https://via.placeholder.com/300")

        # DETAILS
        with col2:
            st.markdown(f"### {pg['name']}")
            st.write(f"📍 {pg['location']}")

            # VERIFIED BADGE
            st.success("✅ Verified by Us")

            st.write("📸 Real room images")
            st.write("🚿 Bathroom reality")
            st.write("🍛 Actual food plate")
            st.write("🍽️ Dining area")
            st.write("🧳 Storage space")
            st.write("🏢 Building view")

            if st.button(f"View Details - {pg['name']}"):
                st.session_state.selected_pg = pg
                st.session_state.page = "details"
                st.rerun()

        st.divider()

# =========================
# DETAILS PAGE
# =========================
if "page" in st.session_state and st.session_state.page == "details":

    pg = st.session_state.selected_pg

    st.title(pg["name"])
    st.write(f"📍 {pg['location']}")

    st.success("✅ Verified by Us")

    st.subheader("📸 Real Captures")

    st.image("https://via.placeholder.com/600", caption="Room")
    st.image("https://via.placeholder.com/600", caption="Bathroom")
    st.image("https://via.placeholder.com/600", caption="Food")
    st.image("https://via.placeholder.com/600", caption="Dining")
    st.image("https://via.placeholder.com/600", caption="Storage")
    st.image("https://via.placeholder.com/600", caption="Outside")

    st.info("What you see is exactly what you get.")

    if st.button("⬅ Back"):
        st.session_state.page = "home"
        st.rerun()
