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


