import streamlit as st
import json
from node_engine import NodeEngine
from vault_system import VaultManager

st.set_page_config(page_title="🎬 Node-Based Pipeline", page_icon="🧩", layout="wide")

# ინიციალიზაცია
if "vault" not in st.session_state:
    st.session_state.vault = VaultManager()
if "engine" not in st.session_state:
    st.session_state.engine = None

# Sidebar - სეიფი და კონფიგი
with st.sidebar:
    st.header("🔐 API სეიფი")
    # ... (იგივე სეიფის UI, რაც ადრე)
    
    st.divider()
    st.header("⚙️ ნაკადის მართვა")
    if st.button("🔄 გადატვირთე ნაკადი"):
        st.session_state.engine = NodeEngine("workflow_config.json", None)  # logger გადაეცე
        st.rerun()
    
    if st.button("▶️ გაუშვი მთლიანი ნაკადი"):
        if st.session_state.engine:
            # შექმენი დროებითი ლოგერი
            class SimpleLogger:
                def add(self, agent, msg, level="info", indent=0):
                    st.toast(f"[{agent}] {msg}", icon="✅" if level=="success" else "❌" if level=="error" else "🔹")
            st.session_state.engine.logger = SimpleLogger()
            success = st.session_state.engine.execute()
            if success:
                st.success("✅ ნაკადი წარმატებით დასრულდა!")
            else:
                st.error("❌ ნაკადი ვერ დასრულდა")

# მთავარი ხედი
st.title("🧩 AI Cinematic Pipeline — ვიზუალური ნოდური სისტემა")

# Mermaid.js დიაგრამა
if st.session_state.engine:
    mermaid_code = st.session_state.engine.get_mermaid_diagram()
    
    # Streamlit-ში Mermaid-ის ჩასმა
    st.markdown(f"""
    <div style="text-align: center; background: #f0f2f6; padding: 20px; border-radius: 10px;">
        <pre class="mermaid">
        {mermaid_code}
        </pre>
    </div>
    """, unsafe_allow_html=True)
    
    # ნოდების რედაქტირება (collapsible)
    st.subheader("⚙️ ნოდების კონფიგურაცია")
    for node_config in st.session_state.engine.workflow["nodes"]:
        with st.expander(f"{node_config['label']} ({node_config['id']})"):
            st.write(f"**აღწერა:** {node_config['description']}")
            st.json(node_config["config"])
            # აქ შეიძლება დაემატოს რედაქტირების ფორმები
else:
    st.info("👉 დააჭირე '🔄 გადატვირთე ნაკადი' Sidebar-ში, რომ დატვირთო ვიზუალური ნაკადი.")

# ლოგების კონტეინერი
st.divider()
st.subheader("📊 რეალურ დროის ლოგები")
log_container = st.empty()

# დროებითი ლოგერი (მომავალში შეიძლება იყოს ცალკე კლასი)
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

if st.session_state.engine:
    st.session_state.engine.logger = StreamlitLogger(log_container)

# ფეისერი
st.caption("""
💡 **როგორ მუშაობს:**
1. თითოეული ბლოკი არის დამოუკიდებელი აგენტი თავისი ლოგიკით
2. ხაზები აჩვენებს მონაცემთა ნაკადს (თემა → სცენარი → ხმა/ვიზუალი → ვიდეო)
3. შეგიძლია დააკონფიგურირო თითოეული ნოდი ცალ-ცალკე
4. "გაუშვი მთლიანი ნაკადი" ასრულებს ყველა ნოდს თანმიმდევრულად
""")
