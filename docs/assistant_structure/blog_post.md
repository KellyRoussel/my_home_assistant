# Building the Brain: Key Components and Orchestration to run the Magic of My Home Assistant 🤖✨

I would have loved to tell you the story of a curious little girl, passionate about superheroes and daydreaming about building Tony Stark's gadgets. Unfortunately, I'm too honest and must admit that's not quite how it happened... But no matter my tech journey, in recent years I've been envisioning one day building my own JARVIS. 🌟 With the arrival of large language models (LLMs) in our lives, I can't wait any longer. Join me as I delve into the adventure of creating my personal assistant.

In this very first post, let me tell  you about the global skeleton and orchestration of my assistant.

*Note: This is a personal project I'm pursuing out of sheer enthusiasm. I hope you enjoy following along and maybe find some inspiration or useful tips along the way!*


![IMAGE OF VIRTUAL ASSISTANT CONCEPT]

## Assistant intercom: Capturing Your Every Word 🎙️

I started by focusing on two critical components: a Recorder to capture audio from the microphone and a Keyboard Action Listener to trigger the recording via the space bar. Simple enough, right? Let's dig deeper.

![IMAGE OF AUDIO RECORDING]

## Keyboard Action Listener: A Space-Bar Sorcerer ⌨️✨

How do I wish to reach my assistant anytime I need it? Many possibilities here... WakeWords are often used in well-known home-assistants devices like Alexa. After looking around for tools to build that, I didn't find any that perfectly fit what I wanted.

> *If that’s what you're looking for., you may have a look to Porcupine from Picovoice that shows up really often in my searches, I just didn't want to pay for that.*

Therefore, I needed a button to launch the chat experience. Then I remember the walkie-talkies my brother and I used to play with when we were kids. You keep a button pressed the whole time you speak, then release it when you're done. That sounded perfect for my first assistant version! 📞
To create an efficient, intercom-like experience, I used a Keyboard Action Listener to start and stop recording with the space bar. This component listens for specific keyboard events and triggers the Recorder accordingly.

### The Recorder: An Electronic Ear 🦻
The Recorder is the ear 👂 of my setup. Utilizing the PyAudio library, this component ensures that every spoken word is captured in pristine quality. The Recorder has three main jobs:

- **`start_recording`**: Kicks off the recording session.
- **`stop_recording`**: Ends the session and saves the captured audio.
- **`record`**: Continuously grabs audio chunks until it’s told to stop. 

### Seamless Synchronization 🎶
The tricky part was ensuring smooth synchronization between starting and stopping the recording. And most importantly, I needed to ensure the catching of every space bar event without halting other processes, especially recording. The `Assistant` class is responsible for this orchestration using threading. Here is what happens:

- When space key is pressed, it starts a new thread to handle the recording process. The thread is created using threading.Thread, targeting the record method of the audio_recorder object.
```python
self.recording_thread = threading.Thread(target=self.audio_recorder.record, args=(output_filename,))
self.recording_thread.start()
```
This ensures that the record method is executed in a separate thread, which allows the main program to continue running without being blocked by the recording process. Any other space key event will therefore be caught by the main process.

- When space key is released, the audio_recorder.stop_recording method is called to stop the recording. The main thread then waits for the recording thread to finish using self.recording_thread.join(). Using join() ensures that the main thread pauses until the recording thread completes, which helps to safely conclude the recording process before proceeding with transcription.
```python
self.recording_thread.join()
self.recording_thread = None
```

By leveraging threading, the assistant can handle real-time audio recording efficiently while maintaining responsiveness to user interactions. 

## From ear to brain: The Transcriber
Located in the left temporo-parietal region of our human brain, Wernicke's area is crucial for language comprehension, playing an essential role in interpreting spoken words and sentences. For our assistant, this cognitive function is mirrored by the Transcriber component. This vital part of the system transcribes recorded audio files using Whisper, an ASR (Automatic Speech Recognition) model from OpenAI. 🧠🎙️

