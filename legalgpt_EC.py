from langchain_groq import ChatGroq
from langchain.schema import Document
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.retrievers import BM25Retriever, EnsembleRetriever
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from FlagEmbedding import FlagReranker
from dotenv import load_dotenv
import os, sys, re, tempfile
import pymupdf4llm, pymupdf
import streamlit as st
import warnings
warnings.filterwarnings('ignore')

load_dotenv()

path = r"C:\Users\siva3\OneDrive\Documents\Naveen Kumar's Files\VSCode_Stuffs\LegalGPT\EC_Documents"
sys.path.append(path)

groq_api_key = st.secrets["general"]["GROQ_API_KEY"]
model = ChatGroq(groq_api_key=groq_api_key, model_name="llama-3.1-70b-versatile", temperature=0) # llama-3.3-70b-versatile | llama-3.1-8b-instant
embeddings = SentenceTransformerEmbeddings(model_name='all-MiniLM-L6-v2') # ai4bharat/indic-bert | all-mpnet-base-v1
reranker = FlagReranker('BAAI/bge-reranker-base', use_fp16=False) # Re-ranker model

# * -------------------------------------- PDF Extraction --------------------------------------

def adjust_bbox(bbox, page_rect, increment=50):
    x0, y0, x1, y1 = bbox
    y0 = max(y0 - increment, 0)  # Expand upwards without going negative
    y1 = min(y1 + increment, page_rect.height)  # Expand downwards
    return (x0, y0, x1, y1)

def pdf_extraction(pdf_path): # For table extraction alone!
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file: # Create a temporary file to store the uploaded PDF
        temp_file.write(pdf_path.getvalue())  # Write file content to temp storage
        temp_file_path = temp_file.name  # Get file path
    
    doc = pymupdf.open(temp_file_path) # Open the PDF using pymupdf with a stream
    output = pymupdf4llm.to_markdown(temp_file_path, page_chunks=True) # Process for tables
    
    content = []

    for page_number in range(len(output)):
        page = doc.load_page(page_number)
        page_rect = page.rect
        
        for table_info in output[page_number]['tables']:
            bbox = table_info['bbox']
            increment = 100
            adjusted_bbox = adjust_bbox(bbox, page_rect, increment)
            expanded_table_text = page.get_text("text", clip=adjusted_bbox)

            lines = expanded_table_text.split('\n')
            texts = ' '.join(line.replace('  ','').strip() for line in lines if line)
            content.append(texts)
            
    return content

# * -------------------------------------- Chunking & Retrieving Process --------------------------------------

def retrieving_process(content, query):
    documents = [Document(page_content=text, metadata={"source": f"chunk {i+1}"}) for i, text in enumerate(content)]
    bm25_retriever = BM25Retriever.from_documents(documents)

    vector_store = FAISS.from_documents(documents, embeddings)
    vector_retriever = vector_store.as_retriever()

    ensemble_retriever = EnsembleRetriever(retrievers=[bm25_retriever, vector_retriever], weights=[0.5, 0.5])
    retrieved_chunks = ensemble_retriever.get_relevant_documents(query)[:7] # TODO: Check the retrieved_chunks length!

    return retrieved_chunks

# * -------------------------------------- Re-ranking Process --------------------------------------

def rerank_documents(retrieved_docs, query):
    input_pairs = [[query, doc.page_content] for doc in retrieved_docs]
    scores = reranker.compute_score(input_pairs)

    for doc, score in zip(retrieved_docs, scores):
        doc.metadata["rerank_score"] = score

    reranked_docs = sorted(retrieved_docs, key=lambda x: x.metadata["rerank_score"], reverse=True)
    return reranked_docs[:3]

# * -------------------------------------- Meta Details Extracion --------------------------------------

def extract_meta_details(context):
    """ Extracting the meta details from the context! """
    meta_details_prompt = PromptTemplate(
        input_variables=["context"],
        template="""
        You are provided with a document. Extract the following details:
        1. Property Value (Mentioned Market Value)
        2. Current Owner (Last mentioned person name or bank name of this property)
        3. Property Location (Address Details)
        4. Last Property Type
        5. Last Property Extent

        Document Text:
        {context}

        Extract the details and return them in a dictionary format like:
        {{
            "Property Value": <value>,
            "Current Owner": <value>,
            "Property Location": <value>,
            "Last Property Type": <value>,
            "Last Property Extent": <value>
        }}
        
        IMPORTANT:
        - Providing responses strictly in Tamil.
        - Return ONLY the JSON output
        - Do NOT include explanatory text
        - Do NOT skip any fields
        - Do NOT hallucinate values
        - If information is not found, use empty string ('')
        - Maintain exact format shown above
        """
    )

    formatted_prompt = meta_details_prompt.format(context=context)
    response = model.invoke(formatted_prompt)
    extracted_details = response.content  # Assuming the LLM returns the details in a dictionary-like format
    print(extracted_details)
    
    return extracted_details

# * -------------------------------------- ChatBot Setup: EC_ChatBot --------------------------------------

