import streamlit as st
from chatbot import generate_contextual_response

st.set_page_config(page_title="Bob's Shoe Recommender", page_icon="👟", layout="centered")

st.title("👟 Bob's Shoe Recommender")

# --- Initialize session state for chat history AND the last seen product ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_product" not in st.session_state:
    st.session_state.last_product = None

if st.button("Clear Conversation History"):
    st.session_state.messages = []
    st.session_state.last_product = None # Also clear the last product
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
        with st.spinner("Bob is thinking... 🤔"):
            try:
                # --- Pass the "notepad" (last_product) to our function ---
                final_answer, product_to_remember = generate_contextual_response(
                    st.session_state.messages,
                    st.session_state.last_product
                )
                st.markdown(final_answer)
                st.session_state.messages.append({"role": "assistant", "content": final_answer})

                # --- If the function found a new product, save it to our "notepad" ---
                if product_to_remember:
                    st.session_state.last_product = product_to_remember

            except Exception as e:
                error_message = f"Aiyooo, something went wrong lah! Error: {e}"
                st.error(error_message)