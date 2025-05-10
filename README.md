# MediaTrackSync

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/0xsysr3ll/mediatracksync/blob/main/LICENSE) [![Python Version](https://img.shields.io/badge/python-3.11%20|%203.12-blue)](https://www.python.org/downloads/) [![Docker Image](https://img.shields.io/badge/docker-ghcr.io/0xsysr3ll/mediatracksync-blue)](https://github.com/0xsysr3ll/mediatracksync/pkgs/container/mediatracksync) [![Build Status](https://github.com/0xsysr3ll/mediatracksync/actions/workflows/ci.yml/badge.svg)](https://github.com/0xsysr3ll/mediatracksync/actions/workflows/ci.yml) [![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black) [![Type Check](https://img.shields.io/badge/types-mypy-blue.svg)](https://mypy.readthedocs.io/) [![Lint](https://img.shields.io/badge/lint-flake8-blue.svg)](https://flake8.pycqa.org/)

A Python application that automatically marks TV shows and movies as watched in your favorite tracking apps whenever playback ends on Plex or Jellyfin.

---

## 🚀 Quick Start

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/0xsysr3ll/mediatracksync.git
   cd mediatracksync
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy the config template and fill in your details:
   ```bash
   cp config/config.template.yml config/config.yml
   ```
5. Edit `config/config.yml` with your credentials and preferences.

---

## ⚙️ Features

- Automatically marks content as watched on TVTime and Trakt.tv
- Supports both TV shows and movies
- Configurable logging with file rotation and JSON format
- Retry mechanism with exponential backoff
- Docker support

---

## 📡 Integrations

- [TVtime Integration](https://github.com/0xsysr3ll/mediatracksync/wiki/TVtime-Integration)
- [TrackTV Integration](https://github.com/0xsysr3ll/mediatracksync/wiki/TrackTV-Integration)

---

## 📡 Webhooks

- [How to Setup Plex Webhook](https://github.com/0xsysr3ll/mediatracksync/wiki/How-to-setup-Plex-webhook)
- [How to Setup Jellyfin Webhook](https://github.com/0xsysr3ll/mediatracksync/wiki/How-to-setup-Jellyfin-Webhook)

---

## ▶️ Usage

1. Start the application:
   ```bash
   python -m app.main
   ```
2. Configure your media server webhook endpoint:
   - Plex: `/webhook/plex`
   - Jellyfin: `/webhook/jellyfin`
3. Watch content on your server; MediaTrackSync handles the rest.

---

## 🐳 Docker

1. Pull the Docker image:
   ```bash
   docker pull ghcr.io/0xsysr3ll/mediatracksync:latest
   ```
2. Run the container:
   ```bash
   docker run -d \
     -p 5000:5000 \
     -v $(pwd)/config:/app/config \
     -v $(pwd)/logs:/app/logs \
     --name mediatracksync \
     ghcr.io/0xsysr3ll/mediatracksync:latest
   ```

---

## 🛠️ Development

1. Install development dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run tests:
   ```bash
   pytest
   ```
3. Run linters:
   ```bash
   flake8 app tests
   mypy app tests
   ```
4. Format code:
   ```bash
   black app tests
   ```
5. Check coverage:
   ```bash
   pytest --cov=app tests/
   ```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes
4. Push to your branch
5. Open a Pull Request with a clear description of your enhancement

---

> _This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details._
