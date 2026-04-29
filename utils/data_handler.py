import pandas as pd
import numpy as np

def to_numeric_safe(value):
    """
    Chuyển đổi một giá trị sang kiểu số một cách an toàn.
    Xử lý: khoảng trắng, dấu phẩy, dấu trừ Unicode, chuỗi rỗng.
    
    Parameters:
        value: Giá trị cần chuyển đổi
    
    Returns:
        Giá trị số hoặc NaN nếu không thể chuyển đổi
    """
    if pd.isna(value):
        return np.nan
    
    # Chuyển sang string và xử lý
    str_val = str(value).strip()
    
    if not str_val or str_val.lower() in ['nan', 'none', '']:
        return np.nan
    
    # Thay dấu phẩy bằng dấu chấm
    str_val = str_val.replace(',', '.')
    # Xử lý dấu trừ Unicode
    str_val = str_val.replace('−', '-')
    
    try:
        return float(str_val)
    except (ValueError, TypeError):
        return np.nan

def convert_numeric_columns(data, columns, strip_whitespace=True):
    """
    Chuyển đổi nhiều cột sang kiểu số một cách an toàn.
    
    Parameters:
        data: DataFrame
        columns: Danh sách các chỉ số cột hoặc tên cột cần chuyển đổi
        strip_whitespace: Có loại bỏ khoảng trắng không
    
    Returns:
        DataFrame đã được chuyển đổi
    """
    data = data.copy().reset_index(drop=True)
    
    for col in columns:
        try:
            if isinstance(col, int):
                # Lấy tên cột từ chỉ số
                col_name = data.columns[col]
            else:
                col_name = col
            
            # Xử lý dữ liệu theo tên cột (tránh vấn đề iloc)
            col_data = data[col_name].astype(str)
            
            if strip_whitespace:
                col_data = col_data.str.strip()
            
            col_data = col_data.str.replace(',', '.', regex=False)
            col_data = col_data.str.replace('−', '-', regex=False)
            col_data = col_data.replace(['', 'nan', 'None', 'NaN'], np.nan)
            col_data = pd.to_numeric(col_data, errors='coerce')
            
            # Gán lại dữ liệu
            data[col_name] = col_data
        except Exception as e:
            print(f"⚠️ Lỗi xử lý cột {col}: {str(e)}")
            continue
    
    return data

def convert_numeric_by_range(data, start_col, end_col=None):
    """
    Chuyển đổi một phạm vi cột từ vị trí bắt đầu đến cột cuối cùng.
    
    Parameters:
        data: DataFrame
        start_col: Chỉ số cột bắt đầu
        end_col: Chỉ số cột kết thúc (nếu None, chuyển đến cột cuối cùng)
    
    Returns:
        DataFrame đã được chuyển đổi
    """
    if end_col is None:
        end_col = len(data.columns)
    
    return convert_numeric_columns(data, range(start_col, end_col))
