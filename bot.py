import telebot
import pandas as pd
from telebot import types
from datetime import datetime

bot = telebot.TeleBot('1488365371:AAGjBymYkkCYJxWSdDeAD63PQa7ps_LjcfI')
#создать датафрейм
# df = pd.DataFrame(columns=["user_id",'date', "name","group","sex","attendance"])
students = pd.read_csv('students.csv', index_col='user_id')
df = pd.read_csv('attendance.csv', index_col='id')
#создаем словарь для записи человека
row = {}
student = {}
today = datetime.today().strftime('%d-%m-%Y')


@bot.message_handler(content_types=['text'])
def start_message(message):
    global student, row, df
    today = datetime.today().strftime('%d-%m-%Y')
    if 'привет' in message.text.lower():
    # записываем идентификатор пользователя и дату заполнения
        row[message.from_user.id] = {"id": len(df)-1, "user_id": message.from_user.id, "date": today}

        # проверяем есть ли пользователь в файле со списком студентов (датафрейм students)
        if message.from_user.id in students.index:
            student[message.from_user.id] = students.loc[message.from_user.id].to_dict()
            student[message.from_user.id]['user_id'] = message.from_user.id
            bot.send_message(message.chat.id, f'Привет, { student[message.from_user.id]["name"] }!')
            # проверяем отвечал ли он сегодня
            query = df.loc[(df['user_id'] == message.from_user.id) & (df['date'] == today)]
            if len(query) == 0:
                # ответа еще нет, значит спрашиваем придет ли на занятие
                ask_attendance(message)
            else:
                row[message.from_user.id] = df.loc[query.index[0]].to_dict()
                row[message.from_user.id]['id'] = query.index[0]
                if row[message.from_user.id]['attendance'] == 'Да':
                    bot.send_message(message.chat.id, 'Жду тебя сегодня на занятии.')
                else:
                    bot.send_message(message.chat.id, 'Ты сказал, что не сможешь сегодня.')
                # уточнение что придет
                markup = types.ReplyKeyboardMarkup()
                markup.row('Я сегодня буду', 'Сегодня не получится :(')
                bot.send_message(message.chat.id, "Или что-то поменялось?", reply_markup=markup)
                bot.register_next_step_handler(message, change_answer)
        else:
            student[message.from_user.id] = {"user_id": message.from_user.id}
            # приветствие
            bot.send_message(message.chat.id, f'Привет, {message.from_user.first_name}!')
            # уточнение имени
            markup = types.ReplyKeyboardMarkup()
            markup.row('Да', 'Нет, это не мое имя')
            bot.send_message(message.chat.id, "Я могу к тебе так обращаться?", reply_markup=markup)
            # передача обработки ответа пользователя на функцию check_name
            bot.register_next_step_handler(message, check_name)
    elif message.text.lower() == 'пока':
        bot.send_message(message.chat.id, f'Прощай,{message.from_user.first_name}')
    elif message.text.lower() == 'покажи сводку':
        count_attendance(message)


def count_attendance(message):
    today = df["date"] == datetime.today().strftime('%d-%m-%Y')
    guys = df["sex"] == "Мужчина"
    girls = df["sex"] == "Женщина"
    group19 = df["group"] == "19:00"
    group20 = df['group'] == '20:30'
    attendance_yes = df["attendance"] == "Да"
    count1 = len(df[girls & today & group19 & attendance_yes])
    count2 = len(df[guys & today & group19 & attendance_yes])
    count3 = len(df[girls & today & group20 & attendance_yes])
    count4 = len(df[guys & today & group20 & attendance_yes])
    bot.send_message(message.chat.id, f'Группа на 19:00\nВсего ответили: {len(df[today & group19])}\n'
                                      f'Девочек будет, {count1}\n'
                                      f'Мальчиков будет, {count2}')
    bot.send_message(message.chat.id, f'Группа на 20:30\nВсего ответили: {len(df[today & group20])}\n'
                                      f'Девочек будет, {count3}\n'
                                      f'Мальчиков будет, {count4}')

def check_name(message):
    keyboard_hider = types.ReplyKeyboardRemove()
    if message.text == 'Да':
        bot.send_message(message.chat.id, f"Хорошо", reply_markup=keyboard_hider)
        student[message.from_user.id]['name'] = message.from_user.first_name
        ask_group(message)
    else:
        bot.send_message(message.chat.id, "А как тебя зовут?", reply_markup=keyboard_hider)
        bot.register_next_step_handler(message, get_name)


