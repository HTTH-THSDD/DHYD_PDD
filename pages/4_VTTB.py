import streamlit as st
import pandas as pd
import gspread
from datetime import datetime
from zoneinfo import ZoneInfo
import pathlib
import base64
from google.oauth2.service_account import Credentials
# FS

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

@st.cache_data(ttl=3600)
def load_data(x):
    credentials = load_credentials()
    gc = gspread.authorize(credentials)
    sheet = gc.open(x).sheet1
    data = sheet.get_all_values()
    header = data[0]
    values = data[1:]
    data_final = pd.DataFrame(values, columns=header)
    return data_final

def thong_tin_hanh_chinh():
    sheeti5 = st.secrets["sheet_name"]["input_5"]
    data_khoa = load_data(sheeti5) 
    chon_khoa = st.selectbox("Khoa/Đơn vị báo cáo ",
                             options=data_khoa["Khoa"].unique(),
                             index=None,
                             placeholder="",
                             )
    if chon_khoa:
        st.session_state.khoa_VTTB = chon_khoa
        ckx = data_khoa.loc[data_khoa["Khoa"]==chon_khoa]
        st.session_state.thiet_bi = ckx
        st.session_state.ten_thiet_bi =  ckx["Tên thiết bị"].iloc[0]
    else:
        if "khoa_VTTB" in st.session_state:
            del st.session_state["khoa_VTTB"]
def kiem_tra():
    so_thiet_bi_thieu=[]
    for i in range (0, len(st.session_state.thiet_bi)):
        if (
            f"trong_{i}" not in st.session_state or st.session_state[f"trong_{i}"] is None
        ) or (
            f"hu_{i}" not in st.session_state or st.session_state[f"hu_{i}"] is None
        ):
            so_thiet_bi_thieu.append(f"{st.session_state.thiet_bi['Tên thiết bị'].iloc[i]}")
    return so_thiet_bi_thieu

@st.dialog("Thông báo")
def warning(a):
    st.warning(f"Vui lòng điền đầy đủ thông tin thiết bị: {', '.join(a)}")

def upload_data_VTTB():
    credentials = load_credentials()
    gc = gspread.authorize(credentials)
    sheeto5 = st.secrets["sheet_name"]["output_5"]
    sheet = gc.open(sheeto5).sheet1
    column_index = len(sheet.get_all_values())  
    now_vn = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))  
    column_timestamp = now_vn.strftime('%Y-%m-%d %H:%M:%S')
    column_ngay_bao_cao = st.session_state.ngay_bao_cao.strftime('%Y-%m-%d')
    column_khoa_bao_cao = str(st.session_state.khoa_VTTB)
    column_nguoi_bao_cao = str(st.session_state.username)
    column_tb_thong_thuong = ""
    for i in range (0, len(st.session_state.thiet_bi)):
        ten = st.session_state.thiet_bi['Tên thiết bị'].iloc[i]
        co_so = str(st.session_state[f"co_so_{i}"])
        dang_su_dung = str(st.session_state[f"dang_su_dung_{i}"])
        trong = str(st.session_state[f"trong_{i}"]) 
        hu = str(st.session_state[f"hu_{i}"])
        column_tb_thong_thuong += ten + "|" + co_so + "|" + dang_su_dung + "|" + trong + "|" + hu + "#"
    column_SCD_bo_sung = ""
    SCD_so_bn = str(st.session_state[f"chua_thuc_hien_{i}"])
    SCD_nguyen_nhan = str(st.session_state[f"nguyen_nhan_{i}"])
    if SCD_so_bn != 0 and SCD_nguyen_nhan != "":
        column_SCD_bo_sung += SCD_so_bn + "|" + SCD_nguyen_nhan

    columnn_SCD_muon_khoa_khac =""
    for idx in st.session_state.additional_columns:
        SCD_muon_khoa_khac = st.session_state[f"muon_tu_khoa_khac_{idx}"]
        SCD_so_luong_muon = str(st.session_state[f"so_luong_muon_{idx}"])
        if SCD_muon_khoa_khac != "--Chọn khoa--" and SCD_so_luong_muon != 0:
                columnn_SCD_muon_khoa_khac += SCD_muon_khoa_khac + ":" + SCD_so_luong_muon + "+"
    if columnn_SCD_muon_khoa_khac != "":
        columnn_SCD_muon_khoa_khac = columnn_SCD_muon_khoa_khac.rstrip("+")

    columnn_SCD_cho_khoa_khac_muon =""
    for idx in st.session_state.additional_columns_2:
        SCD_cho_khoa_khac = st.session_state[f"cho_khoa_khac_muon{idx}"]
        SCD_so_luong_cho_muon = str(st.session_state[f"so_luong_cho_muon_{idx}"])
        if SCD_cho_khoa_khac != "--Chọn khoa--" and SCD_so_luong_cho_muon != 0:
                columnn_SCD_cho_khoa_khac_muon += SCD_cho_khoa_khac + ":" + SCD_so_luong_cho_muon + "+"
    if columnn_SCD_cho_khoa_khac_muon != "":
        columnn_SCD_cho_khoa_khac_muon = columnn_SCD_cho_khoa_khac_muon.rstrip("+")

    sheet.append_row([column_index,column_timestamp, column_ngay_bao_cao, column_khoa_bao_cao, column_nguoi_bao_cao, column_tb_thong_thuong, column_SCD_bo_sung, columnn_SCD_muon_khoa_khac, columnn_SCD_cho_khoa_khac_muon])
    st.toast("Báo cáo đã được gửi thành công")
