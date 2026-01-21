import streamlit as st
import pandas as pd
import gspread
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
import pathlib
import base64
from google.oauth2.service_account import Credentials
import plotly.express as px

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
        with open(file_path, 'r', encoding='latin-1') as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

css_path = pathlib.Path("asset/style.css")

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
    credentials = Credentials.from_service_account_info(
        creds_info,
        scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    )
    return credentials

@st.cache_data(ttl=10)
def load_data_full(sheet_name):
    """Load full data from Google Sheets"""
    credentials = load_credentials()
    gc = gspread.authorize(credentials)
    sheet = gc.open(sheet_name).sheet1
    data = sheet.get_all_values()
    header = data[0]
    values = data[1:]
    df = pd.DataFrame(values, columns=header)
    return df

@st.cache_data(ttl=10)
def load_data_filtered(sheet_name, sd, ed, khoa_list, nv_list=None, loai_bch_list=None):
    """Load and filter data based on date range, departments, employees and quiz types"""
    credentials = load_credentials()
    gc = gspread.authorize(credentials)
    sheet = gc.open(sheet_name).sheet1
    data = sheet.get_all_values()
    header = data[0]
    values = data[1:]
    df = pd.DataFrame(values, columns=header)
    
    # Filter by department
    if khoa_list and len(khoa_list) > 0:
        df = df[df["Khoa"].isin(khoa_list)]
    
    # Filter by employee
    if nv_list and len(nv_list) > 0:
        df = df[df["Nhân viên"].isin(nv_list)]
    
    # Filter by quiz type (Loại bộ câu hỏi) - lọc từ cột F (output_11)
    if loai_bch_list and len(loai_bch_list) > 0:
        # Tìm cột chứa "Loại bộ câu hỏi" trong output_11
        ten_cot_loai_bch = None
        for cot in df.columns:
            if 'loại' in cot.lower() and 'câu' in cot.lower():
                ten_cot_loai_bch = cot
                break
        
        if ten_cot_loai_bch is None:
            for cot in df.columns:
                if 'loại' in cot.lower() and 'bộ' in cot.lower():
                    ten_cot_loai_bch = cot
                    break
        # Nếu vẫn không tìm thấy, dùng cột F (index 5)
        if ten_cot_loai_bch is None and len(df.columns) > 5:
            ten_cot_loai_bch = df.columns[5]
        # Lọc dựa trên cột Loại bộ câu hỏi
        if ten_cot_loai_bch:
            df = df[df[ten_cot_loai_bch].astype(str).str.strip().isin([str(x).strip() for x in loai_bch_list])]
    
    # Convert timestamp and filter by date
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
    df['Ngày thực hiện'] = pd.to_datetime(df['Ngày thực hiện'], errors='coerce')
    
    start_date = pd.Timestamp(sd)
    end_date = pd.Timestamp(ed) + timedelta(days=1)
    
    df = df[(df['Timestamp'] >= start_date) & (df['Timestamp'] < end_date)]
    
    return df

@st.cache_data(ttl=10)
def load_sheet_specific(sheet_name, worksheet_name):
    """Load dữ liệu từ worksheet cụ thể"""
    credentials = load_credentials()
    gc = gspread.authorize(credentials)
    try:
        sheet = gc.open(sheet_name).worksheet(worksheet_name)
    except:
        sheet = gc.open(sheet_name).get_worksheet(0)
    data = sheet.get_all_values()
    header = data[0]
    values = data[1:]
    df = pd.DataFrame(values, columns=header)
    return df

def parse_ket_qua(chuoi_ket_qua):
    """Phân tích chuỗi kết quả thành các cặp STT-câu trả lời"""
    danh_sach_cap = []
    if not chuoi_ket_qua or pd.isna(chuoi_ket_qua):
        return danh_sach_cap
    chuoi_ket_qua = str(chuoi_ket_qua).strip()
    if chuoi_ket_qua == '':
        return danh_sach_cap
    
    cac_cau_hoi = chuoi_ket_qua.split('#')
    for cau in cac_cau_hoi:
        if not cau or cau.strip() == '':
            continue    
        if '|' in cau:
            phan_tach = cau.split('|', 1)
            stt = phan_tach[0].strip()
            cau_tra_loi = phan_tach[1].strip() if len(phan_tach) > 1 else "Chưa trả lời" 
            if stt:
                danh_sach_cap.append({
                    'STT': stt,
                    'Cau_tra_loi': cau_tra_loi
                })  
    return danh_sach_cap

