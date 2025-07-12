import os
from langchain_groq import ChatGroq

# Load API key and initialize the LLM
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
llm = ChatGroq(groq_api_key=GROQ_API_KEY, model="llama3-8b-8192")

def clean_text(text):
    """
    Clean the input text by removing extra spaces, special characters, and newlines.
    """
    import re
    text = re.sub(r'\n+', ' ', text)  # Remove multiple newlines
    text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with a single space
    text = re.sub(r'[^A-Za-z0-9,.;:()\'"\s-]', '', text)  # Remove special characters
    return text.strip()

# Sample resume summary and job description
resume_summary = """
Highly skilled Data Scientist with a strong academic background in Data Science and Statistics, 
and extensive experience in using data insights to drive business growth. Proficient in a range 
of programming languages, including R, Python, and SQL, as well as data visualization tools like 
Tableau and Git. Proven ability to design and implement ETL pipelines, automate data extraction 
and processing, and create interactive data visualizations.
"""

job_description = """
We are a Japanese medical device manufacturing company looking for AI professionals to join 
our Life Science team. Responsibilities include solving time series, RNA sequencing, and 
computer vision problems using machine learning and deep learning techniques. Required 
skills include Python, C++, Pandas, Pytorch, and Tensorflow.
"""

# Clean the resume summary and job description
clean_text_data = clean_text(resume_summary)
clean_job_description = clean_text(job_description)

# Initial prompt to analyze the resume and JD and start the conversation
init_prompt = f"""
You are an AI interviewer. You have been given the following resume summary and job description. 
First, analyze the resume and the job description. Then, start a conversation by asking a 
relevant question based on the resume and job description. Continue the conversation based on the user's responses.

Resume Summary: {clean_text_data}
Job Description: {clean_job_description}
AI:
"""

# Get the initial response to start the conversation
print("\n--- Chat with the LLM ---")
response = llm.invoke(init_prompt)
print("AI:", response.content)

# Start the interactive chat loop
while True:
    user_input = input("You: ")
    if user_input.lower() in ['exit', 'quit']:
        print("Goodbye!")
        break
    
    # Dynamic prompt construction
    prompt = f"""
    Resume Summary: {clean_text_data}
    Job Description: {clean_job_description}
    AI's Previous Question: {response.content}
    User's Answer: {user_input}
    AI: Continue the conversation by providing feedback and asking the next relevant question.
    """
    
    # Invoke the LLM with the dynamic prompt
    response = llm.invoke(prompt)
    print("AI:", response.content)
