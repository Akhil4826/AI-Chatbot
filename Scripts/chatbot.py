import sys
import tkinter as tk
from tkinter import scrolledtext
import random
import json
import pickle
import numpy as np
import nltk
from nltk.stem import WordNetLemmatizer
from keras.models import load_model
import googleapiclient.discovery
import requests
from bs4 import BeautifulSoup
import webbrowser
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, Qt

# Load necessary files and models
lemmatizer = WordNetLemmatizer()
intents = json.loads(open('C:/Users/akhil/Downloads/chatbot/chatbot/intents.json').read())
words = pickle.load(open('words.pkl', 'rb'))
classes = pickle.load(open('classes.pkl', 'rb'))
model = load_model('chatbot_model.h5')

# Google Search API credentials
API_KEY = 'AIzaSyBHDVJGb5HyqKHOZN1o-i1bMOHcvD8tjzA'
CX = '96aeb9f902afd45aa'

# Initialize Google API client
service = googleapiclient.discovery.build('customsearch', 'v1', developerKey=API_KEY)

def clean_up_sentence(sentence):
    sentence_words = nltk.word_tokenize(sentence)
    sentence_words = [lemmatizer.lemmatize(word.lower()) for word in sentence_words]
    return sentence_words

def bag_of_words(sentence):
    sentence_words = clean_up_sentence(sentence)
    bag = [0] * len(words)
    for w in sentence_words:
        for i, word in enumerate(words):
            if word == w:
                bag[i] = 1
    return np.array(bag)

def predict_class(sentence):
    bow = bag_of_words(sentence)
    res = model.predict(np.array([bow]))[0]
    ERROR_THRESHOLD = 0.25
    results = [[i, r] for i, r in enumerate(res) if r > ERROR_THRESHOLD]
    results.sort(key=lambda x: x[1], reverse=True)
    return_list = []
    for r in results:
        return_list.append({'intent': classes[r[0]], 'probability': str(r[1])})
    return return_list

def get_response(intents_list, intents_json):
    if not intents_list:
        return "I don't have a response for that."
    tag = intents_list[0]['intent']
    list_of_intents = intents_json['intents']
    for i in list_of_intents:
        if i['tag'] == tag:
            return random.choice(i['responses'])
    return "I don't have a response for that."

def fetch_google_answer(query):
    try:
        result = service.cse().list(
            q=query,
            cx=CX,
            num=5,
        ).execute()

        responses = []
        video_links = []
        if 'items' in result:
            for item in result['items']:
                snippet = item.get('snippet', '')
                link = item.get('link', '')
                if 'youtube.com/watch' in link:
                    video_links.append(link)
                if snippet:
                    responses.append(f"{snippet} ({link})")

        response_text = '\n\n'.join(responses)
        if video_links:
            response_text += '\n\nVideo Links:\n' + '\n'.join(f'{link}' for link in video_links)

        return response_text if response_text.strip() else ""

    except Exception as e:
        return f"Error fetching Google answer: {str(e)}"

def fetch_duckduckgo_answer(query):
    try:
        search_url = "https://api.duckduckgo.com/"
        params = {"q": query, "format": "json"}
        response = requests.get(search_url, params=params)
        response.raise_for_status()
        search_results = response.json()

        responses = []
        if 'RelatedTopics' in search_results:
            for result in search_results['RelatedTopics']:
                if 'Text' in result and 'FirstURL' in result:
                    snippet = result['Text']
                    link = result['FirstURL']
                    responses.append(f"{snippet} ({link})")

        response_text = '\n\n'.join(responses)

        return response_text if response_text.strip() else ""

    except Exception as e:
        return f"Error fetching DuckDuckGo answer: {str(e)}"

def fetch_yahoo_answer(query):
    try:
        search_url = "https://search.yahoo.com/search"
        params = {"p": query}
        response = requests.get(search_url, params=params)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        responses = []
        for item in soup.find_all('li', class_='dd algo algo-sr Sr'):
            snippet = item.find('div', class_='compText').text
            link = item.find('a', class_='fz-ms')['href']
            responses.append(f"{snippet} ({link})")

        response_text = '\n\n'.join(responses)

        return response_text if response_text.strip() else ""

    except Exception as e:
        return f"Error fetching Yahoo answer: {str(e)}"