def tao_tu_dien_dap_an(du_lieu_dap_an):
    """
    Tạo từ điển đáp án với cấu trúc:
    {
        'ma_de': {
            'stt': {
                'loai': 'Trắc nghiệm' hoặc 'Đúng/Sai',
                'dap_an_dung': 'text câu trả lời đúng' (cho trắc nghiệm),
                'danh_sach_dap_an': ['Đúng', 'Sai', 'Đúng', ...] (cho Đúng/Sai)
            }
        }
    }
    """
    tu_dien = {}
    
    # Tìm tên các cột
    ten_cot_ma_de = next((c for c in du_lieu_dap_an.columns if 'đề' in c.lower() or 'de' in c.lower()), du_lieu_dap_an.columns[0])
    ten_cot_stt = next((c for c in du_lieu_dap_an.columns if 'stt' in c.lower() and 'câu' in c.lower()), None)
    if not ten_cot_stt:
        ten_cot_stt = next((c for c in du_lieu_dap_an.columns if 'stt' in c.lower()), du_lieu_dap_an.columns[1])
    
    ten_cot_loai = next((c for c in du_lieu_dap_an.columns if 'loại' in c.lower() and 'câu' in c.lower()), None)
    ten_cot_cau_tra_loi = next((c for c in du_lieu_dap_an.columns if 'câu trả lời' in c.lower()), du_lieu_dap_an.columns[4])
    ten_cot_ket_qua = next((c for c in du_lieu_dap_an.columns if 'kết quả' in c.lower()), du_lieu_dap_an.columns[5])
    
    for _, dong in du_lieu_dap_an.iterrows():
        ma_de = str(dong[ten_cot_ma_de]).strip()
        stt = str(dong[ten_cot_stt]).strip()
        loai_cau_hoi = str(dong[ten_cot_loai]).strip() if ten_cot_loai else ""
        
        if ma_de not in tu_dien:
            tu_dien[ma_de] = {}
        
        # Phân tích câu trả lời và kết quả
        cac_cau_tra_loi_text = str(dong[ten_cot_cau_tra_loi]).split('\n')
        cac_ket_qua_text = str(dong[ten_cot_ket_qua]).split('\n')
        
        cac_cau_tra_loi = [c.strip() for c in cac_cau_tra_loi_text if c.strip()]
        cac_ket_qua = [k.strip() for k in cac_ket_qua_text if k.strip()]
        
        if loai_cau_hoi == "Trắc nghiệm":
            # Tìm câu trả lời có kết quả là "Đúng"
            dap_an_dung = None
            for i, tra_loi in enumerate(cac_cau_tra_loi):
                if i < len(cac_ket_qua) and cac_ket_qua[i].lower() == "đúng":
                    dap_an_dung = tra_loi
                    break
            
            tu_dien[ma_de][stt] = {
                'loai': 'Trắc nghiệm',
                'dap_an_dung': dap_an_dung
            }
        
        elif loai_cau_hoi == "Đúng/Sai":
            # Lưu danh sách kết quả Đúng/Sai cho từng câu
            tu_dien[ma_de][stt] = {
                'loai': 'Đúng/Sai',
                'danh_sach_dap_an': cac_ket_qua
            }
    
    return tu_dien

def thong_ke_chung(du_lieu):
    """Tạo bảng thống kê chung"""
    if du_lieu.empty:
        return pd.DataFrame()
    
    ten_cot_ma_de = next((c for c in du_lieu.columns if 'đề' in c.lower() or 'de' in c.lower()), du_lieu.columns[5])
    
    bang_thong_ke = du_lieu[['Ngày thực hiện', 'Khoa', 'Nhân viên', ten_cot_ma_de, 'Số câu đúng', 'Điểm quy đổi']].copy()
    bang_thong_ke.columns = ['Ngày thực hiện', 'Khoa', 'Nhân viên thực hiện', 'Tên bộ câu hỏi', 'Số câu đúng', 'Điểm quy đổi']
    
    bang_thong_ke['Ngày thực hiện'] = pd.to_datetime(bang_thong_ke['Ngày thực hiện'], errors='coerce').dt.strftime('%Y-%m-%d')
    bang_thong_ke['Điểm quy đổi'] = pd.to_numeric(bang_thong_ke['Điểm quy đổi'], errors='coerce').fillna(0).round(1)
    
    dong_tong = pd.DataFrame([{
        'Ngày thực hiện': '',
        'Khoa': '',
        'Nhân viên thực hiện': '',
        'Tên bộ câu hỏi': 'TRUNG BÌNH',
        'Số câu đúng': '',
        'Điểm quy đổi': bang_thong_ke['Điểm quy đổi'].mean().round(2)
    }])
    bang_thong_ke = pd.concat([bang_thong_ke, dong_tong], ignore_index=True)
    return bang_thong_ke

