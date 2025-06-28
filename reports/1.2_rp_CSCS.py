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
        khoa_select = data["Khoa"]
    data = data.loc[data["Khoa"].isin(khoa_select)]
    data['Timestamp'] = pd.to_datetime(data['Timestamp'], errors='coerce')
    start_date = sd
    end_date = ed + timedelta(days=1)
    data_final = data[(data['Timestamp'] >= pd.Timestamp(start_date)) & (data['Timestamp'] < pd.Timestamp(end_date))]
    return data_final

def tao_thong_ke(x,y):
    df = pd.DataFrame(x)
    #Lấy những cột cần cho hiển thị lên trang báo cáo
    bo_cot = df[['STT','Timestamp','Khoa', 'Tên chỉ số chăm sóc', 'Tỉ lệ tuân thủ','Tên người đánh giá', 'Tên người thực hiện']]
    bo_cot = df[['STT','Timestamp','Khoa', 'Tên chỉ số chăm sóc', 'Tỉ lệ tuân thủ','Tên người đánh giá', 'Tên người thực hiện']]
    #Chuyển những cột tuân thủ thành dạng số nhờ đổi dấu "," thành "."
    bo_cot['Tỉ lệ tuân thủ'] = bo_cot['Tỉ lệ tuân thủ'].str.replace(',', '.')
    #Chuyển dạng số chính thức
    bo_cot['Tỉ lệ tuân thủ'] = pd.to_numeric(bo_cot["Tỉ lệ tuân thủ"], errors='coerce')
    #Nhấn 100 thành tỉ lệ phần trăm
    bo_cot['Tỉ lệ tuân thủ'] = bo_cot['Tỉ lệ tuân thủ'] * 100

    if y == "Chi tiết":
        if st.session_state.phan_quyen == "4" and st.session_state.username not in [
            st.secrets["user_special"]["u1"],
            st.secrets["user_special"]["u2"],
            st.secrets["user_special"]["u3"]
        ]:
            bo_cot = bo_cot.drop("Khoa",axis=1)
        return bo_cot
    else:
        # Xóa các cột không cần thiết
        bo_cot = bo_cot.drop(["Timestamp", "Tên người đánh giá", "Tên người thực hiện"], axis=1)
        # Nhóm lại bảng đó theo khoa và tên quy trình
        ket_qua = bo_cot.groupby(["Khoa", "Tên chỉ số chăm sóc"]).agg({
            "Tên chỉ số chăm sóc": "count",
            "Tỉ lệ tuân thủ": "mean",
        }).rename(columns={"Tên chỉ số chăm sóc": "Số lượt"}).reset_index()
        # Sort kết quả theo tên khoa
        ket_qua = ket_qua.sort_values("Khoa")
        ket_qua = ket_qua.sort_values("Tên chỉ số chăm sóc")
        # Gắn thêm cột số thứ tự
        ket_qua.insert(0, 'STT', range(1, len(ket_qua) + 1))
        if st.session_state.phan_quyen == "4" and st.session_state.username not in [
            st.secrets["user_special"]["u1"],
            st.secrets["user_special"]["u2"],
            st.secrets["user_special"]["u3"]
        ]:
            ket_qua = ket_qua.drop("Khoa", axis=1)
        return ket_qua
    
def chon_cscs(ten_cscs):
    placeholder1 = st.empty()
    if st.checkbox("Chọn tất cả chỉ số"):
        placeholder1.empty()
        cscs_select = "All"
    else:
        with placeholder1:
            cscs_select = st.multiselect(label="Chọn tên chỉ số chăm sóc",
                                            options= ten_cscs.unique())
    return cscs_select


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
        <p style="color:green">THỐNG KÊ CHỈ SỐ CHĂM SÓC ĐIỀU DƯỠNG</p>
        </div>
    </div>
    <div class="header-underline"></div>

 """, unsafe_allow_html=True)
html_code = f'<p class="demuc"><i>Nhân viên: {st.session_state.username}</i></p>'
st.html(html_code)
sheeti1 = st.secrets["sheet_name"]["input_1"]
sheeti7 = st.secrets["sheet_name"]["input_7"]
data1 = load_data1(sheeti1)
data7 = load_data1(sheeti7)
khoa = data1["Khoa"]
ten_cscs = data7["Tên chỉ số chăm sóc"]
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
    cscs_select = chon_cscs(ten_cscs)
    khoa_select = chon_khoa(khoa)
    submit_thoigian = st.form_submit_button("OK")
if submit_thoigian:
    if ed < sd:
        st.error("Lỗi ngày kết thúc đến trước ngày bắt đầu. Vui lòng chọn lại")  
    else:
        sheeto7 = st.secrets["sheet_name"]["output_7"]
        data = load_data(sheeto7,sd,ed,khoa_select)
        if data.empty:
            st.toast("Không có dữ liệu theo yêu cầu")
        else:
            if cscs_select != "All":
               data = data[data["Tên chỉ số chăm sóc"].isin(cscs_select)]
            with st.expander("Thống kê tổng quát"):
                thongke = tao_thong_ke(data,"Tổng quát")
                st.dataframe(thongke, 
                            hide_index=True, 
                            column_config = {
                                "Tỉ lệ tuân thủ": st.column_config.NumberColumn(format="%.2f %%")
                                })
            with st.expander("Thống kê chi tiết"):
                thongkechitiet = tao_thong_ke(data,"Chi tiết")
                st.dataframe(thongkechitiet,
                            hide_index=True, 
                            column_config = {
                                "Tỉ lệ tuân thủ": st.column_config.NumberColumn(format="%.2f %%")
                                })
powerbi_url = "https://app.powerbi.com/groups/fbea42ac-f40a-4ada-bdbe-95cd1dc34b62/reports/e4d93ac2-150f-4e45-9932-e93fc32666e8/ReportSection?experience=power-bi"
st.markdown(f"[📊 Xem báo cáo chi tiết tại Power BI]({powerbi_url})", unsafe_allow_html=True)


    


