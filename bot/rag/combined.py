from langchain_community.embeddings import GPT4AllEmbeddings
from langchain_community.llms.bedrock import Bedrock
from langchain_community.chat_models import BedrockChat
from langchain.chains import RetrievalQA
from langchain_community.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.prompts import PromptTemplate
import asyncio
import logging

logger = logging.getLogger(__name__)
import boto3
import io
import fitz
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import GPT4AllEmbeddings
from langchain.vectorstores import Chroma

async def create_rag_model(s3_bucket, s3_key):
    try:
        s3 = boto3.client('s3')
        pdf_obj = s3.get_object(Bucket=s3_bucket, Key=s3_key)
        pdf_content = pdf_obj['Body'].read()
        pdf_stream = io.BytesIO(pdf_content)
        doc = fitz.open(stream=pdf_stream, filetype="pdf")
        data = []
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            page_text = page.get_text()
            metadata = {"source": f"s3://{s3_bucket}/{s3_key}", "page": page_num + 1}
            data.append(Document(page_content=page_text, metadata=metadata))

        logger.info(f"Loaded data from s3://{s3_bucket}/{s3_key}")

    except Exception as e:
        logger.error(f"Error loading s3://{s3_bucket}/{s3_key}: {e}")
        return None

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=3500,
        chunk_overlap=500,
        separators=["\n\n", "\n", " ", ""]
    )
    all_splits = text_splitter.split_documents(data)
    logger.info(f"Total chunks created for s3://{s3_bucket}/{s3_key}: {len(all_splits)}")
    embeddings = GPT4AllEmbeddings()
    vectorstore = Chroma.from_documents(documents=all_splits, embedding=embeddings)
    logger.info(f"Vector store created with embeddings for s3://{s3_bucket}/{s3_key}.")

    return vectorstore


async def run_retrieval_qa(llm, retriever, prompt, context_message):
    chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        verbose=False,
        chain_type_kwargs={"prompt": prompt}
    )
    try:
        result = await chain.ainvoke(context_message)
        return result
    except Exception as e:
        logger.error(f"Error during RetrievalQA chain invocation: {e}")
        return ""

async def model_call(vectorstore, temp, msg):
    prompt = PromptTemplate(template=temp, input_variables=["context"])
    model_kwargs =  { 
    "max_tokens": 2048,
    "temperature": 0.0,
    "top_k": 250,
    "top_p": 1,
    }
    llm = BedrockChat(
        model_id="anthropic.claude-3-sonnet-20240229-v1:0",
        region_name="us-west-2",
        model_kwargs=model_kwargs,
        callback_manager=CallbackManager([StreamingStdOutCallbackHandler()]),
        streaming=True,
    )

    if vectorstore is not None:
        retriever = vectorstore.as_retriever(search_kwargs={"k": 50})
        data = await run_retrieval_qa(llm, retriever, prompt,msg)
        return data.get("result")
    
    return "========Model failed======"

