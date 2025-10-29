import streamlit as st
import pandas as pd
import gspread
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
import pathlib
import base64
from google.oauth2.service_account import Credentials
import numpy as np
import io

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
def load_data1(x):
    credentials = load_credentials()
    gc = gspread.authorize(credentials)
    sheet = gc.open(x).sheet1
    data = sheet.get_all_values()
    header = data[0]
    values = data[1:]
    data = pd.DataFrame(values, columns=header)
    return data

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
        khoa_select = data["Khoa"].unique()
    data = data.loc[data["Khoa"].isin(khoa_select)]
    data['Timestamp'] = pd.to_datetime(data['Timestamp'], errors='coerce')
    start_date = sd
    end_date = ed + timedelta(days=1)
    data_final = data[(data['Timestamp'] >= pd.Timestamp(start_date)) & (data['Timestamp'] < pd.Timestamp(end_date))]
    return data_final

def tao_thong_ke(x,y):
    df = pd.DataFrame(x)
    bo_cot = df[['STT','Timestamp','Khoa', 'Tỉ lệ đạt','Tên người đánh giá', 'Tên người thực hiện']]
    bo_cot['Tỉ lệ đạt'] = bo_cot['Tỉ lệ đạt'].str.replace(',', '.')
    bo_cot['Tỉ lệ đạt'] = pd.to_numeric(bo_cot["Tỉ lệ đạt"], errors='coerce')
    bo_cot = bo_cot.dropna(subset=['Tỉ lệ đạt'])
    bo_cot['Tỉ lệ đạt'] = bo_cot['Tỉ lệ đạt'] * 100
    if y == "Tổng quát":
        bo_cot["Thời gian"] = bo_cot["Timestamp"].dt.strftime("%m - %Y")
        bo_cot = bo_cot.groupby(['Khoa', 'Thời gian']).agg({'Khoa':'count','Tỉ lệ đạt': 'mean'}).rename(columns={"Khoa": "Số lượt"}).reset_index()
        bo_cot.insert(0, 'STT', range(1, len(bo_cot) + 1))
    return bo_cot

def chon_khoa(khoa):
    placeholder1 = st.empty()
    if st.session_state.phan_quyen in ["1","2","3"]:
        if st.checkbox("Chọn tất cả khoa"):
            placeholder1.empty()
            khoa_select = "Chọn tất cả khoa"
        else:
            with placeholder1:
                khoa_select = st.multiselect(label="Chọn khoa",
                                                  options= khoa.unique())
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

def chon_thoi_diem(thoi_diem):
    placeholder1 = st.empty()
    if st.checkbox("Chọn tất cả thời điểm"):
        placeholder1.empty()
        thoi_diem_select = "All"
    else:
        with placeholder1:
            thoi_diem_select = st.multiselect(label="Chọn thời điểm đánh giá",
                                            options= thoi_diem.unique())
    return thoi_diem_select

