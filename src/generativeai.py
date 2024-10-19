import os
import google.generativeai as genai
from dotenv import load_dotenv
import re
import time, threading
from realtime import get_current_weather
from google.generativeai.types.generation_types import StopCandidateException

load_dotenv()

genai.configure(api_key=os.getenv('API_KEY'))

# Global variable for realtime weather data
realtime_data = None  # Initialized as None

# Function to update the weather every minute
def update_weather_data():
    global realtime_data
    while True:
        # Fetch new weather data
        realtime_data = get_current_weather(8.81, 76.75)
        time.sleep(60) 

school_data = {
  "name": "Vimala Central School",
  "place": "Chathannoor",
  "about": """
        Vimala Central School, Karamcodu, Kollam is Situated in the very near outskirt of the city of Kollam by the side of the National High-Way 66. Vimala Central School is celebrating its existence with glorious success. Greenery surroundings and tranquil atmosphere of the village, where the school is situated, enhance the feasibility of deep learning in a meditative mood. Learning here is a celebration; where teachers, students, parents and the society at large are engaged as a team in every step. We feel a harmony with the society and the whole nature. That is why the Celebration in our classrooms and campus becomes the cause of joy for all. Our school provides an ideal atmosphere for nurturing the innate talents and needs of young students.
    """,
    "contact number": '8078378659',
  
}

score_data = {
    "Saint.JOHN'S SCHOOL, ANCHAL": "900 points",
    "SARVODAYA CENTRAL VIDYALAYA, NALANCHIRA, TVM": "769 points",
    "VIMALA CENTRAL SCHOOL, KARAMCODU": "717 points",
    "BROOK INTERNATIONAL SCHOOL, SASTHAMCOTTAH": "699 points",
    "GAYATHRI CENTRAL SCHOOL, KAYAMKULAM": "427 points",
    "VISHWADEEPTHI SCHOOL, KATTAKADA": "366 points",
    "Saint. JUDE SCHOOL, MUKHATHALA, KOLLAM": "318 points",
    "KIPS, KARICKOM": "315 points",
    "HOLY FAMILY PUBLIC SCHOOL, ANCHAL": "253 points",
    "MAR BASELIOS SCHOOL, MARUTHAMONPALLY": "230 points",
    "Saint. ANN'S CENTRAL SCHOOL, AYOOR": "225 points",
    "MARY MATHA CENTRAL SCHOOL, POTHENCODE": "199 points",
    "MAR BASELIOS PUBLIC SCHOOL, KAITHACODU": "162 points",
    "MAR BASELIOS OCEAN STAR CENTRAL SCHOOL": "161 points",
    "CHERUPUSHPA CENTRAL SCHOOL, AYOOR": "117 points",
    "INFANT JESUS CENTRAL SCHOOL, THUVAYOOR": "113 points",
    "CARMELGIRI CENTRAL SCHOOL, BHARATHEEPURAM": "109 points",
    "INFANT JESUS SCHOOL, PONGUMMOODU": "108 points",
    "VIMALA ENGLISH VIDYALAYA, KALATHARA, TVM": "105 points",
    "WOODLEM PARK PUBLIC SCHOOL": "104 points",
    "Saint. GEORGE CENTRAL SCHOOL, AMPALATHUMKALA": "81 points",
    "Saint. JOSEPH'S PUBLIC SCHOOL, CHEMBOOR": "76 points",
    "LOURD MATHA PUBLIC SCHOOL, MEENKULAM": "71 points",
    "NGPM CENTRAL SCHOOL, VENCHEMPU": "58 points",
    "PUSHPAGIRIYIL CENTRAL SCHOOL, EDAMON": "55 points",
    "SHALINI BHAVAN SCHOOL, VEMANAPURAM": "48 points",
    "Saint. MARY'S BETHANY, CENTRAL SCHOOL, VALAKOM": "39 points",
    "MAR BASELIOS E M SCHOOL, KUTTAMALA": "10 points",
    "MYSTICAL ROSE SCHOOL, VETTUCADU": "0 points"
}

generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}

history = []

def get_response(user_input):
    global realtime_data  # Use the latest weather data
    try:
      # Update the system instructions with the latest weather data
      system_instruction = f"""
          Your response should not exceed more than two sentences. Response should be easily understandable without any special characters and emojis, except full stops and commas.
          I am integrating you with a face recognition process, sometimes you will get face names like detected faces - ['name'], that are the person in front of you, talk to them.
          If anyone asks about the weather or current location, here is the data: {realtime_data}. If it's a known person, talk to them like you know them before. {school_data} - Use this data if someone asks about the school, if anyone asked some locations in school you response should begin with code '111', its mandatory.
          your name is sentosa, an AI powered reception assistant, built by vimala central school AI club, powered by Ttttecosa robotics, for helping students. you are at an event called sahodaya competition at this school, where various schools will participate and competete in it. here is the points data, which may change after sometime so if someone asks about score, tell them this as the last score when you checked the program, and answer like predicting the winner or winners. The program is  going to reach the end - {score_data}.
      """

      # Reinitialize the model with the updated system instructions
      model = genai.GenerativeModel(
          model_name="gemini-1.5-flash",
          generation_config=generation_config,
          system_instruction=system_instruction
      )

      print('Generating response...')
  
      chat_session = model.start_chat(history=history)

      response = chat_session.send_message(user_input)

      model_response = response.text
      conversation = re.sub(r'[^\w\s.,]+', '', model_response)
      print(conversation)

      # Update history with the latest conversation
      history.append({"role": "user", "parts": [user_input]})
      history.append({"role": "model", "parts": [model_response]})

      return conversation

    except StopCandidateException as e:
        # Handle the exception gracefully
        print("The response was flagged for safety concerns:", e)
        return "The response was flagged as unsafe. Please try rephrasing your input."

weather_thread = threading.Thread(target=update_weather_data)
weather_thread.daemon = True  
weather_thread.start()

