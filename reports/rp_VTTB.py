import streamlit as st
import pandas as pd
import gspread
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
import pathlib
import base64
from google.oauth2.service_account import Credentials

@st.cache_data(ttl=3600)
def get_img_as_base64(file):
    with open(file, "rb") as f:
        data = f.read()
    
    return base64.b64encode(data).decode()

def load_css(file_path):
    with open(file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


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
def load_data(x):
    credentials = load_credentials()
    gc = gspread.authorize(credentials)
    sheet = gc.open(x).sheet1
    data = sheet.get_all_values()
    header = data[0]
    values = data[1:]
    data = pd.DataFrame(values, columns=header)
    return data

@st.cache_data(ttl=10)
def load_data1(sheeto5,sd,ed,khoa_select):
    credentials = load_credentials()
    gc = gspread.authorize(credentials)
    sheet = gc.open(sheeto5).sheet1
    data = sheet.get_all_values()
    header = data[0]
    values = data[1:]
    data = pd.DataFrame(values, columns=header)
    if khoa_select != "Tất cả":
        data = data.loc[data["Khoa báo cáo"].isin(khoa_select)]
    data['Timestamp'] = pd.to_datetime(data['Timestamp'], errors='coerce')
    start_date = sd
    end_date = ed + timedelta(days=1)
    data_final = data[(data['Timestamp'] >= pd.Timestamp(start_date)) & (data['Timestamp'] < pd.Timestamp(end_date))]
    return data_final

def chon_khoa(khoa):
    if st.checkbox("Tất cả"):
        khoa_select = "Tất cả"
    else:
        khoa_select = st.multiselect(label="Chọn khoa",
                                                options= khoa)
    return khoa_select

def khoa_chua_bao_cao(khoa,sd,ed):
    credentials = load_credentials()
    gc = gspread.authorize(credentials)
    sheet = gc.open(sheeto5).sheet1
    data = sheet.get_all_values()
    header = data[0]
    values = data[1:]
    datax = pd.DataFrame(values, columns=header)
    start_date = sd
    end_date = ed + timedelta(days=1)
    datax["Ngày báo cáo"] = pd.to_datetime(datax["Ngày báo cáo"]).dt.date
    datax = datax[(datax["Ngày báo cáo"] >= start_date) & (datax["Ngày báo cáo"] <= end_date)]
    data = datax.groupby("Ngày báo cáo").agg(
    Cac_khoa_da_bao_cao=("Khoa báo cáo", lambda x: ",".join(sorted(set(x)))),
    So_khoa_bao_cao=("Khoa báo cáo", lambda x: len(set(x)))  
    ).reset_index()
    data = data.rename(columns={
    "Cac_khoa_da_bao_cao": "Các khoa đã báo cáo",
    "So_khoa_bao_cao": "Số khoa đã báo cáo"
    })
    tat_ca_khoa = set(khoa)
    data["Các khoa chưa báo cáo"] = data["Các khoa đã báo cáo"].apply(
    lambda x: ", ".join(sorted(tat_ca_khoa - set(map(str.strip, x.split(",")))))
    )
    data["Số khoa chưa báo cáo"] = data["Các khoa chưa báo cáo"].apply(
    lambda x: 0 if not x else len(x.split(", "))
    )
    data["Các khoa đã báo cáo"] = data["Các khoa đã báo cáo"].str.replace(",", "\n")
    data["Các khoa chưa báo cáo"] = data["Các khoa chưa báo cáo"].str.replace(", ", "\n")
    return data
##################################### Main Section ###############################################
css_path = pathlib.Path("asset/style.css")
load_css(css_path)
img = get_img_as_base64("pages/img/logo.png")
st.markdown(f"""
    <div class="fixed-header">
        <div class="header-content">
            <img src="data:image/png;base64,{img}" alt="logo">
            <div class="header-text">
                <h1>BỆNH VIỆN ĐẠI HỌC Y DƯỢC THÀNH PHỐ HỒ CHÍ MINH<br><span style="color:#c15088">Phòng Điều dưỡng</span></h1>
            </div>
        </div>
        <div class="header-subtext">
        <p style="color:green">THỐNG KÊ VẬT TƯ THIẾT BỊ</p>
        </div>
    </div>
    <div class="header-underline"></div>

 """, unsafe_allow_html=True)
html_code = f'<p class="demuc"><i>Nhân viên: {st.session_state.username}</i></p>'
st.html(html_code)
sheeti5 = st.secrets["sheet_name"]["input_5"]
data = load_data(sheeti5)
khoa = data["Khoa"].unique()
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
        st.error("Ngày kết thúc đến trước ngày bắt đầu. Vui lòng chọn lại")  
    else:
        sheeto5 = st.secrets["sheet_name"]["output_5"]
        data1 = load_data1(sheeto5,sd,ed,khoa_select)
        if data1.empty:
            st.warning("Không có dữ liệu theo yêu cầu")
        else:
            st.write(f"Các báo cáo thiết bị của {khoa_select}")
            st.dataframe(data1, use_container_width=True, hide_index=True)
        data2 = khoa_chua_bao_cao(khoa,sd,ed)
        if data2.empty:
            st.warning("Không có dữ liệu theo yêu cầu")
        else:
            st.write(f"Tổng kết báo cáo theo ngày")
            st.dataframe(data2, use_container_width=True, hide_index=True)

