import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import google.generativeai as genai
import base64
from io import BytesIO

# --- CẤU HÌNH AI ---
genai.configure(api_key="AIzaSyBvuuNnTfBHZbkfiNF5eC56ZQ1VtTpjRlM")

def generate_analysis(prompt_text):
    try:
        with st.spinner("🔍 Đang phân tích..."):
            model = genai.GenerativeModel("gemini-2.5-flash")
            default_instruction = (
                "Hãy phân tích dữ liệu điểm thi này. Đưa ra nhận xét về sự chênh lệch giữa các đơn vị, "
                "xác định các đơn vị có kết quả tốt nhất và các đơn vị cần cải thiện. "
                "Đề xuất hướng khắc phục cụ thể.\n\n"
            )
            response = model.generate_content(default_instruction + str(prompt_text))
            return response.text
    except Exception as e:
        return f"❌ Lỗi AI: {e}"

# --- HÀM HỖ TRỢ CUỘN NGANG ---
def st_plt_scrollable(fig, width_px):
    """Chuyển biểu đồ thành HTML có thanh cuộn ngang"""
    tmpfile = BytesIO()
    fig.savefig(tmpfile, format='png', bbox_inches='tight')
    encoded = base64.b64encode(tmpfile.getvalue()).decode('utf-8')
    html = f"""
    <div style="overflow-x: auto; white-space: nowrap; border: 1px solid #ddd; padding: 10px; border-radius: 5px;">
        <img src="data:image/png;base64,{encoded}" style="width: {width_px}px; max-width: none;">
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# --- GIAO DIỆN & SETUP ---
st.set_page_config(page_title="Phân tích điểm thi - Tuyên Quang", layout="wide")

st.markdown("## SỞ GIÁO DỤC VÀ ĐÀO TẠO TUYÊN QUANG")
st.title("📘 PHÂN TÍCH KẾT QUẢ KHÁO SÁT GIỮA NĂM HỌC 2025 - 2026")

# Sidebar
st.sidebar.header("🔎 Cấu hình hiển thị")
chart_zoom = st.sidebar.slider("🔍 Độ dài thanh cuộn (Pixel)", 1000, 5000, 1500, step=100)
st.sidebar.info("💡 Kéo thanh trượt trên để tăng độ dài vùng chứa biểu đồ nếu có quá nhiều trường.")

# Chế độ quản trị
admin_mode = st.sidebar.checkbox("Chế độ quản trị")
if admin_mode:
    password = st.sidebar.text_input("Mật khẩu", type="password")
    if password == "123":
        uploaded_file = st.file_uploader("Tải dữ liệu", type=["xlsx", "csv"])
        if uploaded_file:
            with open("du_lieu_mau.xlsx", "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success("✅ Cập nhật thành công!")

# --- LOAD DỮ LIỆU ---
try:
    try:
        df = pd.read_csv("du_lieu_mau.xlsx - Sheet1.csv")
    except:
        df = pd.read_excel("du_lieu_mau.xlsx")
    df.columns = df.columns.str.strip()
    df['Điểm thi'] = pd.to_numeric(df['Điểm thi'], errors='coerce')
except:
    st.error("❌ Không tìm thấy dữ liệu mẫu.")
    st.stop()

# Bộ lọc trường
school_options = ["Toàn tỉnh"] + sorted(df['Đơn vị'].dropna().unique().tolist())
selected_school = st.sidebar.selectbox("Chọn phạm vi phân tích:", school_options)
df_filtered = df if selected_school == "Toàn tỉnh" else df[df['Đơn vị'] == selected_school]

# =========================================================================
# PHẦN 1: CẤP THPT
# =========================================================================
st.subheader("🏫 Phần 1: Biểu đồ điểm trung bình cấp THPT")

avg_by_school = df_filtered.groupby("Đơn vị")['Điểm thi'].mean()
avg_all = df_filtered['Điểm thi'].mean()
plot_data = avg_by_school.copy()
plot_data["Trung bình toàn bộ"] = avg_all
plot_data = plot_data.sort_values(ascending=False)

labels = []
rank = 1
for name in plot_data.index:
    if name == "Trung bình toàn bộ": labels.append("Trung bình")
    else:
        labels.append(f"{rank}. {name}")
        rank += 1

colors = ['orange' if n == "Trung bình toàn bộ" else 'skyblue' for n in plot_data.index]

fig1, ax1 = plt.subplots(figsize=(20, 7)) # Cố định size trong bộ nhớ
bars = ax1.bar(labels, plot_data.values, color=colors)
for bar in bars:
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2, height + 0.1, f"{height:.2f}", ha='center', rotation=90)

ax1.set_ylim(0, 10)
plt.xticks(rotation=90)
plt.tight_layout()

# HIỂN THỊ CÓ THANH CUỘN
st_plt_scrollable(fig1, chart_zoom)

if st.checkbox("📌 Nhận xét AI cho Phần 1", key="ai1"):
    st.markdown(generate_analysis(f"Dữ liệu THPT: {plot_data.to_dict()}"))

# =========================================================================
# PHẦN 3: CẤP THCS
# =========================================================================
st.divider()
st.subheader("🏫 Phần 3: Biểu đồ điểm trung bình cấp THCS")
try:
    df_thcs = pd.read_excel("du_lieu_mau_thcs.xlsx")
    df_thcs.columns = df_thcs.columns.str.strip()
    df_thcs['Điểm thi'] = pd.to_numeric(df_thcs['Điểm thi'], errors='coerce')
    avg_thcs = df_thcs.groupby("Đơn vị")['Điểm thi'].mean()
    avg_all_thcs = df_thcs['Điểm thi'].mean()
    
    plot_thcs = avg_thcs.copy()
    plot_thcs["Trung bình"] = avg_all_thcs
    plot_thcs = plot_thcs.sort_values(ascending=False)
    
    labels_thcs = [f"{i+1}. {n}" if n != "Trung bình" else n for i, n in enumerate(plot_thcs.index)]
    colors_thcs = ['orange' if n == "Trung bình" else '#2ECC71' for n in plot_thcs.index]

    fig3, ax3 = plt.subplots(figsize=(20, 7))
    bars3 = ax3.bar(labels_thcs, plot_thcs.values, color=colors_thcs)
    ax3.set_ylim(0, 10)
    plt.xticks(rotation=90)
    plt.tight_layout()

    st_plt_scrollable(fig3, chart_zoom)
except:
    st.warning("⚠️ Chưa có dữ liệu cấp THCS.")

# =========================================================================
# PHẦN 4: CẤP TIỂU HỌC
# =========================================================================
st.divider()
st.subheader("🏫 Phần 4: Biểu đồ điểm trung bình cấp Tiểu học")
try:
    df_th = pd.read_excel("du_lieu_mau_th.xlsx")
    df_th.columns = df_th.columns.str.strip()
    df_th['Điểm thi'] = pd.to_numeric(df_th['Điểm thi'], errors='coerce')
    avg_th = df_th.groupby("Đơn vị")['Điểm thi'].mean()
    avg_all_th = df_th['Điểm thi'].mean()
    
    plot_th = avg_th.copy()
    plot_th["Trung bình"] = avg_all_th
    plot_th = plot_th.sort_values(ascending=False)
    
    labels_th = [f"{i+1}. {n}" if n != "Trung bình" else n for i, n in enumerate(plot_th.index)]
    colors_th = ['orange' if n == "Trung bình" else 'violet' for n in plot_th.index]

    fig4, ax4 = plt.subplots(figsize=(25, 7))
    ax4.bar(labels_th, plot_th.values, color=colors_th)
    ax4.set_ylim(0, 10)
    plt.xticks(rotation=90)
    plt.tight_layout()

    st_plt_scrollable(fig4, chart_zoom)
except:
    st.warning("⚠️ Chưa có dữ liệu cấp Tiểu học.")

# =========================================================================
# PHẦN 2: CHI TIẾT THEO LỚP
# =========================================================================
st.divider()
st.subheader("📊 Phần 2: Chi tiết theo Lớp (Cấp THPT)")
list_schools = sorted(df['Đơn vị'].dropna().unique().tolist())
selected_schools_p2 = st.multiselect("Chọn trường:", options=list_schools)

if selected_schools_p2:
    df_p2 = df[df['Đơn vị'].isin(selected_schools_p2)]
    avg_by_class = df_p2.groupby(['Đơn vị', 'Lớp'])['Điểm thi'].mean().reset_index()
    for school in selected_schools_p2:
        school_data = avg_by_class[avg_by_class['Đơn vị'] == school].sort_values(by='Điểm thi', ascending=False)
        st.write(f"#### 🏫 Trường: {school}")
        fig2, ax2 = plt.subplots(figsize=(10, 5))
        ax2.bar(school_data['Lớp'], school_data['Điểm thi'], color='mediumseagreen')
        ax2.set_ylim(0, 10)
        st.pyplot(fig2)