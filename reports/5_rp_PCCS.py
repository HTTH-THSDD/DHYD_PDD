import streamlit as st
import pandas as pd
import gspread
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
import pathlib
import base64
from google.oauth2.service_account import Credentials
import numpy as np

@st.cache_data(ttl=3600)
def get_img_as_base64(file):
    with open(file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

def load_css(file_path):
    with open(file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
css_path = pathlib.Path("asset/style.css")

@st.cache_data(ttl=10)
def get_key_from_value(dictionary, value):
    return next((key for key, val in dictionary.items() if val == value), None)

@st.cache_data(ttl=3600)
def load_credentials():
    creds_info = {
    "type": st.secrets["google_service_account"]["type"],
    "project_id": st.secrets["google_service_account"]["project_id"],
    "private_key_id": st.secrets["google_service_account"]["private_key_id"],
    "private_key": st.secrets["google_service_account"]["private_key"],
    "client_email": st.secrets["google_service_account"]["client_email"],
    "client_id": st.secrets["google_service_account"]["client_id"],
    "auth_uri": st.secrets["google_service_account"]["auth_uri"],
    "token_uri": st.secrets["google_service_account"]["token_uri"],
    "auth_provider_x509_cert_url": st.secrets["google_service_account"]["auth_provider_x509_cert_url"],
    "client_x509_cert_url": st.secrets["google_service_account"]["client_x509_cert_url"],
    "universe_domain": st.secrets["google_service_account"]["universe_domain"],
    }
    # Dùng để kết nối Google APIs
    credentials = Credentials.from_service_account_info(
        creds_info,
        scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    )
    return credentials

@st.cache_data(ttl=10)
def load_data(x,sd,ed,khoa_select):
    credentials = load_credentials()
    gc = gspread.authorize(credentials)
    sheet = gc.open(x).sheet1
    data = sheet.get_all_values()
    header = data[0]
    values = data[1:]
    data = pd.DataFrame(values, columns=header)
    if khoa_select == "Chọn tất cả khoa" and st.session_state.username == st.secrets["user_special"]["u1"]:
        khoa_select = [st.secrets["user_special"]["u1_khoa1"],
                        st.secrets["user_special"]["u1_khoa2"],
                        st.secrets["user_special"]["u1_khoa3"],]
    if khoa_select == "Chọn tất cả khoa" and st.session_state.username == st.secrets["user_special"]["u2"]:
        khoa_select = [st.secrets["user_special"]["u2_khoa1"],
                            st.secrets["user_special"]["u2_khoa2"]]
    if khoa_select == "Chọn tất cả khoa" and st.session_state.username == st.secrets["user_special"]["u3"]:
        khoa_select = [st.secrets["user_special"]["u3_khoa1"],
                            st.secrets["user_special"]["u3_khoa2"]]
    if khoa_select == "Chọn tất cả khoa" and st.session_state.phan_quyen in ["1","2","3"]:
        khoa_select = data["Khoa báo cáo"].unique()
    data = data.loc[data["Khoa báo cáo"].isin(khoa_select)]
    data['Timestamp'] = pd.to_datetime(data['Timestamp'], errors='coerce')
    start_date = sd
    end_date = ed + timedelta(days=1)
    data_final = data[(data['Timestamp'] >= pd.Timestamp(start_date)) & (data['Timestamp'] < pd.Timestamp(end_date))]
    idx = data_final.groupby(
            ["Khoa báo cáo", "Ngày báo cáo", "Ca báo cáo"]
        )["Timestamp"].idxmax()

    # Lọc ra các dòng tương ứng
    data_final_latest = data_final.loc[idx].reset_index(drop=True)
    return data_final_latest
def to_mau_dong_cuoi(data):
    def highlight(row):
        if row.name == len(data) - 1:
            return ['background-color: #ffe599; color: #cf1c00'] * len(row)
        return [''] * len(row)
    return highlight

def custom_format(cell, row_idx, is_last_row):
    if isinstance(cell, (int, float)):
        if is_last_row:
            return f"{cell:,.2f}"
        else:
            return f"{int(cell):,}" if isinstance(cell, int) or cell == int(cell) else f"{cell:,.0f}"
    return cell

# Xử lý toàn bộ bảng: áp dụng định dạng theo từng dòng
def format_per_row(df):
    last_idx = len(df) - 1
    formatted = df.copy()
    for r in df.index:
        for c in df.columns:
            formatted.at[r, c] = custom_format(df.at[r, c], r, r == last_idx)
    return formatted

def tao_thong_ke(x):
    df = pd.DataFrame(x)
    df = df.drop(["STT", "Timestamp"], axis=1)
    df = df.sort_values("Khoa báo cáo")
    # Gắn thêm cột số thứ tự
    df.insert(0, 'STT', range(1, len(df) + 1))
    if st.session_state.phan_quyen == "4" and st.session_state.username not in [
        st.secrets["user_special"]["u1"],
        st.secrets["user_special"]["u2"],
        st.secrets["user_special"]["u3"]
    ]:
        df = df.drop("Khoa báo cáo", axis=1)
    df['Tỉ lệ NB/DD'] = df['Tỉ lệ NB/DD'].str.replace(',', '.')
    df['Tỉ lệ NB/DD'] = pd.to_numeric(df['Tỉ lệ NB/DD'], errors='coerce')
    df['Số người bệnh cấp I'] = pd.to_numeric(df['Số người bệnh cấp I'], errors='coerce')
    df['Số điều dưỡng chăm sóc cấp I'] = pd.to_numeric(df['Số điều dưỡng chăm sóc cấp I'], errors='coerce')
    mean_nb = df["Số người bệnh cấp I"].mean()
    mean_dd = df["Số điều dưỡng chăm sóc cấp I"].mean()
    mean_tl = df["Tỉ lệ NB/DD"].mean()

    # Tạo dòng trung bình
    row_mean = pd.DataFrame({
        "STT": [""],
        "Ngày báo cáo": ["Trung bình"],
        "Khoa báo cáo": [""],
        "Người báo cáo": [""],
        "Ca báo cáo": [""],
        "Số người bệnh cấp I": [mean_nb],
        "Số điều dưỡng chăm sóc cấp I": [mean_dd],
        "Tỉ lệ NB/DD": [mean_tl]
    })
    # Ghép dòng trung bình vào cuối bảng
    cols = df.columns
    row_mean = row_mean[[c for c in cols if c in row_mean.columns]]  # Đảm bảo đúng thứ tự cột
    df = pd.concat([df, row_mean], ignore_index=True)
    df = df.dropna(subset=['Tỉ lệ NB/DD'])
    df = format_per_row(df.copy())
    styled_df = (df.style.apply(to_mau_dong_cuoi(df), axis=1)
                )

    st.dataframe(styled_df, use_container_width=True, hide_index=True)

def chon_khoa(khoa):
    placeholder1 = st.empty()
    if st.session_state.phan_quyen in ["1","2","3"]:
        if st.checkbox("Chọn tất cả khoa"):
            placeholder1.empty()
            khoa_select = "Chọn tất cả khoa"
        else:
            with placeholder1:
                khoa_select = st.multiselect(label="Chọn khoa",
                                                  options= khoa)
        return khoa_select
    else:
        if st.session_state.username == st.secrets["user_special"]["u1"]:
            if st.checkbox("Cả 3 khoa"):
                placeholder1.empty()
                khoa_select = "Chọn tất cả khoa"
            else:
                with placeholder1:
                    khoa_select = st.multiselect(label="Chọn khoa",
                                         options= [
                            st.secrets["user_special"]["u1_khoa1"],
                            st.secrets["user_special"]["u1_khoa2"],
                            st.secrets["user_special"]["u1_khoa3"],])
            return khoa_select
        elif st.session_state.username == st.secrets["user_special"]["u2"]:
            if st.checkbox("Cả 2 khoa"):
                placeholder1.empty()
                khoa_select = "Chọn tất cả khoa"
            else:
                with placeholder1:
                    khoa_select = st.multiselect(label="Chọn khoa",
                                         options= [
                            st.secrets["user_special"]["u2_khoa1"],
                            st.secrets["user_special"]["u2_khoa2"],])
            return khoa_select
        elif st.session_state.username == st.secrets["user_special"]["u3"]:
            if st.checkbox("Cả 2 khoa"):
                placeholder1.empty()
                khoa_select = "Chọn tất cả khoa"
            else:
                with placeholder1:
                    khoa_select = st.multiselect(label="Chọn khoa",
                                         options= [
                            st.secrets["user_special"]["u3_khoa1"],
                            st.secrets["user_special"]["u3_khoa2"]])
            return khoa_select
        else:
            khoa_select = st.session_state.khoa
            khoa_select = [khoa_select]
            return khoa_select
        

##################################### Main Section ###############################################
load_css(css_path)
img = get_img_as_base64("pages/img/logo.png")
st.markdown(f"""
    <div class="fixed-header">
        <div class="header-content">
            <img src="data:image/png;base64,{img}" alt="logo">
            <div class="header-text">
                <h1>BỆNH VIỆN ĐẠI HỌC Y DƯỢC THÀNH PHỐ HỒ CHÍ MINH<span style="vertical-align: super; font-size: 0.6em;">&reg;</span><br><span style="color:#c15088">Phòng Điều dưỡng</span></h1>
            </div>
        </div>
        <div class="header-subtext">
        <p style="color:green">THỐNG KÊ PCCS - CẤP I</p>
        </div>
    </div>
    <div class="header-underline"></div>

 """, unsafe_allow_html=True)
html_code = f'<p class="demuc"><i>Nhân viên: {st.session_state.username}</i></p>'
st.html(html_code)
khoa = ["Đơn vị Gây mê hồi sức Phẫu thuật tim mạch",
        "Đơn vị Hồi sức Ngoại Thần kinh",
        "Khoa Hô hấp",
        "Khoa Hồi sức tích cực",
        "Khoa Thần kinh",
        "Khoa Nội Tim mạch",
        "Khoa Phẫu thuật tim mạch",
        "Khoa Tim mạch can thiệp"]
now_vn = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))  
md = date(2025, 1, 1)
with st.form("Thời gian"):
    cold = st.columns([5,5])
    with cold[0]:
        sd = st.date_input(
        label="Ngày bắt đầu",
        value=md,
        min_value=md,
        max_value=now_vn.date(), 
        format="DD/MM/YYYY",
        )
    with cold[1]:
        ed = st.date_input(
        label="Ngày kết thúc",
        value=now_vn.date(),
        min_value=md,
        max_value=now_vn.date(), 
        format="DD/MM/YYYY",
        )
    khoa_select = chon_khoa(khoa)
    submit_thoigian = st.form_submit_button("OK")
