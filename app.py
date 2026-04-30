import streamlit as st
from node_engine import NodeEngine
from vault_system import VaultManager

st.set_page_config(page_title="🎬 Node-Based Pipeline", page_icon="🧩", layout="wide")

# 1. ინიციალიზაცია
if "vault" not in st.session_state: 
    st.session_state.vault = VaultManager()
if "engine" not in st.session_state:
    try:
        st.session_state.engine = NodeEngine("workflow_config.json", None, st.session_state.vault)
    except Exception as e:
        st.error(f"❌ ნაკადის ჩატვირთვა ვერ მოხერხდა: {e}")
        st.session_state.engine = None

# 2. Sidebar
with st.sidebar:
    st.header("🎛️ მართვა")
    if st.button("▶️ გაუშვი მთლიანი ნაკადი"):
        st.session_state.run_pipeline = True
        st.rerun()
    if st.button("🧹 ლოგების გასუფთავება"):
        if "pipeline_logs" in st.session_state:
            st.session_state.pipeline_logs = []
        st.rerun()

# 3. მთავარი ხედი
st.title("🧩 AI Cinematic Pipeline — ვიზუალური ნოდური სისტემა")

engine = st.session_state.get("engine")
if engine:
    mermaid_code = engine.get_mermaid_diagram()
    st.markdown(f"""
    <div style="text-align: center; background: #f0f2f6; padding: 20px; border-radius: 10px; overflow-x: auto;">
        <pre class="mermaid">{mermaid_code}</pre>
    </div>""", unsafe_allow_html=True)
else:
    st.warning("⚠️ ნაკადის ძრავა ვერ ჩაიტვირთა.")

# 4. ლოგების კონტეინერი
st.divider()
st.subheader("📊 რეალურ დროის ლოგები")
log_container = st.empty()

# 5. გადავადებული შესრულება + მუდმივი ლოგები
if st.session_state.get("run_pipeline"):
    # ლოგების საცავი სესიაში (რომ არ წაიშალოს rerun-ის დროს)
    if "pipeline_logs" not in st.session_state:
        st.session_state.pipeline_logs = []
    
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

    if engine:
        # ძველი ლოგების გასუფთავება ახალი გაშვებისთვის
        st.session_state.pipeline_logs = []
        
        engine.logger = StreamlitLogger(log_container)
        for node in engine.nodes.values():
            node.logger = engine.logger
        
        with st.spinner("⏳ ნაკადი მუშაობს... გთხოვთ მოიცადოთ"):
            success = engine.execute()
        
        st.toast("🎉 წარმატება!" if success else "❌ ვერ დასრულდა", icon="✅" if success else "🚫")
        
        # დროშის გათიშვა, მაგრამ RERUN-ს ნუ ვაკეთებთ, რომ ლოგები დარჩეს ეკრანზე
        st.session_state.run_pipeline = False

st.caption("💡 ლოგები ახლა ინახება სესიაში და არ ქრება გაშვების შემდეგ.")
