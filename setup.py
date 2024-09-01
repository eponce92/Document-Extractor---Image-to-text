from setuptools import setup, find_packages

setup(
    name="pdf_chat_app",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'streamlit',
        'pymupdf4llm',
        'openai',
        'python-dotenv',  # if you decide to use environment variables
    ],
)