# получаем имя
def get_name(message):
    student[message.from_user.id]['name'] = message.text
    ask_group(message)

def ask_group(message):
    markup = types.ReplyKeyboardMarkup()
    markup.row('19:00', '20:30')
    bot.send_message(message.chat.id, "Из какой ты группы?", reply_markup=markup)

    bot.register_next_step_handler(message, get_group)


# получаем группу
def get_group(message):
    student[message.from_user.id]['group'] = message.text  # запоминаем группу

    keyboard_hider = types.ReplyKeyboardRemove()
    if message.text == '19:00':
        bot.send_message(message.chat.id, "Я понял, ты из Конкурсной группы Роста и Тани :)",
                         reply_markup=keyboard_hider)
    elif message.text == '20:30':
        bot.send_message(message.chat.id, "Я понял, ты из продолжающей (2-4 мес) группы Роста и Тани :)",
                         reply_markup=keyboard_hider)
    # задаем следующий вопрос
    ask_gender(message)

def ask_gender(message):
    markup = types.ReplyKeyboardMarkup()
    markup.row('Мужчина', 'Женщина')
    bot.send_message(message.chat.id, "Какого ты пола?", reply_markup=markup)
    # передаем обработку последующего ответа на функцию get_gender
    bot.register_next_step_handler(message, get_gender)

# узнаем пол
def get_gender(message):
    student[message.from_user.id]['sex'] = message.text

    # добавляем в список учеников
    students.loc[message.from_user.id] = student[message.from_user.id]
    students.to_csv('students.csv')

    keyboard_hider = types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, "Окей", reply_markup=keyboard_hider)
    # следующий вопрос - придет ли на занятие
    ask_attendance(message)


def ask_attendance(message):
    markup = types.ReplyKeyboardMarkup()
    markup.row('Да', 'Нет')
    bot.send_message(message.chat.id, "Ты придешь сегодня на занятие?", reply_markup=markup)
    # передаем обработку последующего ответа на функцию reply_attendance
    bot.register_next_step_handler(message, reply_attendance)


def reply_attendance(message):
    keyboard_hider = types.ReplyKeyboardRemove()
    if message.text == 'Да':
        bot.send_message(message.chat.id, "Ура, я тебя записал! До встречи на тренировке! :)",
                         reply_markup=keyboard_hider)
        bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAAJbzl-1divCTLXWKLuOCVn7tMd5i0LrAAKtBQACP5XMClctUSf4nRWyHgQ')
    else:
        bot.send_message(message.chat.id, "Очень жаль :( Надеемся увидеть тебя в следующий раз! ",
                         reply_markup=keyboard_hider)
        bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAAJb0V-1doSaMrc_7iN7T8y-bqZQfTmkAAKABQACP5XMCsWklcbe09p0HgQ')

    # передаем обработку последующего ответа на функцию save_attendance
    save_attendance(message)

def save_attendance(message):
    global student, row, df
    row[message.from_user.id]['attendance'] = message.text
    row[message.from_user.id].update(student[message.from_user.id])
    df.loc[len(df)] = row[message.from_user.id]
    df.to_csv('attendance.csv')


def change_answer(message):
    keyboard_hider = types.ReplyKeyboardRemove()
    if message.text == 'Я сегодня буду':
        bot.send_message(message.chat.id, "Отлично! До встречи на тренировке! :)",
                         reply_markup=keyboard_hider)
        bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAAJbzl-1divCTLXWKLuOCVn7tMd5i0LrAAKtBQACP5XMClctUSf4nRWyHgQ')
        df.at[row[message.from_user.id]['id'], 'attendance'] = "Да"
    elif message.text == 'Сегодня не получится :(':
        bot.send_message(message.chat.id, "Очень жаль :( Надеемся увидеть тебя в следующий раз! ",
                         reply_markup=keyboard_hider)
        bot.send_sticker(message.chat.id, 'CAACAgIAAxkBAAJb0V-1doSaMrc_7iN7T8y-bqZQfTmkAAKABQACP5XMCsWklcbe09p0HgQ')
        df.at[row[message.from_user.id]['id'], 'attendance'] = "Нет"
    df.to_csv('attendance.csv')



bot.polling(none_stop=True, interval=0)