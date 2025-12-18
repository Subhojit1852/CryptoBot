import os
import streamlit as st
import requests
from dotenv import load_dotenv, find_dotenv
# from langchain.chains.llm import LLMChain
from langchain_core.prompts import PromptTemplate
try:
    from langchain_openai import ChatOpenAI
except ImportError:
    from langchain.chat_models import ChatOpenAI
import datetime
import streamlit.components.v1 as components
import time

# Load environment
load_dotenv()

# Configure OpenRouter
os.environ["OPENAI_API_KEY"] = st.secrets["OPENROUTER_API_KEY"]
os.environ["OPENAI_BASE_URL"] = "https://openrouter.ai/api/v1"

# --- Load the LLM (Mistral-7B) ---
def load_llm():
    return ChatOpenAI(
        model="mistralai/mistral-7b-instruct",
        temperature=0.3,
        max_tokens=512,
        openai_api_key=st.secrets["OPENROUTER_API_KEY"],  # Directly pass API key
        openai_api_base="https://openrouter.ai/api/v1",
        # headers={"HTTP-Referer": "https://your-site.com"},  # Required by OpenRouter
    )


# --- Fetch crypto data ---
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

    prices = response["prices"]
    table = "| Date | Price (USD) |\n|------|--------------|\n"
    for timestamp, price in prices[-30:]:
        date = datetime.datetime.fromtimestamp(timestamp / 1000).strftime("%Y-%m-%d")
        table += f"| {date} | ${price:,.2f} |\n"
    return table

# --- Prompt Template ---
crypto_prompt = PromptTemplate(
    template="""
You are an intelligent crypto assistant. Use the context to answer the question.

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
    st.title("CryptoBot — Ask Anything About Bitcoin")
    
    # Background animation
    components.html("""
    <style>
    .floater {
        position: fixed;
        font-size: 34px;
        animation: float 20s linear infinite;
        opacity: 0.4;
        filter: brightness(1.2);
    }
    @keyframes float {
        0% { transform: translateY(100vh) rotate(0deg); }
        100% { transform: translateY(-100vh) rotate(360deg); }
    }
    </style>
    <div class="floater" style="left:5%">💵</div>
    <div class="floater" style="left:15%">₿</div>
    <div class="floater" style="left:25%">💰</div>
    """)

    sample_prompts = [
        "What is the current price of Bitcoin?",
        "Should I buy Bitcoin now or wait?",
        "Tell me a joke about Bitcoin's price?",
        "How much Bitcoin can I get for $1000?"
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

        with st.spinner("Analyzing the blockchain..."):
            try:
                context = get_30_day_price_table()
                chain = crypto_prompt | load_llm()

                response = chain.invoke({
                    "context": context,
                    "question": user_prompt
                })

                result = response.content.strip()


                st.chat_message("assistant").markdown(result)
                st.session_state["messages"].append({"role": "assistant", "content": result})
            except Exception as e:
                st.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main()