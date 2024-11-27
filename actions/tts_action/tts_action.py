import pyttsx3

def speak_vietnamese(text):
    engine = pyttsx3.init()
    rate = engine.getProperty('rate')
    engine.setProperty('rate', rate-20) #Tốc độ nói
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[1].id) #Giọng nói
    engine.say(text)
    engine.runAndWait()