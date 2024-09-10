# Intania 92 Runner Bot
![Test and Release](https://github.com/naveen-pit/intania92-runner-bot/actions/workflows/python-test-and-release.yaml/badge.svg) ![Known Vulnerabilities](https://snyk.io/test/github/naveen-pit/intania-92-runner-bot/badge.svg) [![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=naveen-pit_intania92-runner-bot&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=naveen-pit_intania92-runner-bot) [![Coverage](https://sonarcloud.io/api/project_badges/measure?project=naveen-pit_intania92-runner-bot&metric=coverage)](https://sonarcloud.io/summary/new_code?id=naveen-pit_intania92-runner-bot)


LINE Bot for tracking running distance leaderboard in LINE group


## Overview
This project is a LINE Bot designed to facilitate a running challenge leaderboard among participants on LINE platform. The bot allows users to submit their running distances, updates a leaderboard, and handles image-based distance submissions through OCR algorithm. It is built using Flask, Google Cloud Firestore, and LINE Messaging API.



```mermaid
flowchart LR
    A[LINE Client]
    B[Google Cloud Functions]
    C[Google Cloud Firestore]

    A --> |HTTP Request & Webhook Events| B
    B --> |Store & Retrieve Leaderboard Data| C
    B --> |Send Response| A

    classDef default fill:#fff,stroke:#000,stroke-width:2px;
    class A,B,C default;
```

## Features
- **Text-Based Leaderboard Management:** Users can update their running distances via text messages. The bot parses the messages and updates the leaderboard accordingly.
- **Image-Based Distance Submission:** Users can submit images containing their running distances. The bot extracts the distance using OCR algorithm and updates the leaderboard.
- **Multi-Image Support:** The bot handles multi-image submissions, aggregating the distances before updating the leaderboard.
- **User Identification:** Users are identified by their submitted names, which are extracted from the sent messages. The bot automatically updates the user's name upon submission if needed.
- **Google Cloud Firestore Integration:** All leaderboard data and user information are stored and managed using Firestore.

# Project Structure
```plaintext
.
├── main.py               # Main entry point for the application
├── cloud_interface.py    # Interfaces for handling google cloud operations
├── config.py             # Configuration file for setting up project-specific settings
├── google_cloud.py       # Google Cloud Firestore and Secret client setup
├── ocr.py                # Handle distance extraction from the image using OCR algorithm
├── utils.py              # Utility functions
├── cloudbuild.yaml       # Google Cloud Build configuration for deployment
├── Makefile              # Makefile for setting up and running the project
└── README.md             # Project documentation
```

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/line-bot-leaderboard.git
```

2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Set up your environment variables by creating a `.env` file in the project root or setting the environment variables directly. The variables are prefixed with `LINEBOT_` and include:

- `LINEBOT_LINE_CHANNEL_SECRET_KEY`
- `LINEBOT_LINE_ACCESS_TOKEN`
- `LINEBOT_PROJECT_ID`

Example `.env` file:

```env
LINEBOT_LINE_CHANNEL_SECRET_KEY="your_secret_key"
LINEBOT_LINE_ACCESS_TOKEN="your_access_token"
LINEBOT_PROJECT_ID="your_project_id"
```

## Configuration
The configuration is managed through the config.py file using Pydantic settings. The RunSetting class in this file allows for easy configuration of all the parameters required by the bot.

**Configuration Fields**
- **line_channel_secret_key:** The secret key for the LINE channel.
- **line_access_token:** The access token for the LINE bot.
- **firestore_database:** The Firestore database name for storing leaderboard data.
- **firestore_leaderboard_collection:** The Firestore collection name for the leaderboard.
- **project_id:** The Google Cloud Project ID. If not specified, it will attempt to use the default project ID - associated with your Google Cloud credentials.

## Deployment
### Deploying to Google Cloud Functions
This project includes a cloudbuild.yaml file that automates the deployment process to Google Cloud Functions. To deploy, follow these steps:

1. Ensure you have the Google Cloud SDK installed and authenticated to your project.

2. Use the following command to trigger a deployment:

```bash
gcloud builds submit --config cloudbuild.yaml
```
3. Ensure following permission are granted
- allUsers are accessible the cloud function with `Cloud Functions Invoker` role.
- Service account of the cloud function has granted to Firebase

The `cloudbuild.yaml` file is configured to deploy the function to the `asia-southeast1` region, use Python 3.12 runtime, and set the necessary secrets for LINE API integration.

## Cloud Build Configuration (cloudbuild.yaml)
```yaml
steps:
- name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
  args:
  - gcloud
  - functions
  - deploy
  - intania92-runner-bot
  - --no-gen2
  - --region=asia-southeast1
  - --trigger-http
  - --source=running_bot/.
  - --entry-point=reply
  - --memory=2GB
  - --runtime=python311
  - --set-secrets=LINEBOT_LINE_ACCESS_TOKEN=line-channel-access-token:latest,LINEBOT_LINE_CHANNEL_SECRET_KEY=line-channel-secret:latest
options:
  logging: CLOUD_LOGGING_ONLY
```
This configuration deploys the function with the specified settings and secrets.

## Development
### Setting Up the Project Locally
This project uses `Poetry` for dependency management and includes a `Makefile` for setup and running the project.

**Installing Poetry**
To install Poetry and set up the project:

```bash
make install_poetry_zsh
```
This command installs Poetry, configures shell completions for Zsh, and verifies the installation.

**Linting and Testing**
To lint the code and run tests:

```bash
make lint
make test
```

The `lint` target runs `black`, `ruff`, and `mypy` to check code formatting, linting, and type checking. The `test` target runs tests using pytest with coverage reporting.

**Running Locally**
To run the project locally for development:

```bash
make run_local
```
This command starts the Flask development server on port 8000.

If you want to expose your local development server for external access (e.g., for testing with the LINE webhook), you can use ngrok:

```bash
make ngrok
```

## How to use
This project provides a chatbot that integrates with the LINE messaging platform. The bot allows users to interact with a leaderboard system, primarily focused on tracking distances for a running challenge. Below are the steps and commands for chatting with the bot.

### Add the Bot to a Chat
Ensure the bot is added to your LINE group, room, or as a 1-on-1 chat with the bot.
To do this, scan the following QR code or add the LINE id `@swg8094d`

<img src="./images/linebot_qr.png" alt="linebot qr code" width="200" height="200"/>

### Quick Start

You can quickly start using the bot by sending a message in the format `<Name>+<Distance>` (your name should not contain space). The bot will automatically create and maintain the leaderboard for you.

#### Steps:
1. **Input Your Distance:**
   - **Format:** `<Name>+<Distance>`
   - **Example:** `Alice+3.5`
   - This will initialize the leaderboard with a default title ("Running Challenge") and the current month as the subtitle, adding your distance to the leaderboard.

2. **View the Leaderboard:**
   - After adding your distance, you can view the updated leaderboard by simply checking the bot response:
   - **Example:**
   ```
   ===Running Challenge===
   August 2024
   1 Alice 3.5 km
   ```
3. Note that the leaderboard resets monthly when the subtitle is set to the full month name followed by the year (e.g., August 2024). Rename the subtitle if a reset is not needed.

### Features

**Add/Update Distance**
- Format: `<Name>+<Distance>`
- Example: `John+5.2`
- This will add the distance associated with your name on the leaderboard.

You can add as many distances as you need, as long as distance are numbers.
- Format: `<Name>+<Distance>+<Distance>+...`
- Example: `John+5.2+2+4`
- This will sum and update the distances associated with your name on the leaderboard.

**Subtract Distance**

To subtract distance, use a negative sign in the message.
- Format: `<Name>-<Distance>`
- Example: `John-5.2`
- This will subtract the specified distance from your total on the leaderboard.
- Users whose total distance is ≤ 0 will be removed from the leaderboard.

You can subtract multiple distances in one message.
- Format: `<Name>-<Distance>-<Distance>+...`
- Example: `John-5.2-2-4`
- This will subtract the distances from your total on the leaderboard, removing users with a total distance ≤ 0.

**Register Name**
- When adding or subtracting a distance using the format `<Name>+<Distance>` or `<Name>-<Distance>`, the bot also registers the submitted name in a database.
- Only the most recently submitted name will be registered.
- The registered name will be used for future image submissions, allowing the bot to automatically update the leaderboard without requiring manual entry.

**Change Your Name**
- To change your name without affecting the leaderboard, you can submit your name with 0 distance.
- Format: `<Name>+0`
- Example: `Mary+0`

**Image Submission**
- This feature is only available to users who have previously updated their distance to the leaderboard. Simply send an image to the chat, and the bot will automatically detect the distance in the image using an OCR algorithm and update the leaderboard with the associated name.
- The bot supports both single and multiple image submissions.

NOTE: While the OCR algorithm generally works well with screenshots from fitness tracking apps, its accuracy may be lower for photos taken with a camera, or texts overlaid on photos.


**Update the Leaderboard**
- Format: Start your message with === followed by the leaderboard title and subtitle on the next lines.
- Example:
```
===YOUR TITLE===
YOUR SUBTITLE
```

This will initialize or update the leaderboard with the specified title and subtitle.

- If the leaderboard already has data, you can copy the existing leaderboard, edit the title, subtitle, name, and distances, and send the updated message in the chat.
- Example: For a current leaderboard,
```
===Running Challenge===
August 2024
1 John 10 km
2 May 2 km
```

You can copy the current leaderboard, edit the title, subtitle, rename users, adjust distances, and send the message in chat. For example, renaming the title to `Running Go Go`, changing the subtitle to `Week1`, renaming `May` to `Mary`, and setting her distance to `12` km:
```
===Running Go Go===
Week1
1 John 10 km
2 Mary 12 km
```

The bot will update the title, subtitle, usernames, and re-rank the users by distance.

Bot response:
```
===Running Go Go===
Week1
1 Mary 12 km
2 John 10 km
```
NOTE: Once you change the subtitle apart from full month name followed by the year (e.g., August 2024), the bot will no longer reset the leaderboard monthly.
