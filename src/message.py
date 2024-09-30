# Queues to store messages
user_message_queue = []
bot_message_queue = []

def send_user_message(message):
    user_message_queue.append(message)

def send_bot_message(message):
    bot_message_queue.append(message)