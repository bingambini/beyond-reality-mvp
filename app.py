import streamlit as st
import json
import google.generativeai as genai
from huggingface_hub import InferenceClient

# გვერდის კონფიგურაცია
st.set_page_config(page_title="Beyond Reality — MVP", page_icon="🏛️", layout="wide")

# --- 1. მონაცემების ჩატვირთვა ---
@st.cache_resource
def load_secrets():
    return {
        "GEMINI": st.secrets.get("GEMINI_API_KEY"),
        "HF": st.secrets.get("HF_API_KEY")
    }

@st.cache_data
def load_template():
    with open("config/templates/psych_test_door_choice_v1.json", "r", encoding="utf-8") as f:
        return json.load(f)

secrets = load_secrets()
template = load_template()

# --- 2. ინტერფეისი ---
st.title("🏛️ Beyond Reality — Control Panel")
st.markdown("*AI Content Empire | Psych Tests MVP*")

col1, col2, col3 = st.columns(3)
with col1: st.metric("API Status", "🟢 Active" if secrets["GEMINI"] else "🔴 Missing")
with col2: st.metric("Template", "📄 Loaded")
with col3: st.metric("დღიური შემოსავალი", "$0.00")

tab1, tab2, tab3 = st.tabs(["⚙️ გენერაცია", "📤 დისტრიბუცია", "💰 მონეტიზაცია"])

with tab1:
    st.subheader("🔮 ტესტის გენერაცია")
    
    lang = st.selectbox(" ენა", template["languages"], index=0)
    setting = st.selectbox("🖼️ სცენა", template["generation"]["image_settings"])
    
    if st.button("🚀 დაიწყე გენერაცია", type="primary"):
        with st.spinner("AI მუშაობს... შეიძლება 10-20 წამი დასჭირდეს"):
            try:
                # ტექსტის გენერაცია (Gemini)
                genai.configure(api_key=secrets["GEMINI"])
                model = genai.GenerativeModel("gemini-1.5-flash")
                prompt_text = template["generation"]["text_prompt"].replace("{language}", lang)
                text_response = model.generate_content(prompt_text)
                
                # სურათის გენერაცია (Hugging Face)
                client = InferenceClient(api_key=secrets["HF"])
                prompt_img = template["generation"]["image_prompt"].replace("{setting}", setting)
                image_response = client.text_to_image(prompt_img, model="black-forest-labs/FLUX.1-schnell")
                
                # შედეგების შენახვა
                st.session_state['gen_text'] = text_response.text
                st.session_state['gen_image'] = image_response
                
                st.success("✅ წარმატებით დაგენერირდა!")
                
            except Exception as e:
                st.error(f"❌ შეცდომა: {str(e)}")

    # შედეგების ჩვენება
    if 'gen_text' in st.session_state:
        st.divider()
        st.subheader("📝 შედეგები")
        col_a, col_b = st.columns(2)
        with col_a:
            st.text_area("გენერირებული ტექსტი", st.session_state['gen_text'], height=300)
        with col_b:
            st.image(st.session_state['gen_image'], caption="AI სურათი", use_column_width=True)

with tab2: st.info("🚧 დისტრიბუციის მოდული მომზადებაშია...")
with tab3: st.info("🚧 მონეტიზაციის მოდული მომზადებაშია...")
