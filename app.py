from flask import Flask, render_template, request, jsonify
from gtts import gTTS
import os
import speech_recognition as sr
import wikipedia
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send_message', methods=['POST'])
def send_message():
    user_input_text = request.form['user_input']
    response = get_response(user_input_text)
    speak(response)
    return jsonify({'response': response})

@app.route('/voice_input', methods=['POST'])
def voice_input():
    response = voice_input_processing()
    return jsonify({'response': response})

def voice_input_processing():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
    
    try:
        user_input_text = recognizer.recognize_google(audio)
        print("You said:", user_input_text)
        response = get_response(user_input_text)
        speak(response)
        return response
    except sr.UnknownValueError:
        print("Sorry, I could not understand what you said.")
        return "Sorry, I could not understand what you said."
    except sr.RequestError as e:
        print("Could not request results from Google Speech Recognition service; {0}".format(e))
        return "Could not request results from speech recognition service."

def speak(text):
    tts = gTTS(text=text, lang='en')
    tts.save("output.mp3")
    os.system("start output.mp3")

def get_response(user_input_text):
    try:
        if user_input_text.lower().startswith("tell me about"):
            topic = user_input_text[13:].strip()  # Extract the topic from the input
            return get_wikipedia_info(topic)
        elif "news" in user_input_text.lower():
            return get_latest_news()
        elif "search on facebook" in user_input_text.lower():
            name = user_input_text[18:].strip()
            return search_facebook_profiles(name)
        else:
            return "I'm still learning! Ask me anything else."
    except Exception as e:
        print(e)
        return "Oops! Something went wrong. Please try again."

def get_wikipedia_info(topic):
    try:
        summary = wikipedia.summary(topic, sentences=2)
        return summary
    except wikipedia.exceptions.DisambiguationError as e:
        options = e.options[:3]  # Get the first three options
        return f"Multiple options found for {topic}. Did you mean: {', '.join(options)}?"
    except wikipedia.exceptions.PageError:
        return f"Sorry, I couldn't find any information about {topic}."

def get_latest_news():
    try:
        # Example: fetching latest news from News API (you'll need an API key)
        api_key = 'YOUR_NEWS_API_KEY'
        url = f'https://newsapi.org/v2/top-headlines?country=us&apiKey={api_key}'
        response = requests.get(url)
        data = response.json()
        if 'articles' in data:
            headlines = [article['title'] for article in data['articles']]
            return "\n".join(headlines[:5])  # Return top 5 headlines
        else:
            return "Sorry, I couldn't fetch the latest news at the moment."
    except Exception as e:
        print(e)
        return "Sorry, I encountered an error while fetching the latest news."

def search_facebook_profiles(name):
    search_url = f"https://www.facebook.com/public/{name}"
    response = requests.get(search_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        profile_results = soup.find_all("div", class_="_32mo")
        if profile_results:
            profiles = []
            for result in profile_results:
                profile_name = result.find("div", class_="_32mq").text
                profile_link = result.find("a", class_="_32mo")["href"]
                profiles.append({"name": profile_name, "profile_link": profile_link})
            return "\n".join([f"Name: {profile['name']}, Profile Link: {profile['profile_link']}" for profile in profiles])
        else:
            return "No public profiles found for this name."
    else:
        return "Error: Failed to fetch search results from Facebook."

if __name__ == '__main__':
    app.run(debug=True)
