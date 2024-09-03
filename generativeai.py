import os
import google.generativeai as genai
from dotenv import load_dotenv
import re

load_dotenv()

genai.configure(api_key=os.getenv('API_KEY'))

school_data ={
  "name": "Nirmala Bhavan Higher Secondary School",
  "place": "Trivandrum",
  "about": "Nirmala Bhavan Higher Secondary School, founded in 1964, is a girls school run by the Sisters of the Adoration of the Blessed Sacrament. This religious congregation was founded in 1908 by the first Bishop of Changanacherry, Mar Thomas Kurialachery."
}
generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
  model_name="gemini-1.5-flash",
  generation_config=generation_config,
  system_instruction=f"your response should be short and easy to understand without any special characters or emoji's. if user asks  about any school talk only about this school - {school_data} otherwise talk  accordingly, if the user asks to activate any mode, tell them to stop chat mode first. Your name is Tesa.If some one asks who are you,then tell them your name is Tesa",
)

history = []


def get_response(user_input):

    print('generating response...')
 
    chat_session = model.start_chat(
        history=history
    )

    response = chat_session.send_message(user_input)

    model_response = response.text
    conversation = re.sub(r'[^\w\s.,.]+', '', model_response)
    print(conversation)

    history.append({"role": "user", "parts": [user_input]})
    history.append({"role": "model", "parts": [model_response]})

    return conversation