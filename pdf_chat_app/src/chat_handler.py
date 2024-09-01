from openai import OpenAI
import time

def initialize_thread(pdf_content):
    return [
        {"role": "system", "content": "You are a helpful assistant that answers questions about the following PDF document. Provide accurate and relevant information based on the document's content."},
        {"role": "user", "content": f"Here's the content of the PDF document I want to discuss:\n\n{pdf_content}\n\nPlease help me understand and analyze this document."},
        {"role": "assistant", "content": "Certainly! I've reviewed the content of the PDF document you provided. I'm ready to answer any questions you have about it, provide summaries, or help you analyze specific parts of the document. What would you like to know?"}
    ]

def chat_with_assistant(api_key, messages, user_message):
    client = OpenAI(api_key=api_key)

    # Add the user's message to the conversation
    messages.append({"role": "user", "content": user_message})

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
            max_tokens=300,  # Increased to allow for longer responses
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0,
            response_format={"type": "text"}
        )
        assistant_message = response.choices[0].message.content
        messages.append({"role": "assistant", "content": assistant_message})
        return [(messages[-1]["role"], messages[-1]["content"])]
    except Exception as e:
        return [("assistant", f"An error occurred: {str(e)}")]

def stream_string(s):
    for char in s:
        yield char
        time.sleep(0.02)