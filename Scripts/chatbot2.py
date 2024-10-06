import tkinter as tk
from tkinter import scrolledtext
import random
import json
import pickle
import numpy as np
import nltk
from nltk.stem import WordNetLemmatizer
from keras.models import load_model

# Load necessary files and models
lemmatizer = WordNetLemmatizer()
intents = json.loads(open('intents.json').read())
words = pickle.load(open('words.pkl', 'rb'))
classes = pickle.load(open('classes.pkl', 'rb'))
model = load_model('chatbot_model.h5')

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
    tag = intents_list[0]['intent']
    list_of_intents = intents_json['intents']
    for i in list_of_intents:
        if i['tag'] == tag:
            result = random.choice(i['responses'])
            break
    return result

def chatbot_response(msg):
    ints = predict_class(msg)
    res = get_response(ints, intents)
    return res

def send():
    msg = user_entry.get("1.0", 'end-1c').strip()
    user_entry.delete("1.0", 'end')
    if msg:
        chat_window.config(state=tk.NORMAL)
        chat_window.insert(tk.END, "You: " + msg + '\n\n')
        res = chatbot_response(msg)
        chat_window.insert(tk.END, "Bot: " + res + '\n\n')
        chat_window.config(state=tk.DISABLED)
        chat_window.yview(tk.END)

def on_entry_click(event):
    if user_entry.get("1.0", 'end-1c') == 'Type here...':
        user_entry.delete("1.0", "end")
        user_entry.insert("1.0", '')
        user_entry.config(fg='black')

def on_focus_out(event):
    if user_entry.get("1.0", 'end-1c') == '':
        user_entry.insert("1.0", 'Type here...')
        user_entry.config(fg='grey')

# Create the main window
root = tk.Tk()
root.title("Chatbot")
root.geometry("400x500")
root.configure(bg="#2c3e50")

# Create the chat window frame
chat_frame = tk.Frame(root, bg="#2b3e50")
chat_frame.pack(pady=10)

# Create the chat window
chat_window = scrolledtext.ScrolledText(chat_frame, bd=0, bg="#ecf0f1", fg="#2c3e50", width=50, height=15, font=("Arial", 12))
chat_window.config(state=tk.DISABLED)
chat_window.pack(padx=10, pady=10)

# Create the user input frame
input_frame = tk.Frame(root, bg="#2c3e50")
input_frame.pack(pady=10)

# Create the user input field with placeholder
user_entry = tk.Text(input_frame, bd=0, bg="#ecf0f1", fg='grey', width=30, height=4, font=("Arial", 12))
user_entry.insert("1.0", 'Type here...')
user_entry.bind('<FocusIn>', on_entry_click)
user_entry.bind('<FocusOut>', on_focus_out)
user_entry.pack(side=tk.LEFT, padx=10)

# Create the send button
send_button = tk.Button(input_frame, text="Send", command=send, width=12, height=2, bd=0, bg="#3498db", fg="white", font=("Arial", 12))
send_button.pack(side=tk.RIGHT, padx=10)

root.mainloop()
