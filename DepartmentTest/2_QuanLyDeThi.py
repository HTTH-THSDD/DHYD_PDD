import streamlit as st
import pandas as pd
import gspread
from datetime import datetime
from zoneinfo import ZoneInfo
import pathlib
import base64
from google.oauth2.service_account import Credentials

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

@st.cache_data(ttl=3600)
def get_img_as_base64(file):
    with open(file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

def load_css(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except:
        pass

def load_sheet_by_name(sheet_name, worksheet_name):
    try:
        credentials = load_credentials()
        gc = gspread.authorize(credentials)
        spreadsheet = gc.open(sheet_name)
        
        # Thử tìm worksheet theo tên
        try:
            sheet = spreadsheet.worksheet(worksheet_name)
        except gspread.exceptions.WorksheetNotFound:
            st.warning(f"⚠️ Không tìm thấy worksheet '{worksheet_name}'")
            return pd.DataFrame()
        
        data = sheet.get_all_values()
        if len(data) > 1:  # Có ít nhất header + 1 dòng dữ liệu
            header = data[0]
            values = data[1:]
            return pd.DataFrame(values, columns=header)
        elif len(data) == 1:
            st.info(f"ℹ️ Worksheet '{worksheet_name}' chỉ có header, không có dữ liệu")
            return pd.DataFrame()
        else:
            st.warning(f"⚠️ Worksheet '{worksheet_name}' rỗng")
            return pd.DataFrame()
            
    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"❌ Không tìm thấy Google Sheet: '{sheet_name}'")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Lỗi load dữ liệu: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return pd.DataFrame()

def update_cell_value(sheet_name, worksheet_name, row, col, value):
    credentials = load_credentials()
    gc = gspread.authorize(credentials)
    spreadsheet = gc.open(sheet_name)
    sheet = spreadsheet.worksheet(worksheet_name)
    sheet.update_cell(row, col, value)

def append_rows_to_sheet(sheet_name, worksheet_name, rows):
    credentials = load_credentials()
    gc = gspread.authorize(credentials)
    spreadsheet = gc.open(sheet_name)
    sheet = spreadsheet.worksheet(worksheet_name)
    for row in rows:
        sheet.append_row(row)

def hien_thi_header():
    try:
        img = get_img_as_base64("pages/img/logo.png")
        css_path = pathlib.Path("asset/style.css")
        load_css(css_path)
        st.markdown(f"""
            <div class="fixed-header">
                <div class="header-content">
                    <img src="data:image/png;base64,{img}" alt="logo">
                    <div class="header-text">
                        <h1>BỆNH VIỆN ĐẠI HỌC Y DƯỢC THÀNH PHỐ HỒ CHÍ MINH<span style="vertical-align: super; font-size: 0.6em;">&#174;</span><br><span style="color:#c15088">Phòng Điều dưỡng</span></h1>
                    </div>
                </div>
                <div class="header-subtext">
                <p>HỆ THỐNG QUẢN LÝ ĐỀ THI</p>
                </div>
            </div>
            <div class="header-underline"></div>
         """, unsafe_allow_html=True)
    except:
        st.title("HỆ THỐNG QUẢN LÝ ĐỀ THI")
    
    if 'username' in st.session_state:
        html_code = f'<p class="demuc"><i>Quản trị viên: {st.session_state.username}</i></p>'
        st.html(html_code)

# Initialize session state
if 'questions' not in st.session_state:
    st.session_state.questions = []
if 'question_counter' not in st.session_state:
    st.session_state.question_counter = 1

# Main Section
hien_thi_header()

# Tabs
tab1, tab2 = st.tabs(["📋 Kiểm soát đề", "➕ Tạo bộ câu hỏi"])

# TAB 1: Kiểm soát đề
with tab1:
    st.markdown("<p style='color:#230ee3;font-size:25px;font-weight:bold;text-align:center'>Danh sách bộ câu hỏi</p>", unsafe_allow_html=True)

  
    
    sheeti8 = st.secrets["sheet_name"]["input_8"]
    
    # Load từ Sheet 1 (nơi lưu câu hỏi), hoặc Sheet 2 (nơi lưu config)
    # Nếu bạn muốn hiển thị danh sách mã đề, load từ Sheet 2
    df_config = load_sheet_by_name(sheeti8, "Sheet 2")
    
    # Nếu Sheet 2 rỗng, thử load từ Sheet 1 để lấy tên bộ đề duy nhất
    if len(df_config) == 0:
        df_sheet1 = load_sheet_by_name(sheeti8, "Sheet 1")
        if len(df_sheet1) > 0 and "Tên bộ câu hỏi" in df_sheet1.columns:
            # Lấy những tên bộ đề duy nhất từ Sheet 1
            unique_names = df_sheet1["Tên bộ câu hỏi"].unique()
            df_config = pd.DataFrame({
                "Tên bộ câu hỏi": unique_names,
                "Thời gian tối đa (phút)": [0] * len(unique_names),
                "Điểm số tối đa": [0] * len(unique_names),
                "Trạng thái": ["OFF"] * len(unique_names),
            })
    
    if len(df_config) > 0:
        #st.markdown("### Danh sách mã đề")
        
        # Thêm cột trạng thái nếu chưa có
        if "Trạng thái" not in df_config.columns:
            df_config["Trạng thái"] = "OFF"
        
        for idx, row in df_config.iterrows():
            ma_de = row["Tên bộ câu hỏi"]
            trang_thai_hien_tai = row.get("Trạng thái", "OFF")
            
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.markdown(f"**{ma_de}**")
            
            with col2:
                thoi_gian_text = row.get("Thời gian tối đa (phút)", "N/A")
                st.markdown(f"Thời gian: {thoi_gian_text} phút")
            
            with col3:
                is_on = st.toggle(
                    "Mở đề",
                    value=(trang_thai_hien_tai == "ON"),
                    key=f"toggle_{ma_de}_{idx}",
                )
                
                new_status = "ON" if is_on else "OFF"
                
                # Auto save khi thay đổi
                if new_status != trang_thai_hien_tai:
                    try:
                        credentials = load_credentials()
                        gc = gspread.authorize(credentials)
                        spreadsheet = gc.open(sheeti8)
                        sheet = spreadsheet.worksheet("Sheet 2")
                        
                        # Kiểm tra xem cột D có header chưa
                        header_row = sheet.row_values(1)
                        if len(header_row) < 4 or header_row[3] != "Trạng thái":
                            sheet.update_cell(1, 4, "Trạng thái")
                        
                        # Update trạng thái (row index + 2 vì có header)
                        sheet.update_cell(idx + 2, 4, new_status)
                        
                        st.success(f"✅ Đã {new_status} mã đề {ma_de}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Lỗi: {str(e)}")
            
            st.divider()
    else:
        st.info("ℹ️ Chưa có mã đề nào trong hệ thống")

# TAB 2: Tạo bộ câu hỏi
with tab2:
    st.header("Tạo bộ câu hỏi mới")
    
    # Thông tin cơ bản
    st.subheader("Thông tin bộ đề")
    col1, col2= st.columns(2)
    with col1:
        loai_bo_cau_hoi = st.text_input("Loại bộ câu hỏi *", key="loai_bo_cau_hoi")
    with col2:
        ten_bo_cau_hoi = st.text_input("Tên bộ câu hỏi *", key="ten_bo_cau_hoi")
    
    col3, col4 = st.columns(2)
    with col3:
        diem_toi_da = st.number_input("Điểm số tối đa *", min_value=1, key="diem_toi_da")
    with col4:
        thoi_gian = st.number_input("Thời gian tối đa (phút) *", min_value=1, key="thoi_gian")
    
    st.markdown("---")
    
    # Quản lý câu hỏi
    st.subheader("Danh sách câu hỏi")
    
    # Nút thêm câu hỏi
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Thêm câu hỏi Trắc nghiệm", use_container_width=True):
            # STT = số lượng câu hỏi hiện tại + 1
            new_stt = len(st.session_state.questions) + 1
            st.session_state.questions.append({
                'stt': new_stt,
                'type': 'Trắc nghiệm',
                'question': '',
                'answers': ['', '', '', ''],
                'results': ['Sai', 'Sai', 'Sai', 'Sai']
            })
            st.rerun()
    
    with col2:
        if st.button("➕ Thêm câu hỏi Đúng/Sai", use_container_width=True):
            # STT = số lượng câu hỏi hiện tại + 1
            new_stt = len(st.session_state.questions) + 1
            st.session_state.questions.append({
                'stt': new_stt,
                'type': 'Đúng/Sai',
                'question': '',
                'answers': [''],
                'results': ['Đúng']
            })
            st.rerun()
    
    # Hiển thị các câu hỏi
    for q_idx, question in enumerate(st.session_state.questions):
        with st.expander(f"Câu {question['stt']} - {question['type']}", expanded=True):
            col1, col2 = st.columns([5, 1])
            
            with col1:
                question['question'] = st.text_area(
                    f"Nội dung câu hỏi {question['stt']}",
                    value=question['question'],
                    key=f"q_content_{q_idx}",
                    height=100
                )
            
            with col2:
                if st.button("🗑️ Xóa", key=f"delete_{q_idx}", use_container_width=True):
                    st.session_state.questions.pop(q_idx)
                    # Re-index STT để luôn liên tiếp
                    for i, q in enumerate(st.session_state.questions):
                        q['stt'] = i + 1
                    st.rerun()
            
            st.markdown("**Câu trả lời:**")
            
            if question['type'] == 'Trắc nghiệm':
                # 4 câu trả lời cố định
                for ans_idx in range(4):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        question['answers'][ans_idx] = st.text_input(
                            f"Đáp án {ans_idx + 1}",
                            value=question['answers'][ans_idx],
                            key=f"q_{q_idx}_ans_{ans_idx}",
                            label_visibility="collapsed"
                        )
                    with col2:
                        question['results'][ans_idx] = st.selectbox(
                            "Kết quả",
                            ["Đúng", "Sai"],
                            index=0 if question['results'][ans_idx] == "Đúng" else 1,
                            key=f"q_{q_idx}_res_{ans_idx}",
                            label_visibility="collapsed"
                        )
            
            else:  # Đúng/Sai
                for ans_idx in range(len(question['answers'])):
                    col1, col2, col3 = st.columns([4, 1, 1])
                    with col1:
                        question['answers'][ans_idx] = st.text_input(
                            f"Câu {ans_idx + 1}",
                            value=question['answers'][ans_idx],
                            key=f"q_{q_idx}_ans_{ans_idx}",
                            label_visibility="collapsed"
                        )
                    with col2:
                        question['results'][ans_idx] = st.selectbox(
                            "Kết quả",
                            ["Đúng", "Sai"],
                            index=0 if question['results'][ans_idx] == "Đúng" else 1,
                            key=f"q_{q_idx}_res_{ans_idx}",
                            label_visibility="collapsed"
                        )
                    with col3:
                        if ans_idx == len(question['answers']) - 1:
                            if st.button("➕", key=f"add_ans_{q_idx}_{ans_idx}"):
                                question['answers'].append('')
                                question['results'].append('Đúng')
                                st.rerun()
                        else:
                            if st.button("➖", key=f"remove_ans_{q_idx}_{ans_idx}"):
                                question['answers'].pop(ans_idx)
                                question['results'].pop(ans_idx)
                                st.rerun()
    
    st.markdown("---")
    
    # Nút lưu và tạo mới
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Lưu bộ đề", type="primary", use_container_width=True):
            # Validate
            if not ten_bo_cau_hoi:
                st.error("❌ Vui lòng nhập tên bộ câu hỏi!")
            elif not loai_bo_cau_hoi:
                st.error("❌ Vui lòng nhập loại bộ câu hỏi!")
            elif len(st.session_state.questions) == 0:
                st.error("❌ Vui lòng thêm ít nhất 1 câu hỏi!")
            else:
                # Kiểm tra tất cả câu hỏi đã điền đầy đủ
                valid = True
                for q in st.session_state.questions:
                    if not q['question']:
                        st.error("❌ Vui lòng điền đầy đủ nội dung câu hỏi!")
                        valid = False
                        break
                    for ans in q['answers']:
                        if not ans:
                            st.error("❌ Vui lòng điền đầy đủ câu trả lời!")
                            valid = False
                            break
                    if not valid:
                        break
                
                if valid:
                    try:
                        # Lưu vào Sheet 2 (Quy định) - cấu trúc: Tên bộ câu hỏi, Thời gian, Điểm số tối đa, Trạng thái, Loại bộ câu hỏi
                        config_row = [ten_bo_cau_hoi, str(thoi_gian), str(diem_toi_da), "OFF", loai_bo_cau_hoi]
                        append_rows_to_sheet(sheeti8, "Sheet 2", [config_row])
                        
                        # Lưu vào Sheet 1 (Bộ câu hỏi) theo cấu trúc:
                        # Tên bộ câu hỏi | STT câu hỏi | Câu hỏi | Loại câu hỏi | Câu trả lời | Kết quả | Loại bộ câu hỏi
                        question_rows = []
                        
                        for q in st.session_state.questions:
                            # Format câu trả lời và kết quả - giữ nguyên với \n
                            answers_text = '\n'.join(q['answers'])
                            results_text = '\n'.join(q['results'])
                            
                            # Tạo 1 dòng duy nhất cho mỗi câu hỏi
                            row = [
                                ten_bo_cau_hoi,           # Cột A: Tên bộ câu hỏi
                                str(q['stt']),            # Cột B: STT câu hỏi
                                q['question'],            # Cột C: Câu hỏi
                                q['type'],                # Cột D: Loại câu hỏi (Trắc nghiệm / Đúng-Sai)
                                answers_text,             # Cột E: Câu trả lời (format: Đáp án 1\nĐáp án 2\n...)
                                results_text,             # Cột F: Kết quả (format: Đúng\nSai\nSai\n...)
                                loai_bo_cau_hoi           # Cột G: Loại bộ câu hỏi
                            ]
                            question_rows.append(row)
                        
                        append_rows_to_sheet(sheeti8, "Sheet 1", question_rows)
                        
                        st.success(f"✅ Đã lưu bộ đề '{ten_bo_cau_hoi}' thành công!")
                        st.info(f"ℹ️ Tổng số câu hỏi: {len(st.session_state.questions)}")
                        st.balloons()
                        
                        # Reset form sau 2 giây
                        import time
                        time.sleep(2)
                        st.session_state.questions = []
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Lỗi khi lưu: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())
    
    with col2:
        if st.button("🔄 Tạo bộ đề mới", use_container_width=True):
            st.session_state.questions = []
            st.rerun()