def EC_ChatBot(reranked_docs, user_query): # model
    retriever = FAISS.from_documents(reranked_docs, embeddings).as_retriever()
    
    prompt_template = ChatPromptTemplate.from_template("""
    You are an AI assistant specialized in answering user queries based on the content of Encumbrance Certificate (EC) documents.

    Your responsibilities include:
    1. Providing responses strictly in Tamil.
    2. Giving concise, straight-to-the-point answers without unnecessary explanations.
    3. Maintaining an interactive and human-friendly tone in your responses.
    4. Ensuring your responses are accurate and do not contain hallucinated or made-up information.

    Always rely on the provided context from the EC document to form your answers. If the information is not available in the context, clearly state that you cannot provide an answer.

    Below is the relevant context extracted from the Encumbrance Certificate (EC) document:
    {context}

    User Query:
    {user_query}

    Provide your response based on the context above. If the query cannot be answered from the context, clearly state that the information is not available in the document.
    
    Answer:
    """)

    chat_chain = (
    {
        "context": retriever,
        "user_query": RunnablePassthrough()
    }
    | prompt_template
    | model
    | StrOutputParser()
)
    
    return chat_chain.invoke(user_query)

# * -------------------------------------- Document Remarks Extraction --------------------------------------

def extract_all_document_remarks(extracted_text):
    start_keywords = [r"Document Remarks/ ஆவணக் குறிப்புகள் :", r"Document Remarks", r"ஆவணக் குறிப்புகள்"]
    stop_keyword = r"அட்டவணை \d+"
    
    extracted_results = []

    for element in extracted_text:
        start_pattern = r"|".join(start_keywords)
        
        start_matches = list(re.finditer(start_pattern, element))
        
        if start_matches:
            for match in start_matches:
                start_position = match.start()
                sliced_content = element[start_position:]
                
                stop_match = re.search(stop_keyword, sliced_content)
                if stop_match:
                    end_position = stop_match.start()
                    extracted_results.append(sliced_content[:end_position].strip())
                else:
                    extracted_results.append(sliced_content.strip())

    return extracted_results

# * -------------------------------------- Summarization Setup: EC_Summarization --------------------------------------

def EC_Summarization(extracted_text):
    context = "\n".join([doc.strip() for doc in extracted_text])
    
    summarization_prompt = ChatPromptTemplate.from_template("""
    You are an an expert in summarizing Encumbrance Certificate (EC) documents. Provide a concise summary of the document.
    Your responsibilities include:
    1. Extracting key details like property registration numbers, owner names, transaction history, and other essential information.
    2. Providing a concise summary strictly in Tamil.
    3. Avoiding unnecessary explanations and hallucinated information.

    Context:
    {context}

    Based on the context above, extract and summarize key details such as:
    - பதிவு எண் (Registration Number)
    - உரிமையாளர் பெயர் (Owner Name)
    - நில விவரங்கள் (Land Details)
    - பரிமாற்ற விவரங்கள் (Transaction Details)
    - வரம்புகள் (Boundaries)

    If specific details are not present, indicate that they are unavailable. Provide your response in Tamil.
    Answer:
    """)

    summarize_doc = summarization_prompt.format(context=context)
    
    try:
        response = model.invoke(summarize_doc)
        summarized_content = response.content.strip()
    except Exception as e:
        summarized_content = f"சுருக்கத்திற்கு தேவைப்படும் தகவலை பெற முடியவில்லை. பிழை: {str(e)}"

    return summarized_content

# * -------------------------------------- User Query Refinement (Not In Use) --------------------------------------

refinement_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a query refinement assistant. Improve the user query based on the given task instructions and make it specific and suitable for document retrieval."),
    ("user", "{instructions}"),
    ("user", "{query}"),
    ("assistant", "Refined Query:")])

def refine_query(instructions, query):
    # Refine the query using LLM
    refined_query = model.invoke(refinement_prompt.format(instructions=instructions, query=query))
    return refined_query.content.strip()

# * -------------------------------------- Main Program Starts Here! --------------------------------------

def main(pdf_path, user_query):
    extracted_text = pdf_extraction(pdf_path)
    retrieved_chunks = retrieving_process(extracted_text, user_query)
    reranked_docs = rerank_documents(retrieved_chunks, user_query)
    
    # ChatBot Response
    chatbot_response = EC_ChatBot(reranked_docs, user_query) # model
    if chatbot_response:
        print(chatbot_response)
        
    summarization_response = EC_Summarization(extracted_text)
    if summarization_response:
        print(summarization_response)

    # Document Remarks Extraction
    result = extract_all_document_remarks(extracted_text)
    if result:
        print("Extracted Content:")
        for res in result:
            print(res)
    else:
        print("No matching content found.")


if __name__ == "__main__":
    user_query = "Who is the current claimant of this property?"
    pdf_path = os.path.join(path, "APP_8400001_TXN_397484843_TMPLT_8400004.pdf")
    main(pdf_path, user_query)
    

# *** Queries: ***
"""
What is the value of the land property?
Who is the current owner of this property?
What is the latest Document Remarks and the Schedule Remarks status of this property?
Is there any disputes in this property?
What is the property value mentioned in this EC document?
"""

# meta_query = """
#     From the last section of the document, please extract the following details:
#     Property Value (Mentioned Market Value)
#     Current Owner (Who is the current owner of the property)
#     Property Location (Address)
#     Last Property Type
#     Last Property Extent
# """
