import streamlit as st
from node_engine import NodeEngine
from vault_system import VaultManager

st.set_page_config(page_title="🎬 Node-Based Pipeline", page_icon="🧩", layout="wide")

if "vault" not in st.session_state: st.session_state.vault = VaultManager()
if "engine" not in st.session_state:
    try:
        st.session_state.engine = NodeEngine("workflow_config.json", None, st.session_state.vault)
    except Exception as e: st.error(f"❌ ნაკადის ჩატვირთვა ვერ მოხერხდა: {e}")

with st.sidebar:
    st.header("🎛️ მართვა")
    if st.button("▶️ გაუშვი მთლიანი ნაკადი"):
        st.session_state.run_pipeline = True
        st.rerun()

st.title("🧩 AI Cinematic Pipeline — ვიზუალური ნოდური სისტემა")

if st.session_state.engine:
    mermaid_code = st.session_state.engine.get_mermaid_diagram()
    st.markdown(f"""
    <div style="text-align: center; background: #f0f2f6; padding: 20px; border-radius: 10px; overflow-x: auto;">
        <pre class="mermaid">{mermaid_code}</pre>
    </div>""", unsafe_allow_html=True)

st.divider()
st.subheader("📊 რეალურ დროის ლოგები")
log_container = st.empty()

if st.session_state.get("run_pipeline"):
    class StreamlitLogger:
        def __init__(self, container): self.container, self.entries = container, []
        def add(self, agent, msg, level="info", indent=0):
            icons = {"info":"🔹","success":"✅","warning":"⚠️","error":"❌","start":"🚀","end":"🏁"}
            prefix = "  " * indent
            self.entries.append(f"{prefix}{icons.get(level,'•')} {agent}: {msg}")
            with self.container: st.code("\n".join(self.entries[-30:]), language="text")

    if st.session_state.engine:
        st.session_state.engine.logger = StreamlitLogger(log_container)
        with st.spinner("⏳ ნაკადი მუშაობს..."):
            success = st.session_state.engine.execute()
        st.toast("🎉 წარმატება!" if success else "❌ ვერ დასრულდა", icon="✅" if success else "🚫")
        st.session_state.run_pipeline = False
        st.rerun()

st.caption("💡 ჯერ ჩანს მხოლოდ არქიტექტურა. მომდევნო ნაბიჯში ჩავწერთ `agents/` და `nodes/` ფაილებში კოდს.")
