import streamlit as st
import openai
from llama_index.llms.openai import OpenAI
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings, StorageContext, load_index_from_storage
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

import os
import django
from django.conf import settings
import logging

LOGGER = logging.getLogger(__name__)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "src.heimdall.settings")
django.setup()

st.set_page_config(page_title="Chat with the Streamlit docs, powered by LlamaIndex", page_icon="🦙", layout="centered", initial_sidebar_state="auto", menu_items=None)
st.title("Chat with your infosec docs")

openai.api_key = settings.OPENAI_API_KEY

PERSIST_DIR = os.path.join(settings.PROJECT_DIR, 'storage')

if "messages" not in st.session_state.keys():  # Initialize the chat messages history
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Ask me a question about your information security documents!",
        }
    ]

@st.cache_resource(show_spinner=False)
def load_data():
    Settings.llm = OpenAI(
        model="gpt-3.5-turbo",
        temperature=0.1,
        system_prompt="""You are an expert on 
        the information security and your 
        job is to answer technical questions. 
        Assume that all questions are related 
        to the linked documents. Keep 
        your answers technical and based on 
        facts – do not hallucinate features.""",
    )
    Settings.embed_model = HuggingFaceEmbedding(
        model_name="BAAI/bge-small-en-v1.5" # free open source embedding model from huggingface. openai ada is super expensive!
    )

    if os.path.exists(PERSIST_DIR): # replace with database storage later
        # load the existing index
        LOGGER.info("Found existing stored index. Loading...")
        storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
        index = load_index_from_storage(storage_context)
        return index

    reader = SimpleDirectoryReader(input_dir="./data", recursive=True, required_exts=[".pdf", ".docx", ".xlsx"])
    docs = reader.load_data()
    index = VectorStoreIndex.from_documents(docs)
    index.storage_context.persist(persist_dir=PERSIST_DIR)
    return index


index = load_data()

if "chat_engine" not in st.session_state.keys():  # Initialize the chat engine
    st.session_state.chat_engine = index.as_chat_engine(
        chat_mode="condense_plus_context", verbose=True, streaming=True
    )

if prompt := st.chat_input(
    "Ask a question"
):  # Prompt for user input and save to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

for message in st.session_state.messages:  # Write message history to UI
    with st.chat_message(message["role"]):
        st.write(message["content"])

# If last message is not from assistant, generate a new response
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        response_stream = st.session_state.chat_engine.stream_chat(prompt)
        st.write_stream(response_stream.response_gen)
        message = {"role": "assistant", "content": response_stream.response}
        # Add response to message history
        st.session_state.messages.append(message)