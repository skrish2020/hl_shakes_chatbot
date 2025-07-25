import streamlit as st
import os
from langchain_groq import ChatGroq
from langchain_community.document_loaders import WebBaseLoader
#from langchain.embeddings import OllamaEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.document_loaders.merge import MergedDataLoader
from langchain_community.document_loaders import UnstructuredHTMLLoader,BSHTMLLoader,DirectoryLoader
from langchain_huggingface import HuggingFaceEmbeddings
import time

from dotenv import load_dotenv
load_dotenv()

##load groq and openai api keys
os.environ['OPENAI_API_KEY'] = os.getenv("OPENAI_API_KEY")
groq_api_key = os.getenv('GROQ_API_KEY')

st.title("Ask me \n Please note: I am an AI agent answering delicious recipe questions using LLMs! \n" 
+ "I am a rookie. Please pardon my mistake(s) if any!")
llm = ChatGroq(groq_api_key=groq_api_key,
               #model_name="Llama3-8b-8192")
                model_name="gemma2-9b-it")


prompt=ChatPromptTemplate.from_template(
"""
Answer the questions based on the provided context only. 
Please use only the material provided to base your answer. 
Do to include any external material. 
Please be precise. Please do not include these words:"Based on the provided context"
Please provide the most accurate response based on the question
Please provide an elaborated response. If you have a list of products, put them in a bulleted list
List all products
<context>
{context}
<context>
Questions:{input}

"""
)
os.environ['HF_TOKEN']=os.getenv("HF_TOKEN")
embeddings=HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

def vector_embeddings():
      if "vectors" not in st.session_state:
        #create embeddings
        #st.session_state.embeddings=OpenAIEmbeddings()
        st.session_state.embeddings=embeddings
        pdfloader = PyPDFDirectoryLoader("../ea_files/pdf") ##Data ingestion
        #webbaseloader = WebBaseLoader("https://docs.smith.langchain.com/user_guide")
        htmlloader=DirectoryLoader("../ea_files/html",glob="**/*.mhtml",loader_cls=BSHTMLLoader)
        #docs=htmlloader.load()
        #print(docs)
        st.session_state.loader = MergedDataLoader(loaders=[pdfloader, htmlloader])
        st.session_state.docs=st.session_state.loader.load() ## doc loading
        ##chunk creation
        st.session_state.text_splitter=RecursiveCharacterTextSplitter(chunk_size=1000,chunk_overlap=200)
        #text splitting
        st.session_state.final_documents=st.session_state.text_splitter.split_documents(st.session_state.docs)
        ##vector store creation
        #st.session_state.vectors=FAISS.from_documents(
       #     st.session_state.final_documents,st.session_state.embeddings)
        st.session_state.vectors=FAISS.from_documents(
            st.session_state.final_documents,embeddings)
      

def vector_embeddings_from_local():
    st.session_state.vectors = FAISS.load_local("faiss_index_hl_shake_recipes",embeddings,allow_dangerous_deserialization=True)

st.write("Loading data ... Please wait...")
vector_embeddings_from_local()
st.write("Loading completed ...")

prompt1=st.text_input("Enter your question from the document")

#if st.button("Documents Embedding"):
#    vector_embeddings_from_local()
#    #vector_embeddings()
#   st.write("Vector Store DB is ready (from local index)"



if prompt1:
    start=time.process_time()
    document_chain = create_stuff_documents_chain(llm, prompt)
    retriever=st.session_state.vectors.as_retriever(max_tokens_limit=10000, top_n=5)
    retrieval_chain=create_retrieval_chain(retriever,document_chain)
    response = retrieval_chain.invoke({'input':prompt1})
    print("Response time :",time.process_time()-start)
    st.write(response['answer'])

    # With a streamlit expander
    with st.expander("Document Similarity Search"):
        # Find the relevant chunks
        for i, doc in enumerate(response["context"]):
            st.write(doc.page_content)
            st.write("--------------------------------")
