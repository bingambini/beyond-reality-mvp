import streamlit as st
import os
from node_engine import NodeEngine
from vault_system import VaultManager

# ==================== 1. კონფიგურაცია & სესიის ინიციალიზაცია ====================
st.set_page_config(page_title="🎬 Node-Based Pipeline", page_icon="🧩", layout="wide")

if "vault" not in st.session_state:
    st.session_state.vault = VaultManager()

if "engine" not in st.session_state:
    try:
        st.session_state.engine = NodeEngine("workflow_config.json", None, st.session_state.vault)
    except Exception as e:
        st.error(f"❌ ნაკადის ჩატვირთვა ვერ მოხერხდა: {e}")
        st.session_state.engine = None

if "run_pipeline" not in st.session_state:
    st.session_state.run_pipeline = False
if "pipeline_logs" not in st.session_state:
    st.session_state.pipeline_logs = []

# ==================== 2. გვერდითა პანელი (Sidebar) ====================
with st.sidebar:
    st.header("🎛️ მართვა")
    
    # დავამატეთ key="btn_run" რათა თავიდან ავიცილოთ Duplicate ID
    if st.button("▶️ გაუშვი მთლიანი ნაკადი", key="btn_run_pipeline"):
        st.session_state.run_pipeline = True
        st.session_state.pipeline_logs = [] # ვასუფთავებთ ძველ ლოგებს
        st.rerun()
        
    if st.button("🧹 ლოგების გასუფთავება", key="btn_clear_logs"):
        st.session_state.pipeline_logs = []
        st.rerun()

# ==================== 3. მთავარი ინტერფეისი ====================
st.title("🧩 AI Cinematic Pipeline — ვიზუალური ნოდური სისტემა")

engine = st.session_state.get("engine")
if engine:
    mermaid_code = engine.get_mermaid_diagram()
    st.markdown(f"""
    <div style="text-align: center; background: #f0f2f6; padding: 20px; border-radius: 10px; overflow-x: auto;">
        <pre class="mermaid">{mermaid_code}</pre>
    </div>""", unsafe_allow_html=True)
else:
    st.warning("⚠️ ნაკადის ძრავა ვერ ჩაიტვირთა. გადაამოწმე workflow_config.json")

# ==================== 4. ლოგების კონტეინერი ====================
st.divider()
st.subheader("📊 რეალურ დროის ლოგები")
log_container = st.empty()

class StreamlitLogger:
    def __init__(self, container):
        self.container = container
    def add(self, agent, msg, level="info", indent=0):
        icons = {"info":"🔹","success":"✅","warning":"⚠️","error":"❌","start":"🚀","end":"🏁"}
        prefix = "  " * indent
        entry = f"{prefix}{icons.get(level,'•')} {agent}: {msg}"
        st.session_state.pipeline_logs.append(entry)
        with self.container:
            st.code("\n".join(st.session_state.pipeline_logs[-60:]), language="text")

# ==================== 5. პაიპლაინის შესრულება ====================
if st.session_state.run_pipeline and engine:
    engine.logger = StreamlitLogger(log_container)
    for node in engine.nodes.values():
        node.logger = engine.logger

    with st.spinner("⏳ ნაკადი მუშაობს... გთხოვთ მოიცადოთ"):
        success = engine.execute()

    st.toast("🎉 წარმატება!" if success else "❌ ვერ დასრულდა", icon="✅" if success else "🚫")
    st.session_state.run_pipeline = False 

# ==================== 6. 📂 OUTPUT ფაილების ბრაუზერი, წაშლა & ჩამოტვირთვა ====================
st.divider()
with st.expander("📂 დაგენერირებული ფაილების ნახვა & მართვა", expanded=True):
    output_dir = "./output"
    if os.path.exists(output_dir):
        files = sorted(os.listdir(output_dir), key=lambda f: os.path.getmtime(os.path.join(output_dir, f)), reverse=True)
        
        if not files:
            st.info("📄 ფაილები ჯერ არ დაგენერირებულა.")
        else:
            st.caption(f"📁 ნაპოვნია {len(files)} ფაილი.")
            cols = st.columns(3)
            
            for i, f in enumerate(files):
                full_path = os.path.join(output_dir, f)
                size_kb = os.path.getsize(full_path) / 1024
                col_idx = i % 3
                
                with cols[col_idx]:
                    st.markdown(f"**{f}**")
                    st.caption(f"📦 {size_kb:.1f} KB")
                    
                    # 🗑️ წაშლის ღილაკი (დამატებულია key პარამეტრი)
                    if st.button("🗑️ წაშლა", key=f"btn_del_{f}", type="secondary", use_container_width=True):
                        try:
                            os.remove(full_path)
                            st.toast(f"✅ {f} წაიშალა", icon="🗑️")
                            st.rerun() # სიის განახლება
                        except Exception as e:
                            st.error(f"❌ წაშლა ვერ მოხერხდა: {e}")

                    # პრევიუ & ჩამოტვირთვა (დამატებულია key პარამეტრები)
                    try:
                        if f.endswith(".mp4"):
                            st.video(full_path)
                            with open(full_path, "rb") as file:
                                st.download_button(label="⬇️ MP4", data=file, file_name=f, mime="video/mp4", key=f"dl_{f}", use_container_width=True)
                        elif f.endswith(".png"):
                            st.image(full_path)
                            with open(full_path, "rb") as file:
                                st.download_button(label="⬇️ PNG", data=file, file_name=f, mime="image/png", key=f"dl_{f}", use_container_width=True)
                        elif f.endswith(".mp3"):
                            st.audio(full_path)
                            with open(full_path, "rb") as file:
                                st.download_button(label="⬇️ MP3", data=file, file_name=f, mime="audio/mpeg", key=f"dl_{f}", use_container_width=True)
                    except Exception as e:
                        st.error(f"❌ ჩამოტვირთვა ვერ მოხერხდა: {e}")
    else:
        st.warning("📁 output/ საქაღალდე ჯერ არ არსებობს.")

st.caption("💡 წაშლა არის სამუდამო. ჩამოტვირთე მნიშვნელოვანი ფაილები.")
