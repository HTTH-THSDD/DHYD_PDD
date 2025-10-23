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
        khoa_select = data["Khoa"]
    data = data.loc[data["Khoa"].isin(khoa_select)]
    data['Timestamp'] = pd.to_datetime(data['Timestamp'], errors='coerce')
    start_date = sd
    end_date = ed + timedelta(days=1)
    data_final = data[(data['Timestamp'] >= pd.Timestamp(start_date)) & (data['Timestamp'] < pd.Timestamp(end_date))]
    return data_final

def chuyendoi_phantram(df,x):
    df[x] = df[x].str.replace(',', '.')
    df[x] = pd.to_numeric(df[x], errors='coerce')
    df[x] = df[x] * 100
    return df

def tao_thong_ke(x,y):
    df = pd.DataFrame(x)
    if y == "Chi tiết":
        df = pd.DataFrame(df).sort_values("Khoa")
        df = pd.DataFrame(df).sort_values("Timestamp", ascending=True)
        df = chuyendoi_phantram(df,"Tỉ lệ bước đúng, đủ")
        df = chuyendoi_phantram(df,"Tỉ lệ bước đúng, nhưng chưa đủ")
        df = chuyendoi_phantram(df,"Tỉ lệ bước Không thực hiện hoặc ghi sai")
        df = df.drop("Data",axis=1)
        if st.session_state.phan_quyen == "4" and st.session_state.username not in [st.secrets["user_special"]["u1"],st.secrets["user_special"]["u2"],st.secrets["user_special"]["u3"]]:
            df = df.drop("Khoa",axis=1)
        return df
    else:
        df = pd.DataFrame(df).drop("STT",axis=1)
        df = pd.DataFrame(df).sort_values("Khoa")
        df = chuyendoi_phantram(df,"Tỉ lệ bước đúng, đủ")
        df = chuyendoi_phantram(df,"Tỉ lệ bước đúng, nhưng chưa đủ")
        df = chuyendoi_phantram(df,"Tỉ lệ bước Không thực hiện hoặc ghi sai")
        df["Tháng"] = df["Timestamp"].dt.strftime("%m/%Y")
        df = df.groupby(["Tháng","Khoa"]).agg({
        "Tháng": "count",
        "Tỉ lệ bước đúng, đủ": "mean",
        "Tỉ lệ bước đúng, nhưng chưa đủ": "mean",
        "Tỉ lệ bước Không thực hiện hoặc ghi sai": "mean",
        }).rename(columns={"Tháng": "Số lượt"}).reset_index()
        df.insert(0, 'STT', range(1, len(df) + 1))
        if st.session_state.phan_quyen == "4" and st.session_state.username not in [st.secrets["user_special"]["u1"],st.secrets["user_special"]["u2"],st.secrets["user_special"]["u3"]]:
            df=df.drop("Khoa",axis=1)
        return df

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
        
def tinh_metrics(data):
    """Tính các metrics để hiển thị trên thẻ"""
    # Lượt danh gia
    luot_danh_gia = len(data)
    # Số khoa
    so_khoa = data['Khoa'].nunique()
    # Các tỉ lệ
    data_temp = data.copy()
    data_temp['Tỉ lệ bước đúng, đủ'] = data_temp['Tỉ lệ bước đúng, đủ'].astype(str).str.replace(',', '.')
    data_temp['Tỉ lệ bước đúng, đủ'] = pd.to_numeric(data_temp['Tỉ lệ bước đúng, đủ'], errors='coerce')
    mean_value = data_temp['Tỉ lệ bước đúng, đủ'].mean() * 100
    tl_dung_du = float(format(mean_value, '.2f'))  # Format với 2 chữ số thập phân
    
    return {
        'luot_danh_gia': luot_danh_gia,
        'so_khoa': so_khoa,
        'tl_dung_du': tl_dung_du,
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
        <p style="color:green">THỐNG KÊ HỒ SƠ BỆNH ÁN</p>
        </div>
    </div>
    <div class="header-underline"></div>

 """, unsafe_allow_html=True)
html_code = f'<p class="demuc"><i>Nhân viên: {st.session_state.username}</i></p>'
st.html(html_code)
sheeti1 = st.secrets["sheet_name"]["input_1"]
data = load_data1(sheeti1)
khoa = data["Khoa"]
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
        sheeto2 = st.secrets["sheet_name"]["output_2"]
        data = load_data(sheeto2,sd,ed,khoa_select)
        if data.empty:
            st.toast("Không có dữ liệu theo yêu cầu")
        else:
            metrics = tinh_metrics(data)
            col1, col2, col3 = st.columns([1,1,1])
            with col1:
                st.metric("**:red[Lượt đánh giá]**", f"{metrics['luot_danh_gia']:,}",border=True)
            with col2:
                st.metric("**:red[Số khoa]**", metrics['so_khoa'],border=True)
            with col3:
                if metrics['tl_dung_du'] is not None:
                    if metrics['tl_dung_du'] != 100:
                        st.metric("**:red[Tỉ lệ số bước đúng,đủ]**", f"{metrics['tl_dung_du']:.2f}%",border=True)
                    else:
                        st.metric("**:red[Tỉ lệ số bước đúng,đủ]**", f"{metrics['tl_dung_du']:.0f}%",border=True)                
                else:
                    st.metric("**:red[Tỉ lệ số bước đúng,đủ]**", "-")
            with st.expander("**:blue[Thống kê tổng quát]**"):
                thongke = tao_thong_ke(data,"Tổng quát")
                st.dataframe(thongke, 
                            hide_index=True,
                            column_config = {
                                    "Tỉ lệ bước đúng, đủ": st.column_config.NumberColumn(format="%.2f %%"),
                                    "Tỉ lệ bước đúng, nhưng chưa đủ": st.column_config.NumberColumn(format="%.2f %%"),
                                    "Tỉ lệ bước Không thực hiện hoặc ghi sai": st.column_config.NumberColumn(format="%.2f %%"),
                                    })
            with st.expander("**:blue[Thống kê chi tiết]**"):
                thongkechitiet = tao_thong_ke(data,"Chi tiết")
                st.dataframe(thongkechitiet,
                        hide_index=True,
                        column_config = {
                                    "Tỉ lệ bước đúng, đủ": st.column_config.NumberColumn(format="%.2f %%"),
                                    "Tỉ lệ bước đúng, nhưng chưa đủ": st.column_config.NumberColumn(format="%.2f %%"),
                                    "Tỉ lệ bước Không thực hiện hoặc ghi sai": st.column_config.NumberColumn(format="%.2f %%"),
                                    })
powerbi_url = "https://app.powerbi.com/groups/fbea42ac-f40a-4ada-bdbe-95cd1dc34b62/reports/99d39735-915d-4541-b91e-b0a79a6f861e/ReportSection24ec544e962f63829565?experience=power-bi"
st.markdown(f"[📊 Xem báo cáo chi tiết tại Power BI]({powerbi_url})", unsafe_allow_html=True)

    


