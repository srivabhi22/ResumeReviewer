import os
import re
import logging
import json
from typing import Optional, Tuple, List
from pathlib import Path
from PyPDF2 import PdfReader
from langchain.chains.summarize import load_summarize_chain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from langchain.prompts import PromptTemplate
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from dotenv import load_dotenv
import yaml
from langchain_google_genai import ChatGoogleGenerativeAI


load_dotenv()

def load_prompts():
    filepath = os.path.join(os.path.dirname(__file__), "prompts.yaml")
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        print(f"Error: The file '{filepath}' was not found.")
        return None
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")
        return None
    
class ResumeParserConfig:
    """Configuration class for ResumeParser."""
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

    RESUME_SUMMARY_FILE_PATH = os.path.join(CURRENT_DIR, "resume_summary.txt")
    RESUME_SKILLS_FILE_PATH = os.path.join(CURRENT_DIR, "resume_skills.txt")
    MISSING_SKILLS_FILE_PATH = os.path.join(CURRENT_DIR, "missing_skills.txt")
    JOB_SKILLS_FILE_PATH = os.path.join(CURRENT_DIR, "job_skills.txt")
    RESUME_REWRITTEN_FILE_PATH = os.path.join(CURRENT_DIR, "resume_rewritten.txt")
    ATS_OPTIMIZED_BULLETS_FILE_PATH = os.path.join(CURRENT_DIR, "ats_optimized_bullets.txt")
    RESUME_TEXT = os.path.join(CURRENT_DIR, "resume_text.txt")
    
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    GEMINI_MODEL = "gemini-2.5-pro"
   
class ResumeParserError(Exception):
    """Custom exception for ResumeParser errors."""
    pass

class ResumeParser:
    """A class to parse and analyze resumes using LLMs."""
    
    def __init__(self):
        """Initialize the ResumeParser with Groq API key."""
        gemini_api_key = os.getenv("GOOGLE_API_KEY")
        self.llm = ChatGoogleGenerativeAI(model=ResumeParserConfig.GEMINI_MODEL, 
                                          google_api_key=gemini_api_key, 
                                          temperature=0.2)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=ResumeParserConfig.CHUNK_SIZE,
            chunk_overlap=ResumeParserConfig.CHUNK_OVERLAP,
            separators=["\n\n", "\n", " ", ""]
        )
        self.output_parser = StructuredOutputParser.from_response_schemas([
            ResponseSchema(name="Technical skills", description="List of technical skills mentioned."),
            ResponseSchema(name="Soft skills", description="List of soft skills mentioned."),
            ResponseSchema(name="Academic qualifications", description="List of academic qualifications mentioned.")
        ])
        self._setup_prompts()

    def _setup_prompts(self):
        """Set up prompt templates for resume and job analysis."""
        prompts = load_prompts()
        self.resume_prompt = PromptTemplate(
            input_variables=["text"],
            template=prompts['resume_summary_generator']
        )

        self.credentials_prompt = PromptTemplate(
            input_variables=["resume_content"],
            template=prompts['resume_skill_extractor']
            # output_parser=self.output_parser
        )

        self.missing_skills_prompt = PromptTemplate(
                input_variables=["job_description", "resume_content"],
                template=prompts['job_resume_comparison']
            # output_parser=self.output_parser
        )

        self.job_prompt = PromptTemplate(
            input_variables=["job_description"],
            template=prompts['job_description_skill_extractor']
            # output_parser=self.output_parser
        )

        self.ats_bullet_prompt = PromptTemplate(
            input_variables=["job_description", "resume_content"],
            template=prompts['resume_ats_optimizer']
        )

    @staticmethod
    def extract_text_from_resume(file_path: str) -> Optional[str]:
        """Extract text from a PDF resume."""
        try:
            with open(file_path, 'rb') as file:
                reader = PdfReader(file)
                text = "".join(page.extract_text() for page in reader.pages)
            return text
        except FileNotFoundError:
            raise ResumeParserError(f"Resume file not found: {file_path}")
        except Exception as e:
            raise ResumeParserError(f"Error during PDF processing: {e}")

    @staticmethod
    def save_text_to_file(file_path: str, text_content: str) -> None:
        """Save text content to a file."""
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(text_content)
        except Exception as e:
            raise ResumeParserError(f"Error saving text to {file_path}: {e}")

    @staticmethod
    def extract_dictionary_from_llm_output(text: str) -> str:
        """Extract and validate a dictionary string from LLM output.

        Args:
            text (str): Raw LLM output containing a dictionary.

        Returns:
            str: Cleaned dictionary string or empty string if invalid.
        """
        try:
            # Find the first '{' and the last matching '}'
            start_idx = text.find('{')
            if start_idx == -1:
                return "{}"

            # Track brace count to find matching closing brace
            brace_count = 0
            end_idx = start_idx
            for i, char in enumerate(text[start_idx:]):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = start_idx + i + 1
                        break
            else:
                return "{}"

            # Extract dictionary string
            dict_str = text[start_idx:end_idx].strip()

            # Clean the string (remove backslashes, newlines, etc.)
            dict_str = dict_str.replace('\\', '').replace('\n', ' ').replace('\r', '')

            # Validate dictionary using json.loads
            json.loads(dict_str)

            return dict_str
        except json.JSONDecodeError as e:
            return "{}"
        except Exception as e:
            return "{}"

    def preprocess_resume(self, resume_path: str) -> List[Document]:
        """Preprocess resume by extracting and splitting text into chunks."""
        if not os.path.exists(resume_path):
            raise ResumeParserError(f"Resume file not found: {resume_path}")

        text = self.extract_text_from_resume(resume_path)
        if not text:
            raise ResumeParserError("Failed to extract text from resume.")

        texts = self.text_splitter.split_text(text)
        resume_content = [Document(page_content=t) for t in texts]
        return resume_content


    def parse_resume(self, resume_path: str, job_description: str) -> Tuple[str, str, str, str]:
        """Parse resume and return summary, credentials, missing skills, and job skills."""
        
        # Preprocess resume
        resume_content = self.preprocess_resume(resume_path)
        resume_text = " ".join(doc.page_content for doc in resume_content)
        self.save_text_to_file(ResumeParserConfig.RESUME_TEXT, resume_text)

        # Generate summary
        try:
            chain = load_summarize_chain(
                llm=self.llm,
                chain_type="stuff",
                prompt=self.resume_prompt,
                verbose=False
            )
            summary = chain.invoke({"input_documents": resume_content})
            summary_text = summary['output_text']
            summary_text = re.sub(r"^```json|```$", "", summary_text.strip()).strip()
            self.save_text_to_file(ResumeParserConfig.RESUME_SUMMARY_FILE_PATH, summary_text)
        except Exception as e:
            summary_text = "Error during summarization."
            self.save_text_to_file(ResumeParserConfig.RESUME_SUMMARY_FILE_PATH, summary_text)

        # Extract credentials
        try:
            llm_chain = self.credentials_prompt | self.llm
            credentials_response = llm_chain.invoke({"resume_content": resume_text}).content
            credentials_response = re.sub(r"^```json|```$", "", credentials_response.strip()).strip()
            # credentials_response = self.extract_dictionary_from_llm_output(credentials_response)
            self.save_text_to_file(ResumeParserConfig.RESUME_SKILLS_FILE_PATH, credentials_response)
        except Exception as e:
            credentials_response = "Error extracting credentials."
            self.save_text_to_file(ResumeParserConfig.RESUME_SKILLS_FILE_PATH, credentials_response)

        # Generate job-specific analysis
        try:
            job_llm_chain = self.job_prompt | self.llm
            job_response = job_llm_chain.invoke({"job_description": job_description}).content
            job_response = re.sub(r"^```json|```$", "", job_response.strip()).strip()

            missing_skill_llm_chain = self.missing_skills_prompt | self.llm
            missing_skills_response = missing_skill_llm_chain.invoke({
                "job_description": job_response,
                "resume_content": credentials_response
            }).content
            missing_skills_response = re.sub(r"^```json|```$", "", missing_skills_response.strip()).strip()
            # missing_skills_response = self.extract_dictionary_from_llm_output(missing_skills_response)
            # job_response = self.extract_dictionary_from_llm_output(job_response)
            self.save_text_to_file(ResumeParserConfig.MISSING_SKILLS_FILE_PATH, missing_skills_response)
            self.save_text_to_file(ResumeParserConfig.JOB_SKILLS_FILE_PATH, job_response)
        except Exception as e:
            missing_skills_response = "Error generating missing skills."
            job_response = "Error generating job skills."
            self.save_text_to_file(ResumeParserConfig.MISSING_SKILLS_FILE_PATH, missing_skills_response)
            self.save_text_to_file(ResumeParserConfig.JOB_SKILLS_FILE_PATH, job_response)

        # Rewrite resume bullets for ATS
        ats_chain = self.ats_bullet_prompt | self.llm
        improved_response = ats_chain.invoke({
                "job_description": job_description,
                "resume_content": resume_text
            }).content

        improved_response = re.sub(r"^```json|```$", "", improved_response.strip()).strip()
        # Save improved bullets to file
        self.save_text_to_file(ResumeParserConfig.ATS_OPTIMIZED_BULLETS_FILE_PATH, improved_response)

        return summary_text, credentials_response, missing_skills_response, job_response, improved_response


