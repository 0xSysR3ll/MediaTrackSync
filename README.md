# MediaTrackSync

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/0xsysr3ll/mediatracksync/blob/main/LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.11%20|%203.12-blue)](https://www.python.org/downloads/)
[![Docker Image](https://img.shields.io/badge/docker-ghcr.io/0xsysr3ll/mediatracksync-blue)](https://github.com/0xsysr3ll/mediatracksync/pkgs/container/mediatracksync)
[![Build Status](https://github.com/0xsysr3ll/mediatracksync/actions/workflows/ci.yml/badge.svg)](https://github.com/0xsysr3ll/mediatracksync/actions/workflows/ci.yml)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Type Check](https://img.shields.io/badge/types-mypy-blue.svg)](https://mypy.readthedocs.io/)
[![Lint](https://img.shields.io/badge/lint-flake8-blue.svg)](https://flake8.pycqa.org/)

A Python application that automatically marks TV shows and movies as watched on TVTime and Trakt.tv when they are watched on Plex.

## Features

- Automatically marks content as watched on TVTime and Trakt.tv
- Supports both TV shows and movies
- Configurable logging with file rotation and JSON format
- Retry mechanism with exponential backoff
- Docker support

## Installation

1. Clone the repository:

```bash
git clone https://github.com/0xsysr3ll/mediatracksync.git
cd mediatracksync
```

2. Create a virtual environment and activate it:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
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

## Trakt.tv Setup

To use Trakt.tv integration, you need to create an application and get your credentials:

1. Go to [Trakt.tv OAuth Applications](https://trakt.tv/oauth/applications/new)
2. Fill in the application details:
   - Name: `MediaTrackSync` (or any name you prefer)
   - Description: `Automatically marks content as watched when played on Plex`
   - Redirect URI: `http://127.0.0.1:5000`
   - Permissions: Select `scrobble` and `checkin`
3. Click "Save App"
4. You'll receive your `client_id` and `client_secret`
5. To get the authorization code:
   - Visit: `https://trakt.tv/oauth/authorize?response_type=code&client_id=YOUR_CLIENT_ID&redirect_uri=http://127.0.0.1:5000`
   - Replace `YOUR_CLIENT_ID` with your actual client ID
   - Log in to Trakt.tv if prompted
   - Authorize the application
   - You'll be redirected to `http://127.0.0.1:5000?code=YOUR_CODE`
   - Copy the `code` parameter value
6. Add these values to your `config.yml`:
   ```yaml
   tracktv:
     client_id: 'your-client-id'
     client_secret: 'your-client-secret'
     code: 'your-auth-code'
     redirect_uri: 'http://127.0.0.1:5000'
   ```

> [!WARNING]
> The authorization code (`code`) is temporary and will expire after a short time or when the application exits. If you see a "400 Bad Request" error when starting the application, you'll need to generate a new authorization code by following step 5 again. This is normal behavior and not an error in the application.

## TVTime Setup

> [!NOTE]
> TVTime currently does not provide a public API for third-party applications. As a result, MediaTrackSync uses your TVTime account credentials to authenticate and mark content as watched.
> This is a temporary solution until TVTime provides an official API.

To use TVTime integration:

1. Add your TVTime credentials to your `config.yml`:
   ```yaml
   users:
     your_username:
       tvtime:
         username: 'your-email@example.com'
         password: 'your-password'
   ```

> [!IMPORTANT]
> Your TVTime credentials are stored in plain text in the configuration file.
> Make sure to keep your `config.yml` file secure

## Configuration

The configuration file (`config/config.yml`) contains the following sections:

### Logging

```yaml
logging:
  level: INFO # DEBUG, INFO, WARNING, ERROR, CRITICAL
  format: '%(asctime)s - %(levelname)s - %(message)s'
  file:
    enabled: false
    path: 'logs/app.log'
    max_size: 10485760 # 10MB
    backup_count: 5
    format: 'json'
```

### Webhook

```yaml
webhook:
  rate_limit:
    requests_per_minute: 60
    burst_size: 10
```

### Users

```yaml
users:
  your_username:
    tvtime:
      username: 'your-email@example.com'
      password: 'your-password'
    tracktv:
      client_id: 'your-client-id'
      client_secret: 'your-client-secret'
      code: 'your-auth-code'
      redirect_uri: 'http://127.0.0.1:5000'
```

> [!IMPORTANT]
> `your_username` is your Plex's username and is case-sensitive.

### Retry

```yaml
retry:
  max_retries: 3
  initial_delay: 1
  max_delay: 10
  backoff_factor: 2
  jitter: 0.1
```

## Usage

1. Start the application:

```bash
python -m app.main
```

2. Configure Plex to send webhooks to `http://your-server:5000/webhook/plex`

3. Watch content on Plex, and it will be automatically marked as watched on TVTime and Trakt.tv

## Docker

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

## Development

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

5. Check test coverage:

```bash
pytest --cov=app tests/
```

## TODO

- [ ] Jellyfin support
- [ ] Emby support
- [ ] Database storage for settings
- [ ] Web management interface

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
