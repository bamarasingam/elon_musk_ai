import streamlit as st
import numpy as np
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForCausalLM
import faiss
import torch
import json

# Load data and models (you might want to cache these operations)
@st.cache_resource
def load_data_and_models():
    with open('speech_total.json', 'r') as file:
        speech_total = json.load(file)
    
    embed_model = SentenceTransformer('all-MiniLM-L6-v2')
    index = faiss.read_index("faiss_index.bin")
    
    model_name = "distilgpt2"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name)
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    
    return speech_total, embed_model, index, tokenizer, model, device

speech_total, embed_model, index, tokenizer, model, device = load_data_and_models()

def retrieve_context(query, k=3):
    query_embedding = embed_model.encode([query])[0]
    D, I = index.search(np.array([query_embedding]).astype('float32'), k)
    retrieved_texts = [speech_total[i] for i in I[0]]
    return " ".join(retrieved_texts)

def generate_response(query, max_new_tokens=50):
    context = retrieve_context(query)
    prompt = f"Context: {context}\n\nQuery: {query}\n\nResponse:"
    
    input_ids = tokenizer.encode(prompt, return_tensors="pt").to(device)
    attention_mask = torch.ones(input_ids.shape, dtype=torch.long, device=device)
    
    output = model.generate(
        input_ids,
        attention_mask=attention_mask,
        max_new_tokens=max_new_tokens,
        num_return_sequences=1,
        no_repeat_ngram_size=2,
        temperature=0.7
    )
    
    response = tokenizer.decode(output[0], skip_special_tokens=True)
    return response.split("Response:")[-1].strip()

# Streamlit app
st.title("Ask Elon Musk")

user_question = st.text_input("What would you like to ask Elon Musk?")

if user_question:
    with st.spinner("Generating response..."):
        answer = generate_response(user_question)
    st.write("Elon's response:")
    st.write(answer)

st.markdown("---")
st.write("This app uses a language model trained on Elon Musk's speeches and interviews to generate responses.")