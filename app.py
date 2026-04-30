import streamlit as st
import json
from node_engine import SimpleNodeEngine  # ✅ დარწმუნდი რომ აქ SimpleNodeEngine წერია
from vault_system import VaultManager

st.set_page_config(page_title="🎬 Node-Based Pipeline", page_icon="🧩", layout="wide")

# 1. სესიის ინიციალიზაცია
if "vault" not in st.session_state:
    st.session_state.vault = VaultManager()
if "engine" not in st.session_state:
    try:
        # ვქმნით ძრავას (ლოგერი ჯერ არის None)
        st.session_state.engine = SimpleNodeEngine("workflow_config.json", None, st.session_state.vault)
    except Exception as e:
        st.error(f"❌ ნაკადის ჩატვირთვა ვერ მოხერხდა: {e}")

# 2. გვერდითა პანელი (Sidebar)
with st.sidebar:
    st.header("🔐 API სეიფი")
    # >>> აქ ჩასვი შენი სეიფის UI კოდი (Text Inputs, Save Button) <<<
    # მაგალითად:
    # current_key = st.text_input("Gemini Key", value=st.session_state.vault.get_key("gemini_text", 0), type="password")
    # if st.button("💾 შენახვა"): st.session_state.vault.update_key("gemini_text", 0, current_key)
    
    st.divider()
    st.header("⚙️ ნაკადის მართვა")
    
    # ღილაკი მხოლოდ "დროშას" რთავს და აკეთებს Rerun-ს
    if st.button("▶️ გაუშვი მთლიანი ნაკადი"):
        st.session_state.run_pipeline = True
        st.rerun() # სკრიპტის ხელახლა გაშვება, რათა მიაღწიოს execution ბლოკს

# 3. მთავარი ინტერფეისი
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

# 4. ლოგების კონტეინერი (ახლა უსაფრთხოდ შეგვიძლია განვსაზღვროთ)
st.divider()
st.subheader("📊 რეალურ დროის ლოგები")
log_container = st.empty()

# 5. გადავადებული შესრულება (Deferred Execution)
# ეს ბლოკი მუშაობს მხოლოდ მაშინ, როცა ღილაკი დააჭირე
if st.session_state.get("run_pipeline"):
    
    # ლოგერის კლასი (განისაზღვრება აქ, რადგან log_container უკვე არსებობს)
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
        # ვუკავშირებთ ლოგერს კონტეინერს
        st.session_state.engine.logger = StreamlitLogger(log_container)
        
        # ვუშვებთ ნაკადს სპინერის თანხლებით
        with st.spinner("⏳ ნაკადი მუშაობს... გთხოვთ მოიცადოთ"):
            success = st.session_state.engine.execute()
        
        # შედეგის ჩვენება
        if success:
            st.toast("🎉 ნაკადი წარმატებით დასრულდა!", icon="✅")
        else:
            st.toast("❌ ნაკადი ვერ დასრულდა. შეამოწმე ლოგები.", icon="🚫")
        
        # ვთიშავთ დროშას, რომ შემდეგი ღილაკის დაჭერამდე არ გაეშვას
        st.session_state.run_pipeline = False
        st.rerun() # ბოლო განახლება სუფთა ინტერფეისისთვის

# ფეისერი
st.caption("""
💡 **როგორ მუშაობს:**
1. ზემოთ ხედავ ვიზუალურ დიაგრამას (Mermaid.js)
2. გვერდითა პანელში დააჭირე "გაუშვი ნაკადი"
3. ლოგები გამოჩნდება აქ, ქვემოთ
""")