# Main Section ####################################################################################
css_path = pathlib.Path("asset/style_4_VTTB.css")
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
        <p>BÁO CÁO THIẾT BỊ HẰNG NGÀY</p>
        </div>
    </div>
    <div class="header-underline"></div>
 """, unsafe_allow_html=True)
html_code = f'<p class="demuc"><i>Nhân viên báo cáo: {st.session_state.username}</i></p>'
st.html(html_code)

thong_tin_hanh_chinh()
sheeti5 = st.secrets["sheet_name"]["input_5"]
data_vttb = load_data(sheeti5)
now_vn = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
st.date_input(
    label="Ngày báo cáo",
    value=now_vn.date(),
    format="DD/MM/YYYY",
    key="ngay_bao_cao",
    max_value=now_vn.date(),
) 

st.markdown("""
    <hr style="border: 1.325px solid #195e83; margin: 15px 0;">
    <p style="font-size: 13.5px; color: #333;"> 📌
        <i><span style="color: #f7270b; font-weight: bold;">Lưu ý:</span>
            Báo cáo số máy <span style="color: #042f66; font-weight: bold;">ĐANG DÙNG</span> = 
            số máy <span style="color: #042f66; font-weight: bold;">CỦA KHOA ĐANG DÙNG</span> + 
            số máy <span style="color: #042f66; font-weight: bold;">MƯỢN</span> từ khoa khác <span style="color: #042f66; font-weight: bold;">ĐANG DÙNG</span>
        <br><span style="color: #042f66; font-weight: bold;">(không tính số máy đang cho khoa khác mượn)</span>
        <br><br>
        </i>
    </p>
