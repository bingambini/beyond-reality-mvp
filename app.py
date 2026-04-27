import streamlit as st

# გვერდის კონფიგურაცია
st.set_page_config(
    page_title="Beyond Reality — MVP",
    page_icon="🏛️",
    layout="wide"
)

# სათაური
st.title("🏛️ Beyond Reality — Control Panel")
st.markdown("*AI Content Empire | Psych Tests MVP*")

# სტატუსის პანელი
st.subheader("📊 სისტემის სტატუსი")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("API Status", "🟡 მომზადება")
with col2:
    st.metric("ქვოტები", "–")
with col3:
    st.metric("დღიური შემოსავალი", "$0.00")

# მთავარი მენიუ
st.subheader("🎛️ მენიუ")
tab1, tab2, tab3 = st.tabs(["⚙️ გენერაცია", "📤 დისტრიბუცია", "💰 მონეტიზაცია"])

with tab1:
    st.write("### ტესტის გენერაცია")
    st.info("🚧 ეს მონაკვეთი მზადდება...")
    st.selectbox("აირჩიე ტესტის ტიპი", ["🚪 კარის არჩევანი", "🔮 ფერის ფსიქოლოგია", "🎭 პიროვნების ტიპი"])
    st.selectbox("ენა", ["ქართული", "ინგლისური", "გერმანული"])
    st.text_area("დამატებითი ინსტრუქცია (ოფციონალური)")
    st.button("🔄 გენერაცია", disabled=True)

with tab2:
    st.write("### გამოქვეყნება")
    st.info("🚧 ეს მონაკვეთი მზადდება...")
    st.checkbox("TikTok", disabled=True)
    st.checkbox("Telegram", disabled=True)
    st.checkbox("YouTube Shorts", disabled=True)
    st.button("📤 გამოქვეყნება", disabled=True)

with tab3:
    st.write("### შემოსავალი")
    st.info("🚧 ეს მონაკვეთი მზადდება...")
    st.write("**Telegram Stars:** 0 ⭐ ($0.00)")
    st.write("**Affiliate:** $0.00")

# ფუტერი
st.markdown("---")
st.caption("Beyond Reality v0.1 | 100% Cloud | 0$ Budget")
