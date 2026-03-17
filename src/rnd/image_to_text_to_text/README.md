# talk2cam: Ask Your Camera Anything. Completely locally

**Live Camera Feed QA. Vision-to-Text: Conversing with Reality in Real-Time**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![llama.cpp](https://img.shields.io/badge/llama.cpp-GGUF-green)](https://github.com/ggml-org/llama.cpp)

>▶️[Video talk2cam](https://youtu.be/8lIvBt9HPiM)
---

## Special Thanks
Special thanks to the **[Alibaba Cloud team](https://www.alibabacloud.com/)** for supporting the [AbleMouse project](https://github.com/aradzhabov/AbleMouse/tree/main), which helps make the world more accessible for people with disabilities, and of course for their excellent open-weight models.

---

## About The Project

I've been experimenting with integrating vision-capable language models with live camera streams. The result? An interactive system that can:

- Process real-time video frames
- Answer natural language questions about the scene
- Adapt to new instructions on the fly

This opens up possibilities for:
- 👁️ Assistive technology for visually impaired
- 🏠 Real-time scene understanding
- 🤝 Interactive AI companions
- 📹 Smart surveillance systems

---

## 🚀 How to Run

### 1. Install [llama.cpp](https://github.com/ggml-org/llama.cpp)

There are multiple ways to do this. The simplest is to download a pre-compiled version for your hardware.

For example, I downloaded from [llama.cpp releases](https://github.com/ggml-org/llama.cpp/releases):
- `Windows x64 (CUDA 12)`
- `CUDA 12.4 DLLs`

- **Note 1:** Check your CUDA version by running `nvidia-smi` and looking at the top right corner.
- **Note 2:** If using GPU, copy files from `CUDA 12.4 DLLs` into the `Windows x64 (CUDA 12)` folder.
- **Note 3:** Without GPU everything still works, but you'll need to set a 10+ second delay between frames (for larger models).

### 2. Choose a Model

Browse video-text-to-text models with GGUF format on Hugging Face:
👉 [Video-to-Text Models with llama.cpp support](https://huggingface.co/models?pipeline_tag=video-text-to-text&library=gguf&apps=llama.cpp&sort=downloads)

**You don't need to manually download models** - when you run llama-server, it will automatically download the specified model.

### 3. Start the Server

#### Without GPU: 
- llama-server -hf prithivMLmods/SAGE-MM-Qwen2.5-VL-7B-SFT_RL-GGUF:Q4_K_M


#### With GPU:

- llama-server -hf prithivMLmods/SAGE-MM-Qwen2.5-VL-7B-SFT_RL-GGUF:Q4_K_M -ngl 99

Why this model? I like this model because it's multilingual and answers questions very well.
👉 [SAGE-MM-Qwen2.5-VL-7B-SFT_RL-GGUF](https://huggingface.co/prithivMLmods/SAGE-MM-Qwen2.5-VL-7B-SFT_RL-GGUF) on Hugging Face

💻 For weaker computers:
Try this smaller model (I found it good at describing what it sees, but not as good at answering follow-up questions):
llama-server -hf ggml-org/SmolVLM2-500M-Video-Instruct-GGUF:Q8_0

👉 [SmolVLM2-500M-Video-Instruct-GGUF](https://huggingface.co/ggml-org/SmolVLM2-500M-Video-Instruct-GGUF)
 
### 4. Run Camera Llama
[talk2cam.py](./talk2cam.py)

How to Use
- Start - Click "▶ Start" to begin camera capture
- Ask - Type your question in the instruction box
- Settings - Click "⚙ Settings" to adjust server URL, image size, and interval

⚙️ Configuration Options
- Server URL	Where llama.cpp server is running (default: http://localhost:8080)
- Camera ID	Which camera to use (0 = built-in, 1 = external)
- Interval	Milliseconds between frame captures
- Image Size	Resize images before sending (smaller = faster)
- Instruction	What to ask the model about each frame