def chatbot_response(msg):
    ints = predict_class(msg)
    if not ints:
        google_res = fetch_google_answer(msg)
        duckduckgo_res = fetch_duckduckgo_answer(msg)
        yahoo_res = fetch_yahoo_answer(msg)

        return f"\n\n{google_res}\n\n\n\n{duckduckgo_res}\n\n\n"

    res = get_response(ints, intents)

    google_res = fetch_google_answer(msg)
    duckduckgo_res = fetch_duckduckgo_answer(msg)
    yahoo_res = fetch_yahoo_answer(msg)

    return f":\n\n{res}\n\n\n\n{google_res}\n\n\n\n{duckduckgo_res}\n\n\n"

def send():
    msg = user_entry.get("1.0", 'end-1c').strip()
    user_entry.delete("1.0", 'end')
    if msg:
        chat_window.config(state=tk.NORMAL)
        chat_window.insert(tk.END, f"You: {msg}\n", 'user')
        res = chatbot_response(msg)
        chat_window.insert(tk.END, f"Bot: {res}\n", 'bot')
        chat_window.config(state=tk.DISABLED)
        chat_window.yview(tk.END)

def greet_user():
    chat_window.config(state=tk.NORMAL)
    chat_window.insert(tk.END, "Bot: Hello! How can I assist you today?\n\n", 'bot')

def open_web_chatbot():
    url = "https://www.chatbase.co/chatbot-iframe/LmpAtH8eLEVzg-4mX53Qq"
    webbrowser.open(url)

# Create the main window
root = tk.Tk()
root.title("Chatbot")
root.geometry("1200x1000")

# Optionally, add a method to exit fullscreen mode
def toggle_fullscreen(event=None):
    root.attributes('-fullscreen', not root.attributes('-fullscreen'))
    return "break"

root.bind("<F11>", toggle_fullscreen)  # Bind F11 key to toggle fullscreen

# Configure background color
root.configure(bg='#2b2b2b')

# Create the chat window
chat_window = scrolledtext.ScrolledText(root, bd=0, bg="#333333", fg="#e0e0e0", width=100, height=30, font=("Roboto", 12), wrap=tk.WORD)
chat_window.tag_configure('user', foreground="#00bfff", font=("Roboto", 12, 'bold'))
chat_window.tag_configure('bot', foreground="#e0e0e0", font=("Roboto", 12))
chat_window.config(state=tk.DISABLED)
chat_window.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

# Create the user input field
user_entry = tk.Text(root, bd=0, bg="#ffffff", fg="#333333", width=100, height=5, font=("Roboto", 12), wrap=tk.WORD, relief="flat", highlightthickness=0)
user_entry.pack(pady=10, padx=20, fill=tk.X)

# Create the send button
send_button = tk.Button(root, text="Send", command=send, width=20, height=2, bd=0, bg="#007bff", fg="white", font=("Roboto", 12, 'bold'), relief="raised", overrelief="ridge")
send_button.pack(pady=10)

# Create the open web chatbot button
web_chatbot_button = tk.Button(root, text="Open Web Chatbot", command=open_web_chatbot, width=20, height=2, bd=0, bg="#28a745", fg="white", font=("Roboto", 12, 'bold'), relief="raised", overrelief="ridge")
web_chatbot_button.pack(pady=10)

# Define the ChatbotWebView class to embed the web-based chatbot
class ChatbotWebView(QMainWindow):
    def __init__(self, parent=None):
        super(ChatbotWebView, self).__init__(parent)
        self.setWindowFlags(Qt.Widget)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout(self.central_widget)

        self.web_view = QWebEngineView()
        chatbot_url = "https://www.chatbase.co/chatbot-iframe/LmpAtH8eLEVzg-4mX53Qq"
        self.web_view.setUrl(QUrl(chatbot_url))
        layout.addWidget(self.web_view)

def run_pyqt_app():
    pyqt_app = QApplication(sys.argv)
    pyqt_window = ChatbotWebView()
    pyqt_window.show()
    pyqt_app.exec_()

import threading
pyqt_thread = threading.Thread(target=run_pyqt_app, daemon=True)
pyqt_thread.start()

# Greet the user on startup
root.after(1000, greet_user)

root.mainloop()
