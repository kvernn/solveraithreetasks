import streamlit as st
import asyncio
from chatbot import generate_contextual_response

st.set_page_config(page_title="Bob's Shoe Recommender", page_icon="👟", layout="centered")

st.title("👟 Bob's Shoe Recommender")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_product" not in st.session_state:
    st.session_state.last_product = None

if st.button("Clear Conversation History"):
    st.session_state.messages = []
    st.session_state.last_product = None
    st.rerun()

if not st.session_state.messages:
    st.session_state.messages.append({"role": "assistant", "content": "Hellooo! I am Bob and I am your dearest assistant for today. Please tell me, how can I help you, and what are you looking for?"})

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("What kind of shoe are you looking for?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
    with st.spinner("Bob is thinking... 🤔"):
        try:
            final_answer, product_to_remember = asyncio.run(generate_contextual_response(
                st.session_state.messages,
                st.session_state.last_product
            ))
            message_placeholder.markdown(final_answer)
            st.session_state.messages.append({"role": "assistant", "content": final_answer})

            if product_to_remember:
                st.session_state.last_product = product_to_remember

        except Exception as e:
            error_message = f"Aiyooo, something went wrong lah! Error: {e}"
            message_placeholder.error(error_message)