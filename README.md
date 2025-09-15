
<div align="center">
  <img src="https://raw.githubusercontent.com/juniorsir/TubeZ/main/.github/assets/logo.png" alt="TubeZ Logo" width="150"/>
  <h1>TubeZ</h1>
  <p>
    A powerful, self-hosted web dashboard to search, play, and download video or audio from hundreds of sites using yt-dlp.
  </p>
  <p>
    <a href="https://pypi.org/project/TubeZ/"><img alt="PyPI" src="https://img.shields.io/pypi/v/TubeZ?color=blue&label=pypi%20package"></a>
    <a href="https://github.com/juniorsir/TubeZ/blob/main/LICENSE"><img alt="License" src="https://img.shields.io/github/license/juniorsir/TubeZ"></a>
  </p>
</div>

![TubeZ Demo GIF](https://raw.githubusercontent.com/juniorsir/TubeZ/main/.github/assets/demo.gif)

---

### **Table of Contents**

- [✨ Features in Depth](#-features-in-depth)
- [🛠️ Technology Stack](#️-technology-stack)
- [🚀 Installation](#-installation)
- [▶️ How to Run](#️-how-to-run)
- [🐳 Docker Deployment (Advanced)](#-docker-deployment-advanced)
- [🔧 Configuration](#-configuration)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)

---

## ✨ Features in Depth

-   **Modern & Responsive UI**: Clean, beautiful, and mobile-friendly interface built with Bootstrap. It includes a dark mode theme and a fully responsive layout that works on any device.

-   **Universal Support**:
    -   **YouTube Search**: Find any video on YouTube directly from the app.
    -   **Direct URL Support**: Paste a video, playlist, or channel URL from hundreds of websites supported by `yt-dlp`.

-   **Direct Streaming**: Why wait? Play videos and audio directly in your browser with a multi-stage loading animation that provides clear feedback. It intelligently handles sites that don't support direct streaming.

-   **Advanced Downloads**:
    -   **Format Selection**: Choose the exact video quality, audio quality, or file format you need.
    -   **Playlist & Channel Downloading**: Paste a playlist or channel URL, select the videos you want, and download them all in one go.
    -   **One-Click Audio**: A dedicated "Get Audio" button streamlines downloading music and podcasts.
    -   **Subtitle Support**: Automatically fetches available subtitle languages and allows you to embed them directly into your downloaded video file.

-   **Robust Download Management**:
    -   **Background Queue**: Add multiple items to a download queue that processes sequentially in the background, so you can keep browsing.
    -   **Live Progress**: The UI dynamically updates to show real-time download progress, speed, and ETA without needing a page refresh.
    -   **File Management**: View, download, and delete your completed files directly from the web interface.

-   **Secure & Maintainable**:
    -   **Self-Hosted**: You control your data. Run it on your own machine, home server, or in the cloud.
    -   **Password Protection**: An optional password can be set to protect access to the dashboard.
    -   **Auto-Update Notifications**: The app automatically checks for new versions on PyPI and will prompt for an update, ensuring you're always on the latest stable release.

---

## 🛠️ Technology Stack

-   **Backend**: Python with **Flask**
-   **Core Engine**: **yt-dlp** for all media downloading and metadata extraction.
-   **Frontend**: **Bootstrap 5**, HTML5, CSS3, and modern JavaScript (no framework).
-   **WSGI Server**: **Waitress** for a lightweight production-ready server.
-   **Packaging**: **PyPI** for distribution and **GitHub Actions** for automated publishing.

---

## 🚀 Installation

Make sure you have Python 3.8+ and `ffmpeg` installed on your system.

#### On Linux (Debian/Ubuntu)
```bash
sudo apt update && sudo apt install python3 python3-pip ffmpeg -y
```
### On Termux (Android)
```baah
pkg update && pkg install python ffmpeg -y
```
## Install with pip (Recommended)
*(Note: You may need to use `pip3` instead of `pip` on some systems).*

---

## ▶️ How to Run

After a successful installation, you can start the web server from anywhere in your terminal.
1.  **Install using pip:**
    ```bash
    pip install TubeZ
    ```
2.  **Start the Server:**
    ```bash
    tubez
    ```

3.  **Open the Web Dashboard:**
    Open your web browser and go to: `http://127.0.0.1:8089`

4.  **Find Your Files:**
    Your downloaded videos and audio will be saved in a folder named `TubeZ` inside your main `Downloads` directory. This can be changed in the Settings page.


