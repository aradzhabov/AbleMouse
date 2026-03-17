> Note 1:This R&D project is for demonstration and feedback purposes only.
If you have any questions please contact to aradzhabov@gmail.com


> Note 2: This activity is part of the product development work within the [AbleMouse Ecosystem](https://github.com/aradzhabov/AbleMouse).
>

## TellMeCam

>Experience AI-Vision Without Ever Taking Your Phone Out of Your Pocket

>See with your voice | 100% Hands-Free Voice-Controlled AI-Vision

>Clip, Connect, Talk: The ultra-low-cost wearable eyes for your AI.
---

TellMeCam is the first The **ultra-low-cost** wearable eyes (<$10) for your AI that **SEES** and **ANSWERS** your questions about the surrounding environment in real-time — controlled 100% by voice. **No buttons, no screen interaction required.**

While primarily designed to empower the blind and visually impaired community,  it separates the "eyes" (camera) from the "brain" (smartphone/AI), ensuring safety, affordability, and true mobility, its architecture supports a wide range of applications, from security systems to wildlife monitoring.

> Put your phone in your pocket, lock the screen, and just start talking.

## Why This Matters

1.  **Safety:** For visually impaired users, holding a phone out in public is a theft risk. **tellMeCam** keeps the phone hidden.
2.  **Accuracy:** By mounting the module on the head, the AI "sees" exactly what the user is facing, providing better spatial context.
3.  **Scalability:** Beyond accessibility, this logic can be applied to DIY home security, wildlife tracking, and industrial monitoring.
---

## 🗣️ How It Works

Imagine wearing a small camera module on your head. You simply say: *"BlueBerry, do you see my glasses?"* The system captures an image, analyzes it locally, and speaks the answer back to you.

## Key Operating Scenarios (Voice Controlled)

Everything starts with your custom Wake Word (e.g., **"BlueBerry"**).

| Mode        | Command Example                                | What it does                                                 |
|:------------|:-----------------------------------------------|:-------------------------------------------------------------|
| **Ask**     | *"BlueBerry, what's on the table?"*            | Takes a photo, analyzes it, and speaks the answer.           |
| **Track**   | *"BlueBerry, track - do you the bus number 5"* | Continuously monitors the feed and updates you at intervals. |
| **Scan**    | *"BlueBerry, scan - for the bus number 5"*     | Stays silent until the target object is found.               |
| **Utility** | *"BlueBerry, Flash on"*                        | Controls the module's hardware (LED flash/Torch).            |
| **SOS**     | *"BlueBerry, SOS!"*                            | Triggers emergency alerts or notifies relatives.             |
| **...**     | *"BlueBerry, ...!"*                            | ...                                                          |
---



---


### The Setup

- **The Hardware:** A <$10 ESP32-CAM (*The Eyes*)
- **The Hub:** Your Smartphone in your pocket (*The Voice & Connectivity*)
- **The Brain:** TellMeCam Backend (*The Intelligence — runs locally or in the cloud*)

---

### Features

- **True Background Operation:** The app works seamlessly with the screen off. No need to hold your phone or keep it active; it stays securely in your pocket.

- **Battery Optimized:** By offloading vision to the external module and running the app in the background, you save significant smartphone battery life.

- **Hands-Free Voice Control:** Full interaction via Wake Word (e.g., "BlueBerry"). Start tracking, scanning, or asking questions without ever touching your device.











