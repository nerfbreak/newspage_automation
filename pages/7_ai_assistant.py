import streamlit as st
from openai import OpenAI
import html
from utils import check_auth, render_header, render_footer, clean_html

# --- AUTH CHECK ---
check_auth()

# --- HEADER ---
render_header("AI Assistant", st.session_state.current_user)

# --- INIT OPENAI CLIENT ---
# We retrieve the NVIDIA API Key from Streamlit Secrets.
# Ensure that [secrets.toml] has: NVIDIA_API_KEY = "nvapi-..."
api_key = st.secrets.get("NVIDIA_API_KEY", "")
if not api_key:
    st.error("NVIDIA_API_KEY is missing from secrets.toml. Please add it to use the AI Assistant.")
    st.stop()

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=api_key
)

# --- INIT SESSION STATE FOR CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- HERO BANNER ---
st.markdown(f"""
<div style='margin-bottom: 24px;'>
    <h1 style='font-size: 2.2rem; font-weight: 800; color: #0F172A; margin: 0;'>DeepSeek AI 🤖</h1>
    <p style='font-size: 0.95rem; color: #64748B; margin-top: 4px; font-weight: 500;'>Tanya apa saja seputar data operasional atau analisa umum. Model ditenagai oleh DeepSeek-V4-Pro.</p>
</div>
""", unsafe_allow_html=True)

# --- CHAT CONTAINER ---
# We use a bordered container to follow the Neo-Brutalist styling
st.markdown("<span class='neo-container-marker'></span>", unsafe_allow_html=True)
with st.container(border=True, height=500):
    if len(st.session_state.messages) == 0:
        st.info("👋 Halo! Ada yang bisa saya bantu hari ini?")
        
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# --- CHAT INPUT ---
if prompt := st.chat_input("Ketik pesan Anda di sini..."):
    # 1. Tampilkan pesan user
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Panggil API DeepSeek
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            # We must map our session_state messages to the format expected by OpenAI/NVIDIA API
            api_messages = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
            
            completion = client.chat.completions.create(
                model="deepseek-ai/deepseek-v4-pro",
                messages=api_messages,
                temperature=0.7,
                top_p=0.95,
                max_tokens=2048,
                extra_body={"chat_template_kwargs": {"thinking": False}},
                stream=True
            )
            
            # Stream the response
            for chunk in completion:
                if chunk.choices[0].delta.content is not None:
                    full_response += chunk.choices[0].delta.content
                    message_placeholder.markdown(full_response + "▌")
                    
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            st.error(f"Terjadi kesalahan saat memanggil API: {e}")

render_footer()
