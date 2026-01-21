# AbleMouse AI edition

> ❤️Control the mouse pointer using your face.
> 
> The code works under both Windows and Mac Os. Note: Unix/Ubuntu support possible — requires testing

>▶️[Video AbleMouse AI edition](https://youtu.be/AlqSVKt535Y)
> / [Source Code](src/ablemouse_ai_edition/able_mouse_ai_edition.py) / ▶️[initial setup](https://youtu.be/KCn4GMMQkxc)
> 
> Note: In the video demonstration for calling the on-screen keyboard in Windows, I used gesture recognition via [MouseCommander (win)](https://github.com/aradzhabov/AbleMouse/blob/main/src/windows/auto_hot_key/README.md) , which is also part of the AbleMouse project. <br> On macOS, there is no need to use MouseCommander, as the built-in keyboard with the "dwelling" setting enabled and customizable transparency levels is both convenient and does not clutter the interface with its presence.

<img src="docs/img/ablemouse_ai_icon.jpg" alt="AbleMouse AI edition" style="width: 250px; border: 2px solid #ccc; border-radius: 10px;" />


An important aspect is that the solution is fully open-source and can be easily adapted to meet the needs of a specific individual.

To use AbleMouse AI edition, it is enough that you can turn and tilt your head, and use your eyes and mouth. 
The mouse pointer is positioned based on the direction of your nose, allowing you to work effectively even with very large screens.
macOS and Windows do not have such a solution built-in.
Another very important difference from other solutions is that your eyes remain free, as the tracking is based on the direction of your nose. This provides a much more natural feeling for us as humans. For example, solutions that require you to look at the point where you want to move the cursor demand significantly more effort and feel unnatural. An ordinary person using a hand-operated mouse can look anywhere—AbleMouse allows you to do the same.

A few notes on use and configuration:

*   To adapt the program for a specific person, you will need the assistance of someone with basic Python knowledge. In my opinion, a school student's level is sufficient.
    The solution itself is very simple and essentially consists of a single file where settings need to be adjusted for the specific user. Most parameters in the code are self-explanatory from their names, and in most cases, many of them do not need to be changed. I will describe the most important ones below. Please don't hesitate to write to me if you have any questions.

*   I recommend using an external webcam, as this allows for maximum comfort in screen positioning, especially for bedridden individuals.
    If you are using an external webcam, you need to set the `camera` parameter to a value other than 0 (usually this value is 1). The value 0 corresponds to the built-in camera in your laptop.

*   `EYE_CLOSE_THRESHOLD` - Thresholds for determining closed eyes (distance between the upper and lower eyelashes).
    `MOUTH_OPEN_THRESHOLD` - Threshold for determining an open mouth (distance between the lips).

It is important to understand that these parameters greatly depend on the distance of the face from the camera and the camera itself. You also need to consider that, for example, when you tilt your head, the distance between the calculated points decreases due to projection. When you run the program, you can easily check its operation with your settings, as a window will open displaying each gesture. This window can also be used for training. The window will remain open while the program is running but can be hidden behind other applications. This does not affect the program's operation.

*   For Python developers: `Python 3.9-3.12`. To run the program, you will need to create a virtual environment (venv) and install just 3 packages:
    `opencv-python`, `mediapipe==0.10.21`, `pyautogui`
    After that, run [able_mouse_ai_edition.py](src/ablemouse_ai_edition/able_mouse_ai_edition.py). !!After launching, don't forget to properly [calibrate the camera position](https://youtu.be/KCn4GMMQkxc)!!

*   Overall, I also see the program as an educational moment. I think many students will be able to pick up something useful for themselves.
    The program itself is a maximally simplified, small slice from my R&D version from two years ago.

    I could have significantly simplified the code by using `sleep` instructions in more places instead of cooldowns, but my experience shows that these freezes are very noticeable and feel unnatural. I also intentionally did not publish a clean object-oriented version of the code, as it will be much easier for beginners to understand a version without OOP.

## Support
- aradzhabov@gmail.com
- [LinkedIn](https://www.linkedin.com/in/aradzhabov/)

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

### Connect With Us

[![Website](https://img.shields.io/badge/Website-Learn%20More-green)](https://aradzhabov.github.io/gagarin_data_labs/)

**#Accessibility #AssistiveTech #OpenSource #DIY #Innovation #MouthPad #eye-tracker #Neuralink**


