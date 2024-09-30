import os
import google.generativeai as genai
from dotenv import load_dotenv
import re

load_dotenv()

genai.configure(api_key=os.getenv('API_KEY'))

school_data ={
  "name": "CHINMAYA",
  "place": "Kollam",
   "about": """
        The education imparted in the Vidyalaya(means school) fulfills Pujya Gurudev Swami Chinmayananda’s Vision of Education. It enables all Chinmaya kids to bloom with bright hues and spread the fragrance. The presence of Chinmaya Mission Acharya and the Ashram give the Vidyalaya a spiritual ambience. The holy shrine of the Lord Ganesha gives the Vidyalaya a peaceful environment. Chinmaya Blossom, the play school is a feather in the cap of the Vidyalaya. The school is affiliated upto classes XII.
        The Vidyalaya is equipped with the latest technology – hybrid teaching and learning and smart classrooms. Values are inculcated in the young minds with the text “Life, An Aradhana” and Chinmaya Vision Programme. The Vidyalaya curriculum includes the enrichment of communication and language skills, Yoga and co curricular activities.
        The Vidyalaya was a long pending dream of the people of Kollam. It was first established on 23rd Oct 1985 at Manayilkulangara, Kollam. The Vidyalaya attained its gradual growth and classes upto VII started functioning was shifted to its new location at Chandanathope in 1996 under the leadership of Chinmaya Educational Trust, Thiruvananthapuram.
    """,
    "locations": {
        "current location":"always outside first entrance door",
        "second entrance": "go straight from first entrance",
        "MD's cabin": "left to first entrance door",
        "Media department": "left to second entrance door",
        "toilet": "left side of media department.",
        "work desk": "straight from second entrance and turn left.",
        "Technical department": "left to the work desk."
    }
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
  system_instruction=f"""
    Your response should be short(mandatory except Locations) and easy to understand with proper punctuations avoiding emojis, astricks, and exclamations.
    If the user asks about any institutions, talk about this Institution - {school_data['name']}.
    The institution details are as follows:
    Name: {school_data['name']}
    Place: {school_data['place']}
    About: {school_data['about']}
    Locations: {school_data['locations']}
    analyze and fetch only directions(left, right, etc..) from Locations not landmarks and provide in detail to the user
    Otherwise, respond accordingly.
    If the user asks to activate any mode, tell them to stop chat mode first.
    Your name is Samartha.
    If someone asks what your name is, then tell them your name is Samartha and you are made for interacting with students, analysing there emotions and assisting them.
    your creator is Ttttecosa  solutions.
  """
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