def thong_ke_chi_tiet(du_lieu, du_lieu_dap_an):
    """Tạo bảng thống kê chi tiết với đối chiếu đáp án chính xác"""
    cac_dong_chi_tiet = []
    
    # Tìm tên cột mã đề
    ten_cot_ma_de = next((c for c in du_lieu.columns if 'đề' in c.lower() or 'de' in c.lower()), 
                         du_lieu.columns[5] if len(du_lieu.columns) > 5 else du_lieu.columns[0])
    
    # Tạo từ điển đáp án
    tu_dien_dap_an = tao_tu_dien_dap_an(du_lieu_dap_an)
    
    for _, dong in du_lieu.iterrows():
        try:
            cac_cap_ket_qua = parse_ket_qua(dong['Kết quả'])
            ma_de = str(dong[ten_cot_ma_de]).strip()
            
            ngay_thuc_hien = pd.to_datetime(dong['Ngày thực hiện'], errors='coerce')
            ngay_thuc_hien_str = ngay_thuc_hien.strftime('%Y-%m-%d') if pd.notna(ngay_thuc_hien) else ''
            
            if ma_de not in tu_dien_dap_an:
                st.warning(f"⚠️ Không tìm thấy đáp án cho mã đề: {ma_de}")
                continue
            
            for cap in cac_cap_ket_qua:
                try:
                    stt = str(cap['STT']).strip()
                    cau_tra_loi_user = str(cap['Cau_tra_loi']).strip()
                    
                    if stt not in tu_dien_dap_an[ma_de]:
                        st.warning(f"⚠️ Không tìm thấy đáp án cho câu {stt} trong mã đề {ma_de}")
                        ket_qua = "?"
                    else:
                        thong_tin_cau = tu_dien_dap_an[ma_de][stt]
                        loai_cau = thong_tin_cau['loai']
                        
                        if cau_tra_loi_user == "" or cau_tra_loi_user == "Chưa trả lời":
                            ket_qua = "Chưa trả lời"
                        
                        elif loai_cau == "Trắc nghiệm":
                            dap_an_dung = thong_tin_cau['dap_an_dung']
                            if cau_tra_loi_user == dap_an_dung:
                                ket_qua = "✓"
                            else:
                                ket_qua = "✗"
                        
                        elif loai_cau == "Đúng/Sai":
                            danh_sach_dap_an_dung = thong_tin_cau['danh_sach_dap_an']
                            cac_tra_loi_user = [t.strip() for t in cau_tra_loi_user.split('-')]
                            
                            # Tính tỷ lệ đúng
                            so_cau_dung = 0
                            tong_so_cau = len(danh_sach_dap_an_dung)
                            
                            for i, dap_an_dung in enumerate(danh_sach_dap_an_dung):
                                if i < len(cac_tra_loi_user):
                                    if cac_tra_loi_user[i].lower() == dap_an_dung.lower():
                                        so_cau_dung += 1
                            
                            # Hiển thị tỷ lệ đúng
                            ket_qua = f"{so_cau_dung}/{tong_so_cau}"
                        else:
                            ket_qua = "?"
                    
                    cac_dong_chi_tiet.append({
                        'Ngày thực hiện': ngay_thuc_hien_str,
                        'Khoa': dong['Khoa'],
                        'Nhân viên thực hiện': dong['Nhân viên'],
                        'Tên bộ câu hỏi': ma_de,
                        'STT câu hỏi': stt,
                        'Câu trả lời của nhân viên': cau_tra_loi_user if cau_tra_loi_user else "Chưa trả lời",
                        'Kết quả': ket_qua
                    })
                
                except Exception as e:
                    st.warning(f"⚠️ Lỗi xử lý câu {cap.get('STT', 'N/A')}: {str(e)}")
                    continue
        
        except Exception as e:
            st.error(f"❌ Lỗi xử lý dòng: {str(e)}")
            continue
    
    if cac_dong_chi_tiet:
        return pd.DataFrame(cac_dong_chi_tiet)
    else:
        st.info("ℹ️ Không có dữ liệu chi tiết để hiển thị")
        return pd.DataFrame()

