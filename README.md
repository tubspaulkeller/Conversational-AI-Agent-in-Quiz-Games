# Pedagogical Conversational Agent Ben moderates Quiz-Game in Telegram

## Description
Chatbot integrated into a quiz game in Telegram, where users can play solo, in teams, or compete against each other in teams.

## Participant 
Paul Keller 

## Course 
Master-Thesis at TU Braunschweig submitted on 12/15/2023

## Stack:
- Python
- Rasa
- LLM (OpenAI)
- MongoDB
- Telegram
- Docker

### Abstract 

The interaction among learners plays a crucial role in the learning process as it fosters a sense of community and can generate positive relational effects. However, there is often a lack of motivation in collaborative environments, affecting collaboration. Nevertheless, gamified elements can be integrated into the collaborative process. Pedagogical Conversational Agents (PCAs) take on a guiding and moderating role to support learners and effectively control gamified elements. This work focuses on a gamified PCA named Ben, who acts as a moderator for a quiz game and a motivator. Ben offers various game modes for individual and group learning: solitary learning (OKK), collaborative learning (KL), competitive learning without collaboration (KLOK), and competitive learning with collaboration (KLMK). The goal was to determine which mode most positively influences learner's motivation. The study was conducted as part of Design Science Research through a 2x2 experiment (n=120). Significant differences between competitive game modes (KLMK & KLOK) were found using a two-factor ANOVA. Additionally, a structural equation model highlighted significant direct effects of the KLMK mode on learner's intrinsic motivation and the perceived helpfulness of the gamified PCA (Ben). On the other hand, the model revealed significant indirect effects of the KLMK mode. These effects relate to both learner's enjoyment & satisfaction and the perceived utility of competitive & collaborative gamified PCA interaction, with intrinsic motivation serving as a mediator in both cases. 
The following video (in German) will show the different play modes.

https://github.com/tubspaulkeller/PCA-Ben/assets/102319452/87f42add-d023-4312-b46a-c41c9a3290ad

You can play the solo play mode by scanning the following QR code. You will need a Telegram account. The game will be in German.

![PCA_BEN_BOT_QR](https://github.com/tubspaulkeller/PCA-Ben/assets/102319452/c3311aa7-cfcf-4894-84af-74e8a7c86c26)

## Prerequisites
- Rasa 
- MongoDB 
- MongoDB-GUI 
- NGROK
- Telethon-Account 
- Telegram-Account 
- OpenAI-Account
- Bot in Telegram (Botfather)

## Requirements
- rasa==3.1
- telethon==1.28.5
- pyTelegramBotAPI==4.12.
- python-telegram-bot==20.3
- motor==3.1.2
- python-dotenv==1.0.0
- pymongo==4.4.0 
- asyncio==3.4.3
- pillow==10.0.0
- openai==0.27.8
- sqlalchemy<2.0

## Environments 
Create a .env file with the following variables: 
- DB_NAME = <DB_NAME>
- API_ID = <API_ID_TELETHON>
- API_HASH = <API_HASH_TELETHON>
- PHONE_NUMBER = <YOUR_PHONE_NUMBER_TELETHON>
- SESSION_STRING = <SESSION_STRING_TELETHON>
- OPEN_AI = <OPEN_AI_ACCOUNT>
- MONGO_DB_LOCAL = <MONGO_DB_LOCAL>
- BOT_NAME = <BOT_NAME>
- <GROUP_1_CHANNEL_ID> = <GROUP_2_CHANNEL_ID>
- TELEGRAM_ACCESS_TOKEN = <TELEGRAM_ACCECSS_TOKEN_BOT>
- TELEGRAM_URL = <TELEGRAM_URL> 
- <GROUP_1_CHANNEL_ID>_TELEGRAM_INVITE_LINK = 'https://t.me/<GROUP_1_CHANNEL_NAME>'
- <GROUP_2_CHANNEL_ID>_TELEGRAM_INVITE_LINK = 'https://t.me/<GROUP_2_CHANNEL_NAME>'
- WAITING_COUNTDOWN = 60 
- COMPETITION_REMINDER = 2
- DELAY = 5 
- INTERVAL = 10 
- REMINDER_DELAY = 2
- OPEN_QUEST_TIME = 90
- OPEN_QUEST_PENALTY = 5
- BUTTON_QUEST_TIME = 30
- BUTTON_QUEST_PENALTY = 2
- RANK_LIST = 3
- MAX_LINE_LENGTH = 30
- FIRST_CORRECT_THRESHOLD = 1 
- COLLABORATION_THRESHOLD = 2
- IN_TIME_THRESHOLD = 5 # 3
- SINGLE_CHOICE_THRESHOLD = 2 
- MULTIPLE_CHOICE_THRESHOLD = 2 
- OFFENE_FRAGE_THRESHOLD = 2 
- MAX_LEVEL = 4 
- LAST_SLOT = -1 
- MAX_POINTS = 60


## Installation 

- Install Rasa: Follow the steps at [Rasa Documentation](https://rasa.com/docs/rasa/2.x/installation/).
- Install dependent packages using: `pip install -r /Conversational-AI-Agent-in-Quiz-Games/actions/requirements.txt`.
- Install MongoDB and MongoDBCompass (GUI).
- Install NGROK from: [NGROK Download](https://ngrok.com/download).
  
### MongoDB:

First, populate the database with quiz questions and answers.
1. Open a terminal.
2. Navigate to the directory `/Master-Thesis/MongoDB-Dump` in the repository.
3. Run the command: `mongoimport --db rasa_ben`.
4. Update the connection string under `/Conversational-AI-Agent-in-Quiz-Games/.env` for the variable `MONGO_DB_LOCAL`.

### NGROK:

For HTTPS connection between Telegram and Rasa, use NGROK.
1. Open a terminal.
2. Run: `ngrok http 5005`.
Under Forwarding, note the URL ending with ngrok-free.app for further steps.

### RASA:
Next, open two additional terminal windows. Activate the Rasa environment in both terminals from installation. After that, in both terminals, navigate to the directory containing the source code: `/Conversational-AI-Agent-in-Quiz-Games`.

1. If no model exists, run the following command in one terminal: 
    ```bash
    rasa train
    ```

2. Next, insert the NGROK URL into the file `/Conversational-AI-Agent-in-Quiz-Games/credentials.yml` in the format: `"NGROK-URL/webhooks/telegram/webhook"` for the `webhook_url`.

Afterward, execute the following commands:

### Terminal 2:

```bash
rasa run –connector addons.custom_channel.MyIO –debug
 ```
### Terminal 3:
  ```bash
rasa run actions
 ```





