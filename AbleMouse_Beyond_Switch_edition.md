# AbleMouse Beyond Switch Edition
**When All Else Fails, This Works.** 🦾
<img src="docs/img/ablemouse_beyond_switch/imagination2reality.jpg" alt="AbleMouse AI edition" style="width: 250px; border: 2px solid #ccc; border-radius: 10px;" />

🎞 **Video Demonstration :** [Watch on YouTube](https://youtu.be/1zWn1Ha5-U0)👆

Imagine a person who is completely paralyzed (both body and head) and is also **unable to speak**. In the specific case I am referring to, the individual only had access to a single micro-movement — he could only slightly open his mouth.

🕊️ I have developed a solution that helped a person with such a severe disability return to the digital world and regain full control of his computer. This method is more natural and flexible than traditional "Switch Control" approaches (like those implemented in macOS). <br>I am sharing this development because it has the potential to change many lives.



❤️ I would be deeply grateful if you could share this project with those in need or on specialized community forums.

---

### ⚙️ Technical Details

🔹 **Control Principle:** The system is based on a hierarchical menu that cyclically cycles through items. As soon as the user sees the desired command, they provide a signal (that specific micro-movement), and the action is executed.

🔹 **Any Sensor:** In the current version, computer vision via a standard webcam detects the mouth's micro-movement. However, the architecture allows for the connection of absolutely any input signal or sensor. You simply need to send a command to the application server via the **TCP protocol**.

🔹 **Breaking Language Barriers:** The interface is fully customizable and can be translated into any language. Windows' limitations on supported input languages are bypassed automatically — the user sees their native language, while the system correctly interprets the commands.

🔹 **Flexibility:** The server component allows you to build a menu of any complexity, tailored to the specific tasks and physical capabilities of the individual.

---

### 📅 Release Schedule
All source code and detailed setup instructions will be published **this weekend**.

---
# Components, Setup, and Launch

> **Note:** The AbleMouse Beyond Switch code is completely free and distributed under the MIT license. However, to provide audio routing, I use the VB-CABLE driver. <br>VB-CABLE is distributed as Donationware. While it is free to download and use, a donation or license purchase is expected if you find it useful or use it professionally.
> You can support the developer using the following link to [vb-audio](https://shop.vb-audio.com/en/win-apps/11-vb-cable.html)

## Program Components, Their Purpose, and Configuration

1.  **[menu_config.py](src/ablemouse_beyond_switch_edition/menu_config.py)** - Configuration for the menu displayed in the application. It's a kind of constructor that can be adapted to an individual's needs.
2.  **[app_config.py](src/ablemouse_beyond_switch_edition/app_config.py)** - Application settings.
3.  **[main.py](src/ablemouse_beyond_switch_edition/main.py)** - The main component implementing the UI and server logic.
    *   Any application you develop that can send commands via TCP can act as a client.
    *   **Creating a Python venv and Setup**
        *   !!!!! TODO: Which libraries need to be additionally installed.
        * !!!!!! ToDo если будете использовать AI то нужно питон версий ..... см пунк 4 далее ро тексту
    *   In [app_config.py](src/ablemouse_beyond_switch_edition/app_config.py), set the values for your configuration:
        *   `SERVER_CONFIG`
        *   `UI_CONFIG.highlight_interval` - This parameter controls the speed at which menu items alternate. It needs to be adjusted for the specific person you are helping (so they have enough time to react).

4.  Any custom application you develop that can communicate with the server via the TCP protocol can be used as a client.
    *   4.1 In the demonstration video, I used **AbleMouse AI Edition** as the client. Installation and configuration must be performed according to the [AbleMouse AI Edition Setup](AbleMouse_AI_edition.md) guide.
    * 4.2 In the source code [able_mouse_ai_edition.py](src/ablemouse_ai_edition/able_mouse_ai_edition.py), set the variable:
      * 4.2.1 *   `USE_MENU_SYSTEM = True`
      * 4.2.2  If you change the host and port for the AbleMouse Beyond Switch server, you must enter them into the `MENU_HOST` and `MENU_PORT` variables.
      * 4.2.3   It is also recommended to slightly increase the value of `MOUTH_OPEN_THRESHOLD` from what was set in step 1. For example, in my configuration I use `0.002` when using AbleMouse AI Edition independently and `0.008` when using it together with AbleMouse Beyond Switch.

5.  **Install the VB-CABLE Virtual Audio Device driver by VB-Audio Software.**
    *   Installation and setup instructions via the link: [vb_cable.md](vb_cable.md)

6.  **Launch Windows Accessibility Speech (Voice Access)**
    *   Windows Voice Access is used to execute the voice commands generated by the core component.
    *   Setup instructions: [windows_voice_access.md](windows_voice_access.md)

7.  **Launching the Application**
    1.  Start the Server: run [main.py](src/ablemouse_beyond_switch_edition/main.py)
    2.  Start the Client: [able_mouse_ai_edition.py](src/ablemouse_ai_edition/able_mouse_ai_edition.py).
    
8. **Start Session**
<br>Click on the title bar of the application window where the menu is running. Now, rely entirely on AbleMouse Beyond Switch Edition. Put your physical mouse aside and complete all tasks using only the Beyond Switch controls.