job_description = """Tower Research Capital is a leading quantitative trading firm founded in 1998. Tower has built its business on a high-performance platform and independent trading teams. We have a 25+ year track record of innovation and a reputation for discovering unique market opportunities.

Tower is home to some of the world’s best systematic trading and engineering talent. We empower portfolio managers to build their teams and strategies independently while providing the economies of scale that come from a large, global organization.

Engineers thrive at Tower while developing electronic trading infrastructure at a world class level. Our engineers solve challenging problems in the realms of low-latency programming, FPGA technology, hardware acceleration and machine learning. Our ongoing investment in top engineering talent and technology ensures our platform remains unmatched in terms of functionality, scalability and performance.

At Tower, every employee plays a role in our success. Our Business Support teams are essential to building and maintaining the platform that powers everything we do — combining market access, data, compute, and research infrastructure with risk management, compliance, and a full suite of business services. Our Business Support teams enable our trading and engineering teams to perform at their best.

At Tower, employees will find a stimulating, results-oriented environment where highly intelligent and motivated colleagues inspire each other to reach their greatest potential.

Responsibilities:

Developing data pipelines for cleaning, collecting, processing, and analyzing diverse datasets.
Designing and implement machine learning and LLM-based NLP models.
Conducting experiments and tests to evaluate model performance.
Contributing to optimizing and fine-tuning existing machine learning models.

Qualifications:

A bachelor’s, master's, or PhD (ongoing or complete) degree or equivalent from a top university, available to join for an in-office 6 month Internship starting Jan 2025/Feb 2025.
Prior experience with training, building, and deploying models via Tensorflow/Pytorch (or similar) is mandatory.
Experience with CI/CD pipelines and MLOps for automating model deployments.
Skilled in using Linux, SQL, Git, and BASH scripting.
Strong knowledge of Python and hands-on."""
