

def send_user_message(message, user_message_queue):
    user_message_queue.put(message)

def send_bot_message(message, bot_message_queue):
    bot_message_queue.put(message)
