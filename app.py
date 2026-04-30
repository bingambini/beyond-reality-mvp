import streamlit as st
import json
from node_engine import SimpleNodeEngine  # ✅ სწორი სახელი
from vault_system import VaultManager

st.set_page_config(page_title="🎬 Node-Based Pipeline", page_icon="🧩", layout="wide")

# ინიციალიზაცია
if "vault" not in st.session_state:
    st.session_state.vault = VaultManager()
if "engine" not in st.session_state:
    try:
        st.session_state.engine = SimpleNodeEngine("workflow_config.json", None, st.session_state.vault)
    except Exception as e:
        st.error(f"❌ ნაკადის ჩატვირთვა ვერ მოხერხდა: {e}")

# Sidebar
with st.sidebar:
    st.header("🔐 API სეიფი")
    # ... (შეინარჩუნე შენი სეიფის UI კოდი აქ) ...
    
    st.divider()
    st.header("⚙️ ნაკადის მართვა")
    if st.button("▶️ გაუშვი მთლიანი ნაკადი"):
        if st.session_state.engine:
            class StreamlitLogger:
                def __init__(self, container):
                    self.container = container
                    self.entries = []
                def add(self, agent, msg, level="info", indent=0):
                    icons = {"info":"🔹","success":"✅","warning":"⚠️","error":"❌","start":"🚀","end":"🏁"}
                    icon = icons.get(level, "•")
                    prefix = "  " * indent
                    self.entries.append(f"{prefix}{icon} {agent}: {msg}")
                    with self.container:
                        st.code("\n".join(self.entries[-30:]), language="text")
            
            st.session_state.engine.logger = StreamlitLogger(log_container)
            success = st.session_state.engine.execute()
            if success:
                st.success("✅ ნაკადი წარმატებით დასრულდა!")
            else:
                st.error("❌ ნაკადი ვერ დასრულდა. შეამოწმე ლოგები.")

# მთავარი ხედი
st.title("🧩 AI Cinematic Pipeline — ვიზუალური ნოდური სისტემა")

# Mermaid.js დიაგრამა
if st.session_state.engine:
    mermaid_code = st.session_state.engine.get_mermaid_diagram()
    st.markdown(f"""
    <div style="text-align: center; background: #f0f2f6; padding: 20px; border-radius: 10px; overflow-x: auto;">
        <pre class="mermaid">
        {mermaid_code}
        </pre>
    </div>
    """, unsafe_allow_html=True)
else:
    st.info("👉 ნაკადი ვერ ჩაიტვირთა. შეამოწმე workflow_config.json")

# ლოგების კონტეინერი
st.divider()
st.subheader("📊 რეალურ დროის ლოგები")
log_container = st.empty()

st.caption("""
💡 **როგორ მუშაობს:**
1. ზემოთ ხედავ ვიზუალურ დიაგრამას (Mermaid.js)
2. "გაუშვი მთლიანი ნაკადი" ასრულებს ყველა ნოდს თანმიმდევრულად
3. ლოგებში ჩანს თითოეული ნოდის სტატუსი
""")
