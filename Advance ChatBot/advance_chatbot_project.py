from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.llms import Ollama
import streamlit as st
from dotenv import load_dotenv
from fpdf import FPDF
from io import BytesIO
import unicodedata
import os

# Load environment variables
load_dotenv()

# ----------------- PAGE CONFIG -----------------
st.set_page_config(page_title="Llama3 Chatbot", layout="centered")
st.title("✨🤖 Quantum Chat")

# ----------------- CSS -----------------
st.markdown("""
    <style>
    .reportview-container { background-color: #f5f5f5; }
    .stTextInput>div>div>input { font-size: 18px; }
    .sidebar-message {
        animation: fadeIn 0.5s ease-in;
        margin-bottom: 10px;
        padding: 6px;
        background-color: #ffffff11;
        border-radius: 10px;
    }
    @keyframes fadeIn {
        from {opacity: 0; transform: translateX(-10px);}
        to {opacity: 1; transform: translateX(0);}
    }
    .chat-input-container {
        animation: slideFadeIn 0.4s ease;
    }
    @keyframes slideFadeIn {
        from {opacity: 0; transform: translateY(10px);}
        to {opacity: 1; transform: translateY(0);}
    }
    .floating-button {
        position: fixed;
        bottom: 30px;
        right: 30px;
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 14px 20px;
        border-radius: 50px;
        font-size: 18px;
        box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.2);
        cursor: pointer;
        z-index: 1000;
        transition: all 0.3s ease-in-out;
    }
    .floating-button:hover {
        background-color: #45a049;
        transform: scale(1.1);
    }
    </style>
""", unsafe_allow_html=True)

# ----------------- INITIAL STATE -----------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [("system", "You are a helpful AI assistant.")]
if "show_chat_input" not in st.session_state:
    st.session_state.show_chat_input = True
if "selected_message" not in st.session_state:
    st.session_state.selected_message = None
if "starred_messages" not in st.session_state:
    st.session_state.starred_messages = []
if "edit_index" not in st.session_state:
    st.session_state.edit_index = None

# ----------------- TEMPERATURE -----------------
temperature = st.slider("🔧 Set Model Temperature", 0.0, 1.0, 0.7)

# ----------------- MODEL -----------------
llm = Ollama(model="deepseek-r1:1.5b", temperature=temperature)
output_parser = StrOutputParser()

# ----------------- SANITIZE & EXPORT PDF -----------------
def sanitize_text(text):
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")

def export_chat_to_pdf(chat_history):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    pdf.set_title("Chat History")

    for role, message in chat_history:
        if role == "system":
            continue
        icon = "You" if role == "user" else "Bot"
        clean_msg = sanitize_text(message)
        pdf.multi_cell(0, 10, f"{icon}: {clean_msg}", border=0, align="L")
        pdf.ln(2)

    buffer = BytesIO()
    buffer.write(bytes(pdf.output(dest='S')))
    buffer.seek(0)
    return buffer

# ----------------- CLEAR BUTTON -----------------
if st.button("🗑️ Clear Chat"):
    st.session_state.chat_history = [("system", "You are a helpful AI assistant.")]
    st.session_state.selected_message = None
    st.session_state.edit_index = None
    st.session_state.starred_messages = []
    st.rerun()

# ----------------- SIDEBAR -----------------
with st.sidebar:
    st.header("📜 Chat History")
    search_term = st.text_input("🔍 Search", value=st.session_state.get("search_term", ""))
    st.session_state.search_term = search_term.lower()

    for i, (role, message) in enumerate(st.session_state.chat_history):
        if role == "system":
            continue
        if st.session_state.search_term and st.session_state.search_term not in message.lower():
            continue

        icon = "🧑‍💻" if role == "user" else "🤖"
        preview = message[:25] + "..." if len(message) > 25 else message
        starred = i in st.session_state.starred_messages

        col1, col2, col3 = st.columns([6, 1, 1])
        with col1:
            if st.button(f"{icon} {preview}", key=f"msg_{i}"):
                st.session_state.selected_message = (role, message)
                st.session_state.selected_index = i
        with col2:
            if st.button("⭐" if not starred else "✅", key=f"star_{i}"):
                if starred:
                    st.session_state.starred_messages.remove(i)
                else:
                    st.session_state.starred_messages.append(i)
                st.rerun()
        with col3:
            if st.button("✏️", key=f"edit_{i}"):
                st.session_state.edit_index = i
                st.session_state.edit_text = message
                st.session_state.selected_message = None
                st.rerun()

    if st.button("📄 Export Chat to PDF"):
        pdf_buffer = export_chat_to_pdf(st.session_state.chat_history)
        st.download_button("📥 Download PDF", data=pdf_buffer, file_name="chat_history.pdf", mime="application/pdf")

    if st.button("🧼 New Chat"):
        st.session_state.chat_history = [("system", "You are a helpful AI assistant.")]
        st.session_state.selected_message = None
        st.session_state.edit_index = None
        st.session_state.starred_messages = []
        st.rerun()

# ----------------- MAIN DISPLAY -----------------
if st.session_state.edit_index is not None:
    idx = st.session_state.edit_index
    role, _ = st.session_state.chat_history[idx]

    with st.form("edit_form"):
        new_text = st.text_area("✏️ Edit Message", value=st.session_state.get("edit_text", ""))
        save = st.form_submit_button("📏 Save")
        cancel = st.form_submit_button("❌ Cancel")

    if save:
        st.session_state.chat_history[idx] = (role, new_text)
        st.session_state.edit_index = None
        st.session_state.edit_text = ""
        st.rerun()
    elif cancel:
        st.session_state.edit_index = None
        st.rerun()

elif st.session_state.selected_message:
    role, message = st.session_state.selected_message
    icon = "🧑‍💻" if role == "user" else "🤖"
    st.markdown(f"### {icon} {role.capitalize()}:\n\n{message}")
    if st.button("🔁 Back to Full Chat View"):
        st.session_state.selected_message = None
        st.rerun()
else:
    for role, message in st.session_state.chat_history:
        if role == "user":
            st.markdown(f"**🗣️ You:** {message}")
        elif role == "assistant":
            st.markdown(f"**🔊 Bot:** {message}")

# ----------------- FLOATING BUTTON -----------------
st.markdown("""
    <form action='#' method='post'>
        <button class="floating-button" name="add_chat" type="submit">➕</button>
    </form>
""", unsafe_allow_html=True)

# ----------------- HANDLE INPUT -----------------
query_params = st.query_params
if "add_chat" in st.session_state or "add_chat" in query_params:
    st.session_state.show_chat_input = True

if st.session_state.show_chat_input:
    with st.container():
        st.markdown('<div class="chat-input-container">', unsafe_allow_html=True)
        with st.form("chat_form", clear_on_submit=True):
            user_input = st.text_input("💬 Type your next message here", key="user_input")
            submitted = st.form_submit_button("Send")
        st.markdown('</div>', unsafe_allow_html=True)

    if submitted and user_input:
        st.session_state.chat_history.append(("user", user_input))
        prompt = ChatPromptTemplate.from_messages(st.session_state.chat_history)
        chain = prompt | llm | output_parser

        with st.spinner("🧐 Thinking..."):
            try:
                response = chain.invoke({})
                st.session_state.chat_history.append(("assistant", response))
                st.rerun()
            except Exception as e:
                st.session_state.chat_history.append(("assistant", f"Error: {e}"))
                st.rerun()
