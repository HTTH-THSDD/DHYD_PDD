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
def kiem_tra_tong():
    thong_bao_loi=[]
    for i in range(0, len(st.session_state.thiet_bi)):
        ten_thiet_bi = st.session_state.thiet_bi['Tên thiết bị'].iloc[i] 
        if f"dang_su_dung_{i}" not in st.session_state or st.session_state[f"dang_su_dung_{i}"] is None:
            thong_bao_loi.append(f'{ten_thiet_bi} - số liệu Đang dùng chưa được báo cáo')
        if f"trong_{i}" not in st.session_state or st.session_state[f"trong_{i}"] is None:
            thong_bao_loi.append(f'{ten_thiet_bi} - số liệu Trống chưa được báo cáo')
        if f"hu_{i}" not in st.session_state or st.session_state[f"hu_{i}"] is None:
            thong_bao_loi.append(f'{ten_thiet_bi} - số liệu Hư chưa được báo cáo')
    return thong_bao_loi


def kiem_tra_may_SCD():
    """
    Kiểm tra số lượng máy SCD
    Công thức: Đang dùng - Tổng mượn + Tổng cho mượn + Trống + Hư = Cơ số
    """
    thong_bao_loi_SCD = []
    for i in range(0, len(st.session_state.thiet_bi)):
        ma_thiet_bi = st.session_state.thiet_bi['Mã thiết bị'].iloc[i]
        if ma_thiet_bi[0] != "A":
            ten_thiet_bi = st.session_state.thiet_bi['Tên thiết bị'].iloc[i]
            co_so = st.session_state.get(f"co_so_{i}", 0)
            dang_su_dung = st.session_state.get(f"dang_su_dung_{i}", 0)
            trong = st.session_state.get(f"trong_{i}", 0)
            hu = st.session_state.get(f"hu_{i}", 0)
            
            # Tính tổng số lượng mượn từ khoa khác
            tong_muon = 0
            if "them_cot_muon" in st.session_state:
                for idx in st.session_state.them_cot_muon:
                    khoa_muon = st.session_state.get(f"muon_tu_khoa_khac_{idx}", "--Chọn khoa--")
                    so_luong_muon = st.session_state.get(f"so_luong_muon_{idx}", 0)
                    if khoa_muon != "--Chọn khoa--" and so_luong_muon is not None:
                        tong_muon += so_luong_muon 
            # Tính tổng số lượng cho khoa khác mượn
            tong_cho_muon = 0
            if "them_cot_cho_muon" in st.session_state:
                for idx in st.session_state.them_cot_cho_muon:
                    khoa_cho_muon = st.session_state.get(f"cho_khoa_khac_muon{idx}", "--Chọn khoa--")
                    so_luong_cho_muon = st.session_state.get(f"so_luong_cho_muon_{idx}", 0)
                    if khoa_cho_muon != "--Chọn khoa--" and so_luong_cho_muon is not None:
                        tong_cho_muon += so_luong_cho_muon
            # Áp dụng công thức: Đang dùng - Tổng mượn + Tổng cho mượn + Trống + Hư = Cơ số
            ket_qua = dang_su_dung - tong_muon + tong_cho_muon + trong + hu
            
            if ket_qua != co_so:
                chenh_lech = ket_qua - co_so
                thong_bao_loi_SCD.append(
                    f'Cơ số: {co_so}, Tổng tính: {ket_qua}, Số liệu chênh lệch: {chenh_lech:+d} máy'
                )  
    return thong_bao_loi_SCD

@st.dialog("Thông báo")
def warning(danh_sach_loi):
    if not danh_sach_loi:
        return
    content = "Vui lòng điền đầy đủ thông tin thiết bị:\n\n" + "\n".join(f"- {loi}" for loi in danh_sach_loi)
    st.warning(content)
    st.info("💡 **Lưu ý:** Nếu số lượng là 0, vui lòng nhập số 0.")

@st.dialog("Báo cáo máy SCD chưa chính xác")
def warning_SCD(danh_sach_loi_SCD):
    if not danh_sach_loi_SCD:
        return 
    Loi_SCD = "**Số liệu thiết bị SCD chưa chính xác:**\n\n"  +  "\n".join(f"- {loi}" for loi in danh_sach_loi_SCD) 
    st.error(Loi_SCD)