if submit_thoigian:
    if ed < sd:
        st.error("Lỗi ngày kết thúc đến trước ngày bắt đầu. Vui lòng chọn lại")  
    else:
        sheeto8 = st.secrets["sheet_name"]["output_8"]
        data = load_data(sheeto8,sd,ed,khoa_select)
        if data.empty:
            st.toast("Không có dữ liệu theo yêu cầu")
        else:
            st.markdown("<h5 style='text-align: center;'></h5>", unsafe_allow_html=True)
            ds_khoa_da_bao_cao = data["Khoa báo cáo"].unique().tolist()
            ds_khoa_chua_bao_cao = list(set(khoa) - set(ds_khoa_da_bao_cao))
            if ds_khoa_chua_bao_cao:
                st.markdown(f"<h4 style='text-align: center;'>❌ Danh sách các khoa chưa báo cáo ({len(ds_khoa_chua_bao_cao)})</h5>", unsafe_allow_html=True)
                st.markdown("<ul style='list-style-type: disc; padding-left: 20px;'>", unsafe_allow_html=True)
                for khoa in ds_khoa_chua_bao_cao:
                    st.markdown(f"<li>{khoa}</li>", unsafe_allow_html=True)
                st.markdown("</ul>", unsafe_allow_html=True)
                st.divider()
                st.markdown(f"<h4 style='text-align: center;'>✅Danh sách các khoa đã báo cáo ({len(ds_khoa_da_bao_cao)})</h5>", unsafe_allow_html=True)
                st.markdown("<ul style='list-style-type: disc; padding-left: 20px;'>", unsafe_allow_html=True)
                for khoa in ds_khoa_da_bao_cao:
                    st.markdown(f"<li>{khoa}</li>", unsafe_allow_html=True) 
                st.markdown("</ul>", unsafe_allow_html=True)   
            else:
                st.markdown("<p style='text-align: center;'>Tất cả các khoa đã báo cáo</p>", unsafe_allow_html=True)
            st.divider()
            st.markdown("<h4 style='text-align: center;'>Thống kê báo cáo phân cấp chăm sóc</h5>", unsafe_allow_html=True)
            tao_thong_ke(data)
            



