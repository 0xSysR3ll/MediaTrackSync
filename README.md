# MediaTrackSync

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/0xsysr3ll/mediatracksync/blob/main/LICENSE) [![Python Version](https://img.shields.io/badge/python-3.11%20|%203.12-blue)](https://www.python.org/downloads/) [![Docker Image](https://img.shields.io/badge/docker-ghcr.io/0xsysr3ll/mediatracksync-blue)](https://github.com/0xsysr3ll/mediatracksync/pkgs/container/mediatracksync) [![Build Status](https://github.com/0xsysr3ll/mediatracksync/actions/workflows/ci.yml/badge.svg)](https://github.com/0xsysr3ll/mediatracksync/actions/workflows/ci.yml) [![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black) [![Type Check](https://img.shields.io/badge/types-mypy-blue.svg)](https://mypy.readthedocs.io/) [![Lint](https://img.shields.io/badge/lint-flake8-blue.svg)](https://flake8.pycqa.org/)

> [!NOTE]
> A Python application that automatically marks TV shows and movies as watched in your favorite tracking apps whenever playback ends on Plex or Jellyfin.

## 📋 Table of Contents

- [Features](#-features)
- [Supported Services](#-supported-services)
- [Quick Start](#-quick-start)
- [Configuration](#-configuration)
- [Integrations](#-integrations)
- [Webhooks](#-webhooks)
- [Usage](#-usage)
- [Docker](#-docker)
- [Development](#-development)
- [Contributing](#-contributing)
- [License](#-license)

## ⚙️ Features

- Automatically marks content as watched on TVTime and Trakt.tv
- Supports both TV shows and movies
- Configurable logging with file rotation and JSON format
- Retry mechanism with exponential backoff
- Docker support
- Multi-user support
- Automatic metadata provider integration (IMDB, TVDB, TMDB)

## 🎯 Supported Services

### Media Servers
- [Plex](https://github.com/0xsysr3ll/mediatracksync/wiki/How-to-setup-Plex-webhook)
- [Jellyfin](https://github.com/0xsysr3ll/mediatracksync/wiki/How-to-setup-Jellyfin-Webhook)

### Tracking Services
- [TVtime](https://github.com/0xsysr3ll/mediatracksync/wiki/TVtime-Integration)
- [Trakt.tv](https://github.com/0xsysr3ll/mediatracksync/wiki/TrackTV-Integration)

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or 3.12
- Docker (optional)
- Media server (Plex or Jellyfin)
- Tracking service accounts (TVtime and/or Trakt.tv)

### Installation

<details>
<summary>Local Installation</summary>

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

</details>

## ⚙️ Configuration

The configuration file (`config/config.yml`) supports the following options:

```yaml
# Example configuration
users:
  user1:  # Username as key
    tvtime:
      username: "tvtime_user"
      password: "tvtime_pass"
    tracktv:
      client_id: "your_client_id"
      client_secret: "your_client_secret"
      code: "your_auth_code"
      redirect_uri: "http://127.0.0.1:5000"

logging:
  level: "INFO"
  format: "json"
  file: "logs/mediatracksync.log"
  max_size: 10485760  # 10MB
  backup_count: 5
```

> [!IMPORTANT]
> The `redirect_uri` must match exactly what you configured in your Trakt.tv application settings.
> This URL does not need to be reacheable by Trakt.tv

## 📡 Integrations

<details>
<summary>TVtime Integration</summary>

See the [TVtime Integration Guide](https://github.com/0xsysr3ll/mediatracksync/wiki/TVtime-Integration) for detailed setup instructions.
</details>

<details>
<summary>TrackTV Integration</summary>

See the [TrackTV Integration Guide](https://github.com/0xsysr3ll/mediatracksync/wiki/TrackTV-Integration) for detailed setup instructions.
</details>

## 📡 Webhooks

<details>
<summary>Plex Webhook Setup</summary>

See the [Plex Webhook Guide](https://github.com/0xsysr3ll/mediatracksync/wiki/How-to-setup-Plex-webhook) for detailed setup instructions.
</details>

<details>
<summary>Jellyfin Webhook Setup</summary>

See the [Jellyfin Webhook Guide](https://github.com/0xsysr3ll/mediatracksync/wiki/How-to-setup-Jellyfin-Webhook) for detailed setup instructions.
</details>

## ▶️ Usage

### Development

1. Start the application in development mode:
   ```bash
   python -m app.main
   ```

### Production

For production deployment, use Gunicorn as the WSGI server:

1. Install Gunicorn:
   ```bash
   pip install gunicorn
   ```

2. Start the application:
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"
   ```

## 🐳 Docker

### Quick Start

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

### Docker Compose

For production deployment, use Docker Compose with Gunicorn:

```yaml
services:
  mediatracksync:
    image: ghcr.io/0xsysr3ll/mediatracksync:latest
    ports:
      - "5000:5000"
    volumes:
      - ./config:/app/config
      - ./logs:/app/logs
    environment:
      - PORT=5000
    command: gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"
```

## 🛠️ Development

<details>
<summary>Development Setup</summary>

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
</details>

### Project Structure

```
mediatracksync/
├── app/
│   ├── managers/     # Media server managers
│   ├── services/     # Tracking services
│   ├── utils/        # Utility functions
│   └── main.py       # Application entry point
├── config/           # Configuration files
├── logs/            # Log files
├── tests/           # Test files
└── requirements.txt # Dependencies
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes
4. Push to your branch
5. Open a Pull Request with a clear description of your enhancement

### Development Guidelines

- Follow PEP 8 style guide
- Write tests for new features
- Update documentation
- Use type hints
- Run linters before committing

## 📝 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

> [!TIP]
> Found a bug or have a feature request? Please [open an issue](https://github.com/0xsysr3ll/mediatracksync/issues/new)!