def upload_data_VTTB():
    try:
        # Sử dụng hàm load_credentials() đã có
        credentials = load_credentials()
        gc = gspread.authorize(credentials)
        sheeto5 = st.secrets["sheet_name"]["output_5"]
        spreadsheet = gc.open(sheeto5)
        sheet = spreadsheet.get_worksheet(0)
        # Lấy tất cả giá trị để tìm dòng cuối cùng
        all_values = sheet.get_all_values()
        last_row = len(all_values)
        next_row = last_row + 1 
        # Tạo STT mới từ dòng cuối
        if last_row > 1:
            try:
                last_stt = int(all_values[-1][0])
                new_stt = last_stt + 1
            except:
                new_stt = last_row
        else:
            new_stt = 1
        
        # Chuẩn bị dữ liệu timestamp và thông tin hành chính
        now_vn = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))  
        column_timestamp = now_vn.strftime('%Y-%m-%d %H:%M:%S')
        column_ngay_bao_cao = st.session_state.ngay_bao_cao.strftime('%Y-%m-%d')
        column_khoa_bao_cao = str(st.session_state.khoa_VTTB)
        column_nguoi_bao_cao = str(st.session_state.username)
        
        # Xử lý dữ liệu thiết bị thông thường
        column_tb_thong_thuong = ""
        for i in range(0, len(st.session_state.thiet_bi)):
            ten = st.session_state.thiet_bi['Tên thiết bị'].iloc[i]
            co_so = str(st.session_state.get(f"co_so_{i}", 0))
            dang_su_dung = str(st.session_state.get(f"dang_su_dung_{i}", 0))
            trong = str(st.session_state.get(f"trong_{i}", 0)) 
            hu = str(st.session_state.get(f"hu_{i}", 0))
            column_tb_thong_thuong += ten + "|" + co_so + "|" + dang_su_dung + "|" + trong + "|" + hu + "#"
        
        # Xử lý dữ liệu SCD bổ sung
        column_SCD_bo_sung = ""
        last_index = len(st.session_state.thiet_bi) - 1
        SCD_so_bn = str(st.session_state.get(f"chua_thuc_hien_{last_index}", 0))
        SCD_nguyen_nhan = str(st.session_state.get(f"nguyen_nhan_{last_index}", ""))
        if SCD_so_bn != "0" and SCD_nguyen_nhan != "":
            column_SCD_bo_sung += SCD_so_bn + "|" + SCD_nguyen_nhan

        # Xử lý dữ liệu SCD mượn từ khoa khác
        columnn_SCD_muon_khoa_khac = ""
        if "them_cot_muon" in st.session_state:
            for idx in st.session_state.them_cot_muon:
                SCD_muon_khoa_khac = st.session_state.get(f"muon_tu_khoa_khac_{idx}", "--Chọn khoa--")
                SCD_so_luong_muon = str(st.session_state.get(f"so_luong_muon_{idx}", 0))
                if SCD_muon_khoa_khac != "--Chọn khoa--" and SCD_so_luong_muon != "0":
                    columnn_SCD_muon_khoa_khac += SCD_muon_khoa_khac + ":" + SCD_so_luong_muon + "+"
        if columnn_SCD_muon_khoa_khac != "":
            columnn_SCD_muon_khoa_khac = columnn_SCD_muon_khoa_khac.rstrip("+")
        # Xử lý dữ liệu SCD cho khoa khác mượn
        columnn_SCD_cho_khoa_khac_muon = ""
        if "them_cot_cho_muon" in st.session_state:
            for idx in st.session_state.them_cot_cho_muon:
                SCD_cho_khoa_khac = st.session_state.get(f"cho_khoa_khac_muon{idx}", "--Chọn khoa--")
                SCD_so_luong_cho_muon = str(st.session_state.get(f"so_luong_cho_muon_{idx}", 0))
                if SCD_cho_khoa_khac != "--Chọn khoa--" and SCD_so_luong_cho_muon != "0":
                    columnn_SCD_cho_khoa_khac_muon += SCD_cho_khoa_khac + ":" + SCD_so_luong_cho_muon + "+"
        if columnn_SCD_cho_khoa_khac_muon != "":
            columnn_SCD_cho_khoa_khac_muon = columnn_SCD_cho_khoa_khac_muon.rstrip("+")
        # Tạo row mới
        new_row = [
            new_stt,
            column_timestamp, 
            column_ngay_bao_cao, 
            column_khoa_bao_cao, 
            column_nguoi_bao_cao, 
            column_tb_thong_thuong, 
            column_SCD_bo_sung, 
            columnn_SCD_muon_khoa_khac, 
            columnn_SCD_cho_khoa_khac_muon
        ]
        # Ghi dữ liệu vào dòng tiếp theo (fix lỗi replace)
        range_to_update = f'A{next_row}:I{next_row}'
        sheet.update(range_to_update, [new_row], value_input_option='USER_ENTERED')
        
        st.toast("✅ Báo cáo đã được gửi thành công")
        # Clear cache để load data mới
        st.cache_data.clear()   
    except Exception as e:
        st.error(f"❌ Lỗi khi upload dữ liệu: {str(e)}")
        import traceback
        st.code(traceback.format_exc())


