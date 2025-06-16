import os
import streamlit as st
import requests
from dotenv import load_dotenv, find_dotenv
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_huggingface import HuggingFaceEndpoint
import datetime
import streamlit.components.v1 as components
import time

# Load environment
load_dotenv(find_dotenv())
HF_TOKEN = "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"
HUGGINGFACE_REPO_ID = "HuggingFaceH4/zephyr-7b-beta"

# Disable file watcher bug in Streamlit
import streamlit.watcher.local_sources_watcher
streamlit.watcher.local_sources_watcher.get_module_paths = lambda module: []

# --- Load the LLM ---
def load_llm():
    return HuggingFaceEndpoint(
        repo_id=HUGGINGFACE_REPO_ID,
        temperature=0.3,
        huggingfacehub_api_token=HF_TOKEN,
        max_new_tokens=512,
        stop=["Context:", "Question:", "Answer:"]
    )

# --- Fetch real-time crypto context ---
def get_crypto_context():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        data = requests.get(url).json()
        price = data['bitcoin']['usd']
        return f"The current price of Bitcoin is ${price} USD."
    except Exception:
        return "Live Bitcoin price is currently unavailable."

def get_30_day_price_table():
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
    params = {"vs_currency": "usd", "days": 30}
    response = requests.get(url, params=params).json()

    prices = response["prices"]  # [ [timestamp, price], ... ]

    table = "| Date | Price (USD) |\n|------|--------------|\n"
    for timestamp, price in prices[-30:]:
        date = datetime.datetime.fromtimestamp(timestamp / 1000).strftime("%Y-%m-%d")
        table += f"| {date} | ${price:,.2f} |\n"

    return table

# --- Create a prompt template ---
crypto_prompt = PromptTemplate(
    template="""
You are an intelligent and creative crypto assistant. Use the current market context to answer the user's question carefully and accurately.ONLY answer the following question using the provided market context. Do NOT answer anything else or generate another question.

Your capabilities include:
1. If the question is about price predictions or future trends, offer a **balanced analysis** — never make guarantees, but share what might affect price direction.
2. For investment-related queries, explain risks and common strategies without direct advice.
3. For general knowledge, explain clearly and factually.
4. Always stick to the provided context for current data (like price).
5. You may reference **external macro trends** like regulations, ETFs, or halving cycles in your analysis.
6. Be creative when asked for humor.
7. Perform basic math for conversions and estimates.

- Answer ONLY the user's question.
- Do NOT invent or answer new questions.
- Do NOT output anything beyond what was asked.
- Use the context to reason, include math if needed.
- Be creative when asked for humor or analogies.
If you don't know something, be honest and say so.

Context:
{context}

Question:
{question}

Answer:
""",
    input_variables=["context", "question"]
)

# --- Streamlit App ---
def main():
    st.set_page_config(page_title="CryptoBot 💰", page_icon="🚀", layout="centered")
    st.title(" CryptoBot — Ask Anything About Bitcoin")
    st.markdown("""
<style>
html, body {
    background-color: #0f1117;
    overflow-x: hidden;
    font-family: 'Courier New', monospace;
}

.background-floaters {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    z-index: 0;
}

.floater {
    position: absolute;
    font-size: 34px;
    animation: float 20s linear infinite;
    opacity: 0.4; /* brighter visibility */
    filter: brightness(1.2); /* slight glow effect */
}

@keyframes float {
    0%   { transform: translateY(100vh) rotate(0deg); }
    100% { transform: translateY(-100vh) rotate(360deg); }
}

/* Make Streamlit's content show above background */
.block-container {
    position: relative;
    z-index: 1;
}
</style>

<div class="background-floaters">
    <div class="floater" style="left: 5%; animation-delay: 0s;">💵</div>
    <div class="floater" style="left: 15%; animation-delay: 3s;">₿</div>
    <div class="floater" style="left: 25%; animation-delay: 5s;">💰</div>
    <div class="floater" style="left: 35%; animation-delay: 7s;">📉</div>
    <div class="floater" style="left: 45%; animation-delay: 9s;">📈</div>
    <div class="floater" style="left: 55%; animation-delay: 11s;">💸</div>
    <div class="floater" style="left: 65%; animation-delay: 13s;">🪙</div>
    <div class="floater" style="left: 75%; animation-delay: 15s;">💹</div>
    <div class="floater" style="left: 85%; animation-delay: 17s;">🤑</div>
    <div class="floater" style="left: 95%; animation-delay: 19s;">🏦</div>
</div>
""", unsafe_allow_html=True)



    sample_prompts = [
        "What is the current price of Bitcoin?",
        "Should I buy Bitcoin now or wait?",
        "Tell me a joke about Bitcoin’s price?",
        "How much Bitcoin can I get for $1000?",
        "Give me the 30-day price trend of BTC."
    ]

    st.markdown("### Try a sample question:")
    for question in sample_prompts:
        if st.button(question):
            st.session_state["auto_prompt"] = question

    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_prompt = st.chat_input("Ask your crypto question...")
    if "auto_prompt" in st.session_state:
        user_prompt = st.session_state.pop("auto_prompt")

    if user_prompt:
        st.chat_message("user").markdown(user_prompt)
        st.session_state["messages"].append({"role": "user", "content": user_prompt})

        with st.spinner("Thinking like Satoshi... 💭"):
            try:
                context = get_30_day_price_table()
                llm_chain = LLMChain(llm=load_llm(), prompt=crypto_prompt)
                response = llm_chain.invoke({
                    "context": context,
                    "question": user_prompt
                })
                result = response["text"]
                st.chat_message("assistant").markdown(result)
                st.session_state["messages"].append({"role": "assistant", "content": result})

            except Exception as e:
                st.error(f"Error: {e}")

if __name__ == "__main__":
    main()