""", unsafe_allow_html=True)

if "khoa_VTTB" in st.session_state and st.session_state["khoa_VTTB"] is not None:
    thiet_bi = st.session_state.thiet_bi
    
    for i in range(0, len(thiet_bi)):
        ten = thiet_bi['Tên thiết bị'].iloc[i]
        Ten_thiet_bi = f"{thiet_bi['Mã thiết bị'].iloc[i]}: {thiet_bi['Tên thiết bị'].iloc[i]}"
        st.markdown(f'''
                <p style="font-size: 15px; 
                    color: #005259; 
                    font-family: 'Source Sans Pro', sans-serif; 
                    font-weight: bold;">
                    {Ten_thiet_bi}
                </p>
                ''', unsafe_allow_html=True
                )
        # st.markdown(f'''<div class="divider">''', unsafe_allow_html=True)
        # st.markdown('''
        #     <style>
        #     .divider .stHorizontalBlock {
        #         display: flex;
        #         flex-wrap: wrap;
        #         gap: 10px !important;
        #     }
        #     .divider .stHorizontalBlock > div {
        #         width: 100px !important;
        #         min-width: 100px !important;
        #         max-width: 100px !important;
        #     }
        #     </style>
        #     ''', unsafe_allow_html=True)

        ma_thiet_bi = thiet_bi['Mã thiết bị'].iloc[i]
        col1, col2, col3, col4  = st.columns([1, 1, 1, 1])
        with col1:
            thiet_bi['2025'] = pd.to_numeric(thiet_bi['2025'],errors='coerce')
            SL = int(thiet_bi['2025'].iloc[i]) if pd.notnull(thiet_bi['2025'].iloc[i]) else 0
            st.number_input(
                label="Cơ số",
                value=SL,  # Chuyển đổi giá trị thành số nguyên
                disabled =True, # Chỉ cho phép đọc
                key=f"co_so_{i}"
            )    
        with col2:
            st.number_input(
                label="Đang dùng",
                value=SL,  # Chuyển đổi giá trị thành số nguyên
                step=1,
                key=f"dang_su_dung_{i}",
                min_value=0,
            )
        with col3:
            st.number_input(
                label="Trống",
                step=1,
                key=f"trong_{i}",
                value=0,
                min_value=0,
                )
        with col4:
            st.number_input(
                label="Hư",
                step=1,
                key=f"hu_{i}",
                value=0,
                min_value=0,
                )
                 
        # st.markdown(f'''</div class="divider">''', unsafe_allow_html=True)
        if ma_thiet_bi[0] != "A":
            with st.expander(f"Thông tin bổ sung thiết bị {ten}", expanded=False):
                st.number_input(
                        label="Số người bệnh có chỉ định sử dụng máy SCD nhưng chưa thực hiện",
                        min_value=0,
                        step=1,
                        key=f"chua_thuc_hien_{i}",
                    )
                st.selectbox(
                        label="Nguyên nhân người bệnh chưa được sử dụng máy SCD",
                        options=["", "Không có máy", "Không có vớ", "Nguyên nhân khác"],
                        key=f"nguyen_nhan_{i}",
                    )

                # Hai cột: mượn từ khoa khác | cho khoa khác mượn
                st.markdown(f'''
                <p style="font-size: 15px; 
                    color: #005259; 
                    font-family: 'Source Sans Pro', sans-serif; 
                    font-weight: bold;">
                    {ten} mượn từ khoa khác
                </p>
                ''', unsafe_allow_html=True)
                if "additional_columns" not in st.session_state:
                    st.session_state.additional_columns = [1]
                for idx in st.session_state.additional_columns:
                    c1, c2 = st.columns([7, 3])
                    with c1:
                        st.selectbox(
                            label="-",
                            options=["--Chọn khoa--"] + list(data_vttb["Khoa"].unique()),
                            key=f"muon_tu_khoa_khac_{idx}",
                        )
                    with c2:
                        st.number_input(
                            label="-",
                            step=1,
                            key=f"so_luong_muon_{idx}",
                        )
                c_add, c_remove = st.columns([1, 1])
                with c_add:
                    if st.button("Thêm lựa chọn", key=f"them_lua_chon"):
                        st.session_state.additional_columns.append(len(st.session_state.additional_columns) + 1)
                        st.rerun()
                with c_remove:
                    if st.button("Xóa", key=f"xoa_lua_chon"):
                        if len(st.session_state.additional_columns) > 1:
                            st.session_state.additional_columns.pop()
                            st.rerun()
                st.markdown(f'''
                <p style="font-size: 15px; 
                    color: #005259; 
                    font-family: 'Source Sans Pro', sans-serif; 
                    font-weight: bold;">
                    {ten} cho khoa khác mượn
                </p>
                ''', unsafe_allow_html=True)
                if "additional_columns_2" not in st.session_state:
                    st.session_state.additional_columns_2 = [1]
                for idx in st.session_state.additional_columns_2:
                    c1, c2 = st.columns([7, 3])
                    with c1:
                        st.selectbox(
                            label="-",
                            options=["--Chọn khoa--"] + list(data_vttb["Khoa"].unique()),
                            key=f"cho_khoa_khac_muon{idx}",
                        )
                    with c2:
                        st.number_input(
                            label="-",
                            step=1,
                            key=f"so_luong_cho_muon_{idx}",
                        )
                c_add, c_remove = st.columns([1, 1])
                with c_add:
                    if st.button("Thêm lựa chọn", key=f"them_lua_chon_2"):
                        st.session_state.additional_columns_2.append(len(st.session_state.additional_columns_2) + 1)
                        st.rerun()
                with c_remove:
                    if st.button("Xóa", key=f"xoa_lua_chon_2"):
                        if len(st.session_state.additional_columns_2) > 1:
                            st.session_state.additional_columns_2.pop()
                            st.rerun()

        # Nút gửi
    submitbutton = st.button("Lưu kết quả",type='primary',key="luu")
    if submitbutton:
        a = kiem_tra()
        if len(a) == 0:
            upload_data_VTTB()
        else:
            warning(a)
else:
    st.warning("Vui lòng chọn khoa cần báo cáo")