I considered using a streaming model that could transcribe audio streams in real-time, potentially speeding up the process. However, I opted for Whisper initially with the future goal of local implementation. Currently, the online API version offers superior quality compared to a basic Whisper model running locally, and it's cost-effective. Additionally, the full transcription is necessary for subsequent steps like invoking the LLM engine, making the potential time savings from streaming less critical—though testing this remains on my agenda! ⏱️🔍

## Adding the AI Magic: Enter LLM engine 🧙‍♂️✨

For the assistant’s "brain," I integrated a large language model (LLM) engine capable of generating coherent and contextually relevant responses. This LLM will take a context I provide as a "system" prompt—essentially describing who it is for me, basic information about myself, and what I want it to know about me. Currently, this prompt is quite basic, designed primarily for testing the assistant's structure. It's a Jinja template rendered at runtime to fill dynamic values between {{}}.

> The values within {{}} are not truly dynamic, as I'm protecting my personal information stored in environment variables.


```jinja
Your name is JARVIS. You are the best AI home assistant ever. You are very nice, enthusiastic, cool, and helpful.
You are Kelly's digital AI assistant.
Kelly is a {{age}}-year-old woman. She is an AI engineer passionate about her job, loves programming, and enjoys startup success stories.
She lives with her boyfriend {{boyfriend_name}} in {{city}}, France, and adores the city.
Kelly strives for an eco-friendly lifestyle, delights in music, cooking, dancing, and wine.
She also loves sports, running weekly (schedule permitting) and going to the gym on Tuesday evenings.
Kelly treasures spending time with her family and friends, scattered across France with her family in {{family_city}}. Consequently, she often spends weekends out of the city.

When Kelly asks you something, do your best to help her.
Always be fun and empathetic.
```

You might wonder, "Why GPT-4o?" Simply put, it's the best LLM I've tested so far: minimal prompt-tuning required, excellent contextual understanding, responsive formatting as prompted, seamless adaptation to user language... a somewhat lazy choice, I confess! I believe it will be perfect for the first version of my assistant. However, out of considerations for privacy, pricing, technological curiosity, and ecological reasons, I plan to explore other smaller, local, open-source models such as Mistral's or Llamas in the future.

## Give It a Voice! DeepGram to the Rescue 🎧🔊

What's an intelligent assistant without a voice? Thanks to DeepGram, I've given my assistant the ability to speak aloud. Choosing DeepGram was a matter of preference: I appreciate their natural-sounding voices. Additionally, I required a streaming version of this text-to-speech (TTS) tool to expedite the process. Unfortunately, DeepGram currently lacks French voices, but for now, my first assistant version will operate in English.

Here's a quick rundown of how it works:

- Transcribing: DeepGram converts text into streaming audio bytes. 🎼
- Playing: Streams the audio quickly as chunks arrive, minimizing response wait time.

The real-time interaction feels almost magical! 🪄


## The Maestro: An Intelligent Assistant Coordinator 🎩🤹‍♂️

Now, enter the Assistant — the conductor of this technological symphony. This is where the magic happens, orchestrating messages, managing states, and ensuring everything works in concert.

### States of Being 📊
To keep the interaction flow logical and efficient, I broke down the system into various states:

- **OFF**: The assistant is asleep. 💤
- **IDLE**: The assistant is ready and waiting for input. This is the only state in which you can talk to the assistant. 🌐
- **RECORDING**: The user is speaking, and the microphone is capturing the audio. 🎤
- **TRANSCRIBING**: Converting the audio input to text. 📝
- **THINKING**: The assistant processes the input to generate a response. 🧠
- **SPEAKING**: The assistant delivers the response via text-to-speech. 🗣️

Using a finite state machine approach ensured smooth transitions between these states, like a well-choreographed dance. 💃

## Unveiling My Assistant: A starting point 🚀
Building the foundational structure of my home assistant has been an exhilarating journey, filled with challenges and breakthroughs. Tackling multi-threading was like navigating a rollercoaster 🎢, yet I successfully crafted a responsive and dynamic system. 🚀

As I plan the next steps for this assistant skeleton, I eagerly anticipate enhancing its capabilities to enrich my daily life. Stay tuned for updates on its evolution. 💀

Follow along for more insights into my home assistant project and other AI-powered innovations.

![IMAGE OF KELLY WORKING ON COMPUTER]