def to_mau_ket_qua_sai(dong):
    """Làm nổi bật câu trả lời sai"""
    if dong['Kết quả'] == '✗':
        return ['background-color: #ffcccc'] * len(dong)
    if dong['Kết quả'] == 'Chưa trả lời':
        return ['background-color: #ffffcc'] * len(dong)
    elif dong['Kết quả'] not in ['✓', 'Chưa trả lời', '?'] and '/' in str(dong['Kết quả']):
        # Highlight tỷ lệ không đạt 100%
        try:
            parts = str(dong['Kết quả']).split('/')
            if len(parts) == 2 and parts[0] != parts[1]:
                return ['background-color: #ffcccc'] * len(dong)
        except:
            pass
    return [''] * len(dong)

def bang_tra_cuu(du_lieu_input8):
    ten_cot_ma_de = next((c for c in du_lieu_input8.columns if 'đề' in c.lower() or 'de' in c.lower()), du_lieu_input8.columns[0])
    cac_bo_cau_hoi = du_lieu_input8[ten_cot_ma_de].unique().tolist() 
    with st.form("form_tra_cuu"):
        cot1, cot2 = st.columns(2)
        with cot1:
            bo_cau_hoi_duoc_chon = st.selectbox(
                "Tên bộ câu hỏi",
                options=cac_bo_cau_hoi,
                index=0 if cac_bo_cau_hoi else None
            )
        with cot2:
            if bo_cau_hoi_duoc_chon:
                cac_cau_hoi = du_lieu_input8[du_lieu_input8[ten_cot_ma_de] == bo_cau_hoi_duoc_chon]['STT câu hỏi'].unique().tolist()
                cau_hoi_duoc_chon = st.selectbox(
                    "STT câu hỏi",
                    options=["Tất cả"] + cac_cau_hoi,
                    index=0
                )
            else:
                cau_hoi_duoc_chon = None
        
        nut_tra_cuu = st.form_submit_button("Tra cứu")
    
    if nut_tra_cuu and bo_cau_hoi_duoc_chon:
        du_lieu_loc = du_lieu_input8[du_lieu_input8[ten_cot_ma_de] == bo_cau_hoi_duoc_chon].copy()
        if cau_hoi_duoc_chon and cau_hoi_duoc_chon != "Tất cả":
            du_lieu_loc = du_lieu_loc[du_lieu_loc['STT câu hỏi'] == cau_hoi_duoc_chon] 
        du_lieu_hien_thi = []
        for _, dong in du_lieu_loc.iterrows():
            danh_sach_tra_loi = str(dong['Câu trả lời']).split('\n')
            danh_sach_dung = str(dong['Kết quả']).split('\n')
            
            cac_tra_loi_dinh_dang = []
            for i, tra_loi in enumerate(danh_sach_tra_loi):
                if i < len(danh_sach_dung) and danh_sach_dung[i].strip().lower() == "đúng":
                    cac_tra_loi_dinh_dang.append(f"✅ {tra_loi.strip()}")
                else:
                    cac_tra_loi_dinh_dang.append(f"❌ {tra_loi.strip()}")
            
            du_lieu_hien_thi.append({
                'Tên bộ câu hỏi': dong[ten_cot_ma_de],
                'STT câu hỏi': dong['STT câu hỏi'],
                'Loại câu hỏi': dong.get('Loại câu hỏi', ''),
                'Câu hỏi': dong['Câu hỏi'],
                'Các câu trả lời': '\n'.join(cac_tra_loi_dinh_dang),
            })
        bang_hien_thi = pd.DataFrame(du_lieu_hien_thi) 
        st.dataframe(bang_hien_thi, 
                     use_container_width=True, 
                     height=450,
                     hide_index=True
                    )

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
        <p style="color:green">THỐNG KÊ KẾT QUẢ TRẮC NGHIỆM</p>
        </div>
    </div>
    <div class="header-underline"></div>
