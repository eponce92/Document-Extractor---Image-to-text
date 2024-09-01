import base64
from openai import OpenAI
import logging
import pymupdf4llm
import openai

class PDFConverter:
    def __init__(self, api_key, model="gpt-4o-mini"):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def describe_image_and_context(self, image_path, context_before, context_after, user_prompt):
        try:
            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')

            prompt = f"""
            You are an AI assistant helping to convert documents with images into accessible text formats. 
            Your task is to describe an image in detail, considering its context within the document.

            Document Context:
            1. Text before the image:
            {context_before}

            2. Text after the image:
            {context_after}

            User-provided context and preferences:
            {user_prompt}

            Instructions:
            1. Analyze the image carefully, considering all visual elements.
            2. Provide a detailed description of the image that would be meaningful to someone who cannot see it.
            3. Relate the image content to the surrounding text context where relevant.
            4. Consider the user-provided context and preferences when describing the image.
            5. Structure your description as follows:
            a. Brief overview 
            b. Detailed description 
            c. Relevance to document context 
            6. Use clear, concise language and avoid making assumptions about information not present in the image or context.
            7. If the image contains text, include it verbatim in your description.
            8. For diagrams, charts, or graphs, explain their type and the information they convey, including any relevant numbers or key data points.
            9. Describe colors, shapes, spatial relationships, and any other visually significant elements.

            Your description should enable a person who cannot see the image to understand its content and significance within the document.
            """

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_data}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500
            )
            return response.choices[0].message.content
        except openai.error.APIError as e:
            logging.error(f"OpenAI API error: {e}")
            return f"Error in image description: OpenAI API error occurred"
        except openai.error.RateLimitError as e:
            logging.error(f"OpenAI rate limit error: {e}")
            return f"Error in image description: Rate limit exceeded"
        except Exception as e:
            logging.error(f"Unexpected error in image description: {e}")
            return f"Error in image description: An unexpected error occurred"