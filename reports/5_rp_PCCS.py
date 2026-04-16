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
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except UnicodeDecodeError:
        # Fallback to different encoding if UTF-8 fails
        with open(file_path, 'r', encoding='latin-1') as f:
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
            ["Khoa báo cáo", "Ngày báo cáo"]
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

# def custom_format(cell, row_idx, is_last_row, col_name=None):
#     try:
#         if col_name in ["Tỉ lệ NB/ĐD sáng", "Tỉ lệ NB/ĐD chiều", "Tỉ lệ NB/ĐD tối"]:
#             if pd.isna(cell) or cell == "":
#                 return ""
#             if isinstance(cell, (int, float)):
#                 return f"{cell:,.2f}"
#         if isinstance(cell, (int, float)):
#             if pd.isna(cell):
#                 return ""
#             if is_last_row:
#                 return f"{cell:,.2f}"
#             else:
#                 return f"{int(cell):,}" if isinstance(cell, int) or cell == int(cell) else f"{cell:,.0f}"
#         return str(cell) if cell is not None else ""
#     except Exception as e:
#         return str(cell)

def custom_format(cell, row_idx, is_last_row, col_name=None):
    try:
        if pd.isna(cell) or cell == "":
            return ""
        # Nhóm tỉ lệ → luôn 2 chữ số
        if col_name in ["Tỉ lệ NB/ĐD sáng", "Tỉ lệ NB/ĐD chiều", "Tỉ lệ NB/ĐD tối"]:
            if isinstance(cell, (int, float)):
                return f"{float(cell):,.2f}"
        # Các số khác
        if isinstance(cell, (int, float)):
            if is_last_row:
                return f"{float(cell):,.2f}"
            else:
                if float(cell).is_integer():
                    return f"{int(cell):,}"
                else:
                    return f"{float(cell):,.0f}"
        return str(cell)
    except Exception:
        return str(cell)

#Xử lý toàn bộ bảng: áp dụng định dạng theo từng dòng
# def format_per_row(df):
#     if df.empty:
#         return df
#     last_idx = len(df) - 1
#     # Convert dataframe to list of lists to avoid dtype assignment issues
#     data = []
#     for r_idx, r in df.iterrows():
#         row_data = []
#         for c in df.columns:
#             cell_value = custom_format(r[c], r_idx, r_idx == last_idx, c)
#             row_data.append(cell_value)
#         data.append(row_data)
    
#     # Rebuild dataframe from list as object dtype
#     formatted = pd.DataFrame(data, columns=df.columns, dtype=object)
#     return formatted

def format_per_row(df):
    if df.empty:
        return df
    last_idx = len(df) - 1
    formatted_data = []
    for r_idx in range(len(df)):
        row_data = []
        for c in df.columns:
            cell = df.iloc[r_idx][c]
            formatted_cell = custom_format(cell, r_idx, r_idx == last_idx, c)
            row_data.append(formatted_cell)
        formatted_data.append(row_data)
    return pd.DataFrame(formatted_data, columns=df.columns)

def tao_thong_ke(x):
    df = pd.DataFrame(x)
    df = df.drop(["STT", "Timestamp","Data"], axis=1)
    df = df.sort_values("Khoa báo cáo")
    # Gắn thêm cột số thứ tự
    df.insert(0, 'STT', range(1, len(df) + 1))
    if st.session_state.phan_quyen == "4" and st.session_state.username not in [
        st.secrets["user_special"]["u1"],
        st.secrets["user_special"]["u2"],
        st.secrets["user_special"]["u3"]
    ]:
        df = df.drop("Khoa báo cáo", axis=1)
    
    # Xử lý an toàn cho conversion chuỗi sang số
    for col in ["Tỉ lệ NB/ĐD sáng", "Tỉ lệ NB/ĐD chiều", "Tỉ lệ NB/ĐD tối"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(',', '.')
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    mean_sang = df["Tỉ lệ NB/ĐD sáng"].mean() if "Tỉ lệ NB/ĐD sáng" in df.columns else 0
    mean_chieu = df["Tỉ lệ NB/ĐD chiều"].mean() if "Tỉ lệ NB/ĐD chiều" in df.columns else 0
    mean_toi = df["Tỉ lệ NB/ĐD tối"].mean() if "Tỉ lệ NB/ĐD tối" in df.columns else 0
    
    mean_sang = round(mean_sang, 2) if pd.notna(mean_sang) else 0
    mean_chieu = round(mean_chieu, 2) if pd.notna(mean_chieu) else 0
    mean_toi = round(mean_toi, 2) if pd.notna(mean_toi) else 0

    # Tạo dòng trung bình
    row_mean = pd.DataFrame({
        "STT": [""],
        "Ngày báo cáo": ["Trung bình"],
        "Khoa báo cáo": [""],
        "Người báo cáo": [""],
        "Tỉ lệ NB/ĐD sáng": [mean_sang],
        "Tỉ lệ NB/ĐD chiều": [mean_chieu],
        "Tỉ lệ NB/ĐD tối": [mean_toi]
    })
    # Ghép dòng trung bình vào cuối bảng
    cols = df.columns
    row_mean = row_mean[[c for c in cols if c in row_mean.columns]]  # Đảm bảo đúng thứ tự cột
    row_mean = row_mean.astype(object)  # Convert to object dtype to match formatted df
    df = pd.concat([df, row_mean], ignore_index=True)
    df = df.apply(pd.to_numeric, errors="ignore")
    df = format_per_row(df.copy())
    styled_df = (df.style.apply(to_mau_dong_cuoi(df), axis=1))
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
                <h1>BỆNH VIỆN ĐẠI HỌC Y DƯỢC THÀNH PHỐ HỒ CHÍ MINH<span style="vertical-align: super; font-size: 0.6em;">&#174;</span><br><span style="color:#c15088">Phòng Điều dưỡng</span></h1>
            </div>
        </div>
        <div class="header-subtext">
        <p style="color:green">THỐNG KÊ NB PCCS CẤP I/ ĐD</p>
        </div>
    </div>
    <div class="header-underline"></div>

 """, unsafe_allow_html=True)
html_code = f'<p class="demuc"><i>Nhân viên: {st.session_state.username}</i></p>'
st.html(html_code)
khoa = ["Đơn nguyên Gây mê hồi sức Phẫu thuật tim mạch",
        "Đơn nguyên Hồi sức Ngoại Thần kinh",
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
        value=now_vn.date(),
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
            st.markdown("<h4 style='text-align: center;'>Thống kê Người bệnh PCCS cấp I/ Điều dưỡng</h5>", unsafe_allow_html=True)
            tao_thong_ke(data)
            


