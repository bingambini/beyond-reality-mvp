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
    """ავტომატურად პოულობს საუკეთესო ხელმისაწვდომ Gemini მოდელს"""
    try:
        genai.configure(api_key=api_key)
        models = genai.list_models()
        preferred_models = [
            "gemini-1.5-flash",
            "gemini-1.5-flash-latest",
            "gemini-pro",
            "gemini-1.0-pro",
        ]
        
        available_models = []
        for model in models:
            if 'generateContent' in model.supported_generation_methods:
                model_name = model.name.replace("models/", "")
                available_models.append(model_name)
        
        for preferred in preferred_models:
            if preferred in available_models:
                return genai.GenerativeModel(preferred)
        
        if available_models:
            return genai.GenerativeModel(available_models[0])
        
        raise Exception("არცერთი Gemini მოდელი არ არის ხელმისაწვდომი")
    except Exception as e:
        return genai.GenerativeModel("gemini-pro")

secrets = load_secrets()
template = load_template()

# --- 2. ინტერფეისი ---
st.title("🏛️ Beyond Reality — Control Panel")
st.markdown("*AI Content Empire | Psych Tests MVP*")

# სტატუსის მეტრიკები
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
        
with col2: st.metric("HF API", "🟢 Active" if secrets["HF"] else "🔴 Missing")
with col3: st.metric("Template", "📄 Loaded")

tab1, tab2, tab3 = st.tabs(["⚙️ გენერაცია", "📤 დისტრიბუცია", "💰 მონეტიზაცია"])

with tab1:
    st.subheader("🔮 ტესტის გენერაცია (Director Mode)")
    
    lang = st.selectbox("🌐 ენა", template["languages"], index=0)
    setting = st.selectbox("🖼️ სცენა (ფონი)", template["generation"]["image_settings"])
    
    if st.button("🚀 დაიწყე გენერაცია", type="primary"):
        with st.spinner("🤖 დირიჟორი მუშაობს: 1. ტექსტი... 2. 3 სურათი... 3. შეკერვა..."):
            try:
                # --- A. ტექსტის გენერაცია (Gemini) ---
                model = get_best_gemini_model(secrets["GEMINI"])
                prompt_text = template["generation"]["text_prompt"].replace("{language}", lang)
                text_response = model.generate_content(prompt_text)
                
                # --- B. სურათების გენერაცია (დირიჟორის ლოგიკა) ---
                client = InferenceClient(api_key=secrets["HF"])
                base_prompt = template["generation"]["image_prompt"].replace("{setting}", setting)
                
                # დირიჟორი აძლევს კონკრეტულ სტილს თითოეულ კარს (A, B, C)
                door_styles = [
                    "dark ancient wooden door with iron rings, mysterious glow", # სტილი A
                    "ornate gothic metal door with gold details, tall and elegant", # სტილი B
                    "glowing magical door made of crystal and stone, ethereal light"  # სტილი C
                ]
                
                generated_images = []
                for i in range(3):
                    # დირიჟორი აკონკრეტებს: მხოლოდ ერთი ობიექტი, CLOSE UP
                    specific_prompt = f"{base_prompt}, SINGLE door in center, {door_styles[i]}, close up shot, no other doors, vertical composition"
                    
                    # ვამატებთ პარამეტრებს უკეთესი ხარისხისთვის
                    img = client.text_to_image(
                        prompt=specific_prompt, 
                        model="black-forest-labs/FLUX.1-schnell",
                        guidance_scale=7.5,
                        num_inference_steps=25
                    )
                    generated_images.append(img)
                
                # --- C. შეკერვა (Collage Logic) ---
                # ვამოწმებთ რომ სურათები ერთი ზომის იყოს
                target_size = (768, 1024) # Vertical 3:4 approx
                resized_images = [img.resize(target_size) for img in generated_images]
                
                # ვქმნით ცარიელ კანვასს (სიმაღლე = 3 * სურათის სიმაღლე)
                total_height = target_size[1] * 3
                canvas = Image.new('RGB', (target_size[0], total_height), color=(20, 20, 20))
                
                # ვაკრავთ სურათებს ერთმანეთს (ზემოდან ქვემოთ)
                canvas.paste(resized_images[0], (0, 0))
                canvas.paste(resized_images[1], (0, target_size[1]))
                canvas.paste(resized_images[2], (0, target_size[1] * 2))
                
                # --- შედეგების შენახვა ---
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
