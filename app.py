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

@st.cache_resource
def get_best_gemini_model(api_key):
    """ავტომატურად პოულობს საუკეთესო ხელმისაწვდომ Gemini მოდელს"""
    try:
        genai.configure(api_key=api_key)
        # მივიღოთ ყველა მოდელი, რომელსაც აქვს generateContent მეთოდი
        models = genai.list_models()
        
        # ვეძებთ უფასო/სტაბილურ მოდელებს პრიორიტეტის მიხედვით
        preferred_models = [
            "gemini-1.5-flash",      # ყველაზე სწრაფი და იაფი
            "gemini-1.5-flash-latest",
            "gemini-pro",            # სტაბილური
            "gemini-1.0-pro",
        ]
        
        available_models = []
        for model in models:
            if 'generateContent' in model.supported_generation_methods:
                model_name = model.name.replace("models/", "")
                available_models.append(model_name)
        
        # ვეძებთ პირველ სასურველ მოდელს
        for preferred in preferred_models:
            if preferred in available_models:
                return genai.GenerativeModel(preferred)
        
        # თუ არცერთი სასურველი არ არის, ვიღებთ პირველ ხელმისაწვდომს
        if available_models:
            return genai.GenerativeModel(available_models[0])
        
        raise Exception("არცერთი Gemini მოდელი არ არის ხელმისაწვდომი")
        
    except Exception as e:
        st.error(f"⚠️ მოდელის შერჩევის შეცდომა: {str(e)}")
        # Fallback: ვცადოთ gemini-pro
        return genai.GenerativeModel("gemini-pro")

secrets = load_secrets()
template = load_template()

# --- 2. ინტერფეისი ---
st.title("🏛️ Beyond Reality — Control Panel")
st.markdown("*AI Content Empire | Psych Tests MVP*")

# API სტატუსი
col1, col2, col3 = st.columns(3)
with col1: 
    if secrets["GEMINI"]:
        try:
            model = get_best_gemini_model(secrets["GEMINI"])
            st.metric("Gemini API", f"🟢 {model.model_name}")
        except:
            st.metric("Gemini API", "🔴 Error")
    else:
        st.metric("Gemini API", "🔴 Missing Key")
        
with col2: st.metric("HF API", "🟢 Ready" if secrets["HF"] else "🔴 Missing")
with col3: st.metric("Template", "📄 Loaded")

tab1, tab2, tab3 = st.tabs(["⚙️ გენერაცია", "📤 დისტრიბუცია", "💰 მონეტიზაცია"])

with tab1:
    st.subheader("🔮 ტესტის გენერაცია")
    
    lang = st.selectbox("🌐 ენა", template["languages"], index=0)
    setting = st.selectbox("🖼️ სცენა", template["generation"]["image_settings"])
    
    if st.button("🚀 დაიწყე გენერაცია", type="primary"):
        with st.spinner("🤖 AI მუშაობს... შეიძლება 10-30 წამი დასჭირდეს"):
            try:
                # ტექსტის გენერაცია (Gemini)
                model = get_best_gemini_model(secrets["GEMINI"])
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