""", unsafe_allow_html=True)

html_code = f'<p class="demuc"><i>Nhân viên: {st.session_state.username}</i></p>'
st.html(html_code)

# Load master data
sheeti1 = st.secrets["sheet_name"]["input_1"]
sheeti8 = st.secrets["sheet_name"]["input_8"]
sheeto11 = st.secrets["sheet_name"]["output_11"]

du_lieu_input1 = load_data_full(sheeti1)
du_lieu_input8 = load_sheet_specific(sheeti8, "Sheet 1")
du_lieu_output_full = load_data_full(sheeto11)

danh_sach_khoa = du_lieu_input1["Khoa"].unique().tolist()
danh_sach_nhan_vien = du_lieu_input1["Nhân viên"].unique().tolist()
danh_sach_loai_bch = du_lieu_input8["Loại bộ câu hỏi"].unique().tolist()

now_vn = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
md = date(2026, 1, 1)

tab1, tab2 = st.tabs(["Thống kê kết quả", "Tra cứu bộ câu hỏi"])

with tab1:
    with st.form("filter_form"):
        cot1, cot2 = st.columns(2)
        with cot1:
            ngay_bat_dau = st.date_input(
                label="Ngày bắt đầu",
                value=now_vn.date(),
                min_value=md,
                max_value=now_vn.date(),
                format="DD/MM/YYYY",
            )
        with cot2:
            ngay_ket_thuc = st.date_input(
                label="Ngày kết thúc",
                value=now_vn.date(),
                min_value=md,
                max_value=now_vn.date(),
                format="DD/MM/YYYY",
            )
        
        khoa_duoc_chon = st.multiselect(
            label="Khoa",
            options=sorted(danh_sach_khoa),
            default=None,
            key="khoa_select"
        )
        
        # Lọc nhân viên theo khoa đã chọn
        if khoa_duoc_chon:
            nhan_vien_loc = du_lieu_input1[du_lieu_input1["Khoa"].isin(khoa_duoc_chon)]["Nhân viên"].unique().tolist()
        else:
            nhan_vien_loc = danh_sach_nhan_vien
        
        nhan_vien_duoc_chon = st.multiselect(
            label="Nhân viên thực hiện",
            options=sorted(nhan_vien_loc),
            default=None,
            key="nhan_vien_select"
        )
        
        chon_loai_bch = st.multiselect(
            label="Loại bộ câu hỏi",
            options=danh_sach_loai_bch,
            default=None,
            key="loai_bch_select"
        )

        nut_loc = st.form_submit_button("OK", type="primary")

    if nut_loc:
        if ngay_ket_thuc < ngay_bat_dau:
            st.error("❌ Lỗi: Ngày kết thúc đến trước ngày bắt đầu. Vui lòng chọn lại!")
        else:
            bo_loc_khoa = khoa_duoc_chon if khoa_duoc_chon and len(khoa_duoc_chon) > 0 else danh_sach_khoa
            bo_loc_nhan_vien = nhan_vien_duoc_chon if nhan_vien_duoc_chon and len(nhan_vien_duoc_chon) > 0 else None
            bo_loc_loai_bch = chon_loai_bch if chon_loai_bch and len(chon_loai_bch) > 0 else None
            
            du_lieu_output = load_data_filtered(sheeto11, ngay_bat_dau, ngay_ket_thuc, bo_loc_khoa, bo_loc_nhan_vien, bo_loc_loai_bch)
            
            if du_lieu_output.empty:
                st.warning("⚠️ Không tìm thấy dữ liệu phù hợp với bộ lọc đã chọn.")
            else:
                st.markdown("---")
                with st.expander("**:blue[Thống kê chung]**", expanded=True):
                    bang_thong_ke_chung = thong_ke_chung(du_lieu_output)
                    bang_thong_ke_styled = bang_thong_ke_chung.style.format({
                        'Điểm quy đổi': '{:.2f}'
                    })
                    st.dataframe(bang_thong_ke_styled, use_container_width=True, hide_index=True)
                
                st.markdown("---")
                with st.expander("**:blue[Thống kê chi tiết]**", expanded=True):
                    st.markdown("""
                        <p style="color:#f21f3f;font-size:15px;text-align:left"><i>
                            Chú thích Cột "Kết quả":<br>
                                <span style="margin-left:20px;">Đối với loại câu hỏi Trắc nghiệm: Đánh dấu "✗" hoặc "✓"; </span><br>
                                <span style="margin-left:20px;">Đối với loại câu hỏi Đúng/Sai: Tỉ lệ số câu trả lời đúng/số câu trả lời.</span>
                        </i>
                        </p>
                    """, unsafe_allow_html=True)
                    bang_thong_ke_chi_tiet = thong_ke_chi_tiet(du_lieu_output, du_lieu_input8)
                    
                    if not bang_thong_ke_chi_tiet.empty:
                        bang_co_mau = bang_thong_ke_chi_tiet.style.apply(to_mau_ket_qua_sai, axis=1)
                        st.dataframe(bang_co_mau, use_container_width=True, height=400, hide_index=True)
                    else:
                        st.info("Không có dữ liệu chi tiết.")

with tab2:
    bang_tra_cuu(du_lieu_input8)