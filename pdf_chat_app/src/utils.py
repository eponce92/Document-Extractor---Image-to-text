from openai import OpenAI

def get_model_options(api_key):
    client = OpenAI(api_key=api_key)
    models = client.models.list()
    return [model.id for model in models.data]