def clear_session_state():
    keys_to_clear = ["khoa_VTTB", "thiet_bi", "ten_thiet_bi"]
    if "thiet_bi" in st.session_state:
        for i in range(0, len(st.session_state.thiet_bi)):
            keys_to_clear.extend([
                f"co_so_{i}",
                f"dang_su_dung_{i}",
                f"trong_{i}",
                f"hu_{i}",
                f"chua_thuc_hien_{i}",
                f"nguyen_nhan_{i}"
            ])
    if "them_cot_muon" in st.session_state:
        for idx in st.session_state.them_cot_muon:
            keys_to_clear.extend([
                f"muon_tu_khoa_khac_{idx}",
                f"so_luong_muon_{idx}"
            ])
        keys_to_clear.append("them_cot_muon")
    if "them_cot_cho_muon" in st.session_state:
        for idx in st.session_state.them_cot_cho_muon:
            keys_to_clear.extend([
                f"cho_khoa_khac_muon{idx}",
                f"so_luong_cho_muon_{idx}"
            ])
        keys_to_clear.append("them_cot_cho_muon")

    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key] 
    st.rerun()

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
                #value=SL,  # Chuyển đổi giá trị thành số nguyên
                step=1,
                key=f"dang_su_dung_{i}",
                min_value=0,
                value=None,    
            )
        with col3:
            st.number_input(
                label="Trống",
                step=1,
                key=f"trong_{i}",
                min_value=0,
                value=None, 
                )
        with col4:
            st.number_input(
                label="Hư",
                step=1,
                key=f"hu_{i}",
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
                if "them_cot_muon" not in st.session_state:
                    st.session_state.them_cot_muon = [1]
                for idx in st.session_state.them_cot_muon:
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
                        st.session_state.them_cot_muon.append(len(st.session_state.them_cot_muon) + 1)
                        st.rerun()
                with c_remove:
                    if st.button("Xóa", key=f"xoa_lua_chon"):
                        if len(st.session_state.them_cot_muon) > 1:
                            st.session_state.them_cot_muon.pop()
                            st.rerun()
                st.markdown(f'''
                <p style="font-size: 15px; 
                    color: #005259; 
                    font-family: 'Source Sans Pro', sans-serif; 
                    font-weight: bold;">
                    {ten} cho khoa khác mượn
                </p>
                ''', unsafe_allow_html=True)
                if "them_cot_cho_muon" not in st.session_state:
                    st.session_state.them_cot_cho_muon = [1]
                for idx in st.session_state.them_cot_cho_muon:
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
                        st.session_state.them_cot_cho_muon.append(len(st.session_state.them_cot_cho_muon) + 1)
                        st.rerun()
                with c_remove:
                    if st.button("Xóa", key=f"xoa_lua_chon_2"):
                        if len(st.session_state.them_cot_cho_muon) > 1:
                            st.session_state.them_cot_cho_muon.pop()
                            st.rerun()

        # Nút gửi
    submitbutton = st.button("Lưu kết quả", type='primary', key="luu")
    if submitbutton:
        loi_bat_buoc = kiem_tra_tong()
        if len(loi_bat_buoc) > 0:
            warning(loi_bat_buoc)
        else:
            loi_SCD = kiem_tra_may_SCD()
            if len(loi_SCD) > 0:
                warning_SCD(loi_SCD)
            else:
                upload_data_VTTB()
                clear_session_state()
else:
    st.warning("Vui lòng chọn khoa cần báo cáo")