def tinh_metrics(data):
    """Tính các metrics để hiển thị trên thẻ"""
    # Lượt đánh giá
    luot_danh_gia = len(data)
    # Số khoa
    so_khoa = data['Khoa'].nunique()
    # Số Điều dưỡng - đếm distinct từ 1 cột, loại bỏ giá trị rỗng và khoảng trắng
    dieu_duong_set = set()
    for col in ['Tên người thực hiện']:
        if col in data.columns:
            # Lọc các giá trị không rỗng và không chỉ là khoảng trắng
            valid_values = data[col].dropna()
            valid_values = valid_values[valid_values.astype(str).str.strip() != '']
            dieu_duong_set.update(valid_values.unique())
    # Loại bỏ giá trị rỗng nếu có trong set
    dieu_duong_set.discard('')
    dieu_duong_set.discard(None)
    so_dieu_duong = len(dieu_duong_set)
    # Tỉ lệ tuân thủ toàn CSCS
    data_temp = data.copy()
    data_temp['Tỉ lệ đạt'] = data_temp['Tỉ lệ đạt'].astype(str).str.replace(',', '.')
    data_temp['Tỉ lệ đạt'] = pd.to_numeric(data_temp['Tỉ lệ đạt'], errors='coerce')
    mean_value = data_temp['Tỉ lệ đạt'].mean() * 100
    tl_dat= float(format(mean_value, '.2f'))  # Format với 2 chữ số thập phân
    
    return {
        'luot_danh_gia': luot_danh_gia,
        'so_khoa': so_khoa,
        'so_dieu_duong': so_dieu_duong,
        'tl_dat': tl_dat,
    }
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
        <p style="color:green">THỐNG KÊ ĐÁNH GIÁ PRIME</p>
        </div>
    </div>
    <div class="header-underline"></div>

 """, unsafe_allow_html=True)
html_code = f'<p class="demuc"><i>Nhân viên: {st.session_state.username}</i></p>'
st.html(html_code)
sheeti1 = st.secrets["sheet_name"]["input_1"]
sheeto6 = st.secrets["sheet_name"]["output_6"]
data = load_data1(sheeti1)
data_thoi_diem = load_data1(sheeto6)
khoa = data["Khoa"]
thoi_diem = data_thoi_diem["Thời điểm đánh giá"]
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
    thoi_diem_select = chon_thoi_diem(thoi_diem)
    
    submit_thoigian = st.form_submit_button("OK")
if submit_thoigian:
    if ed < sd:
        st.error("Lỗi ngày kết thúc đến trước ngày bắt đầu. Vui lòng chọn lại")  
    else:
        sheeto6 = st.secrets["sheet_name"]["output_6"]
        data = load_data(sheeto6,sd,ed,khoa_select)
        if thoi_diem_select != "All":
            data = data[data["Thời điểm đánh giá"].isin(thoi_diem_select)]
            if data.empty:
                st.toast("Không có dữ liệu theo yêu cầu")
            else:
                metrics = tinh_metrics(data)
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("**:red[Lượt đánh giá]**", metrics['luot_danh_gia'],border=True)
                with col2:
                    st.metric("**:red[Số khoa]**", metrics['so_khoa'],border=True)
                with col3:
                    st.metric("**:red[Số điều dưỡng]**", metrics['so_dieu_duong'],border=True)
                with col4:
                    if metrics['tl_dat'] is not None:
                        if metrics['tl_dat'] != 100:
                            st.metric("**:red[Tỉ lệ đạt]**", f"{metrics['tl_dat']:.2f}%",border=True)
                        else:
                            st.metric("**:red[Tỉ lệ đạt]**", f"{metrics['tl_dat']:.0f}%",border=True)                
                    else:
                        st.metric("**:red[Tỉ lệ đạt]**", "-")  

                with st.expander("**:blue[Thống kê tổng quát]**"):
                    thongke = tao_thong_ke(data,"Tổng quát")
                    st.dataframe(thongke, 
                                hide_index=True,
                                column_config = {
                                        "Tỉ lệ đạt": st.column_config.NumberColumn(format="%.2f %%")
                                        })
                with st.expander("**:blue[Thống kê chi tiết]**"):
                    thongkechitiet = tao_thong_ke(data,"Chi tiết")
                    st.dataframe(thongkechitiet,
                                hide_index=True, 
                                column_config = {
                                        "Tỉ lệ đạt": st.column_config.NumberColumn(format="%.2f %%")
                                        })
        else:
            metrics = tinh_metrics(data)
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("**:red[Lượt đánh giá]**", metrics['luot_danh_gia'],border=True)
            with col2:
                st.metric("**:red[Số khoa]**", metrics['so_khoa'],border=True)
            with col3:
                st.metric("**:red[Số điều dưỡng]**", metrics['so_dieu_duong'],border=True)
            with col4:
                if metrics['tl_dat'] is not None:
                    if metrics['tl_dat'] != 100:
                        st.metric("**:red[Tỉ lệ đạt]**", f"{metrics['tl_dat']:.2f}%",border=True)
                    else:
                        st.metric("**:red[Tỉ lệ đạt]**", f"{metrics['tl_dat']:.0f}%",border=True)                
                else:
                    st.metric("**:red[Tỉ lệ đạt]**", "-")  

            with st.expander("**:blue[Thống kê tổng quát]**"):
                thongke = tao_thong_ke(data,"Tổng quát")
                st.dataframe(thongke, 
                            hide_index=True,
                            column_config = {
                                    "Tỉ lệ đạt": st.column_config.NumberColumn(format="%.2f %%")
                                    })
            with st.expander("**:blue[Thống kê chi tiết]**"):
                thongkechitiet = tao_thong_ke(data,"Chi tiết")
                st.dataframe(thongkechitiet,
                            hide_index=True, 
                            column_config = {
                                    "Tỉ lệ đạt": st.column_config.NumberColumn(format="%.2f %%")
                                    })                
powerbi_url = "https://app.powerbi.com/groups/fbea42ac-f40a-4ada-bdbe-95cd1dc34b62/reports/e4d93ac2-150f-4e45-9932-e93fc32666e8/49312121a00775315830?experience=power-bi"
st.markdown(f"[📊 Xem báo cáo chi tiết tại Power BI]({powerbi_url})", unsafe_allow_html=True)

