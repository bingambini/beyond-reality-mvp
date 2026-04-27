import streamlit as st
import json
import google.generativeai as genai
from huggingface_hub import InferenceClient
from PIL import Image
import io

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
    try:
        genai.configure(api_key=api_key)
        models = genai.list_models()
        preferred_models = ["gemini-1.5-flash", "gemini-pro", "gemini-1.0-pro"]
        available_models = [m.name.replace("models/", "") for m in models if 'generateContent' in m.supported_generation_methods]
        
        for preferred in preferred_models:
            if preferred in available_models:
                return genai.GenerativeModel(preferred)
        return genai.GenerativeModel(available_models[0]) if available_models else genai.GenerativeModel("gemini-pro")
    except Exception as e:
        return genai.GenerativeModel("gemini-pro")

secrets = load_secrets()
template = load_template()

# --- 2. ინტერფეისი ---
st.title("🏛️ Beyond Reality — Control Panel")
st.markdown("*AI Content Empire | Psych Tests MVP*")

col1, col2, col3 = st.columns(3)
with col1: st.metric("Gemini API", "🟢 Active" if secrets["GEMINI"] else "🔴 Missing")
with col2: st.metric("HF API", "🟢 Active" if secrets["HF"] else "🔴 Missing")
with col3: st.metric("Template", "📄 Loaded")

tab1, tab2, tab3 = st.tabs(["⚙️ გენერაცია", "📤 დისტრიბუცია", "💰 მონეტიზაცია"])

with tab1:
    st.subheader("🔮 ტესტის გენერაცია (სტრუქტურული)")
    
    lang = st.selectbox("🌐 ენა", template["languages"], index=0)
    setting = st.selectbox("🖼️ სცენა (ფონი)", template["generation"]["image_settings"])
    
    if st.button("🚀 დაიწყე გენერაცია (Director Mode)", type="primary"):
        with st.spinner("🤖 დირიჟორი მუშაობს: 1. ტექსტი... 2. 3 სურათი... 3. შეკერვა..."):
            try:
                # A. ტექსტის გენერაცია
                model = get_best_gemini_model(secrets["GEMINI"])
                prompt_text = template["generation"]["text_prompt"].replace("{language}", lang)
                text_response = model.generate_content(prompt_text)
                
                # B. სურათების გენერაცია (Loop 3-ჯერ)
                # დირიჟორის ლოგიკა: არ ვთხოვთ 3 კარს ერთ სურათზე. ვქმნით 3 სურათს.
                client = InferenceClient(api_key=secrets["HF"])
                base_prompt = template["generation"]["image_prompt"].replace("{setting}", setting)
                
                generated_images = []
                for i in range(3):
                    # ვარიაცია პრომპტში, რომ სურათები განსხვავებული იყოს
                    variation_prompt = f"{base_prompt}, distinct door style {i+1}, unique design"
                    img = client.text_to_image(variation_prompt, model="black-forest-labs/FLUX.1-schnell")
                    generated_images.append(img)
                
                # C. შეკერვა (Collage Logic)
                # ვამოწმებთ რომ სურათები ერთი ზომის იყოს
                target_size = (768, 1024) # Vertical 3:4 approx
                resized_images = [img.resize(target_size) for img in generated_images]
                
                # ვქმნით ცარიელ კანვასს (სიმაღლე = 3 * სურათის სიმაღლე)
                total_height = target_size[1] * 3
                canvas = Image.new('RGB', (target_size[0], total_height), color=(20, 20, 20))
                
                # ვაკრავთ სურათებს
                canvas.paste(resized_images[0], (0, 0))
                canvas.paste(resized_images[1], (0, target_size[1]))
                canvas.paste(resized_images[2], (0, target_size[1] * 2))
                
                # შედეგების შენახვა
                st.session_state['gen_text'] = text_response.text
                st.session_state['gen_image'] = canvas # ახლა ეს არის შეკერილი სურათი
                
                st.success("✅ დირიჟორმა წარმატებით შეკრა სურათი!")
                
            except Exception as e:
                st.error(f"❌ შეცდომა: {str(e)}")

    # შედეგების ჩვენება
    if 'gen_text' in st.session_state:
        st.divider()
        st.subheader("📝 შედეგები (ტრიპტიქი)")
        col_a, col_b = st.columns([1, 1])
        with col_a:
            st.text_area("გენერირებული ტექსტი", st.session_state['gen_text'], height=400)
        with col_b:
            # ვაჩვენებთ შეკერილ სურათს
            st.image(st.session_state['gen_image'], caption="🚪 3 კარი (დირიჟორის მიერ შეკერილი)", use_column_width=True)

with tab2: st.info("🚧 დისტრიბუციის მოდული მომზადებაშია...")
with tab3: st.info("🚧 მონეტიზაციის მოდული მომზადებაშია...")
