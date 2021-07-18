#! /usr/bin/env python
# -*- coding: utf-8 -*-

import telebot
from telebot import types
import pandas as pd
import requests

telegram_token = '{your_token}'

bot = telebot.TeleBot(telegram_token)


class RandomChooser:
    def __init__(self, data):
        self.data = data

    @staticmethod
    def from_csv(csv):
        return RandomChooser(pd.read_csv(csv))

    def __call__(self, author=None, tag=None):
        if author is not None:
            author_chunks = author.split()
            result_dataframe = self.data[self.data.apply(
                lambda row: all([chunk.lower() in row['author'].lower().split() for chunk in author_chunks]),
                axis=1
            )]
            return result_dataframe.sample(1).iloc[0] if not result_dataframe.empty else None
        elif tag is not None:
            result_dataframe = self.data[self.data.apply(
                lambda row: tag in row['tags'],
                axis=1
            )]
            return result_dataframe.sample(1).iloc[0] if not result_dataframe.empty else None
        else:
            return self.data.sample(1).iloc[0]


rc = RandomChooser.from_csv('books_table.csv')
tags = pd.read_csv('tags_table.csv')


@bot.message_handler(commands=['start'])
def say_hello(message):
    hello_msg = bot.send_message(
        message.chat.id,
        "Привет! Я чат-бот и я могу:\n"
        "- помочь тебе выбрать книгу\n"
        "- прочесть тебе краткое содержание\n"
        "Выбери, что ты хочешь, с помощью появившихся кнопок",
        reply_markup=create_menu()
    )
    bot.register_next_step_handler(hello_msg, process_menu)


# следующие 2 функции - реализация меню
def create_menu():
    return create_reply_keyboard([['Выбрать рандомную книгу', 'Прочесть краткое содержание']])


@bot.message_handler(func=lambda msg: True, content_types=['text'])
def process_menu(message):
    if message.text == 'Выбрать рандомную книгу':
        random_choose(message.chat.id)
    elif message.text == 'Прочесть краткое содержание':
        audio_summary(message.chat.id)


# клавиатура с кнопками по списку списков надписей на кнопках
def create_reply_keyboard(button_rows):
    markup = types.ReplyKeyboardMarkup()
    for row in button_rows:
        row = [types.KeyboardButton(button) for button in row]
        markup.row(*row)
    return markup


# следующие 5 функций - реализация "Выбрать рандомную книгу"
def random_choose(chat_id):
    category_markup = create_reply_keyboard([['нет', 'по автору', 'по тэгу']])
    msg = bot.send_message(
        chat_id,
        "Хочешь я выберу по какому-то параметру?",
        reply_markup=category_markup
    )
    bot.register_next_step_handler(msg, choose_category)


def choose_category(category_message):
    if category_message.text == 'нет':
        present_choice_msg(category_message.chat.id)
        print_book(category_message.chat.id, rc())
    elif category_message.text == 'по автору':
        bot.register_next_step_handler(
            bot.send_message(
                category_message.chat.id,
                "Какой автор тебя интересует?",
                reply_markup=types.ReplyKeyboardRemove(selective=False)
            ),
            choose_author
        )
    else:
        bot.register_next_step_handler(
            bot.send_message(
                category_message.chat.id,
                "Выбери интересующий тебя тэг",
                reply_markup=create_reply_keyboard([[tag] for tag in tags['tag']])
            ),
            choose_tag
        )


def choose_author(author_message):
    book = rc(author=author_message.text)
    if book is None:
        bot.register_next_step_handler(
            bot.send_message(
                author_message.chat.id,
                "Ошибка в имени автора или такого автора я не знаю. Попробуй ещё раз",
                reply_markup=types.ReplyKeyboardRemove(selective=False)
            ),
            choose_author
        )
    else:
        present_choice_msg(author_message.chat.id)
        print_book(author_message.chat.id, book)


def choose_tag(tag_message):
    book = rc(tag=tag_message.text)
    present_choice_msg(tag_message.chat.id)
    print_book(tag_message.chat.id, book)


def present_choice_msg(chat_id):
    return bot.send_message(
        chat_id,
        "Вот, что я подобрал для тебя:",
        reply_markup=types.ReplyKeyboardRemove(selective=False)
    )


# следующие 5 функций - реализация "Прочесть краткое содержание"
def audio_summary(chat_id):
    category_markup = create_reply_keyboard([['хочу рандомную', 'хочу конкретную']])
    msg = bot.send_message(
        chat_id,
        "Мне выбрать книгу рандомно или ты хочешь какую-то конкретную?",
        reply_markup=category_markup
    )
    bot.register_next_step_handler(msg, audio_category)


def audio_category(category_message):
    chat_id = category_message.chat.id
    if category_message.text == "хочу рандомную":
        book = rc()
        text = book['summary']
        parts_number = make_audio(text)

        while parts_number == 0:
            book = rc()
            text = book['summary']
            parts_number = make_audio(text)

        present_choice_msg(chat_id)
        print_book(chat_id, book)

        for i in range(parts_number):
            url = "https://api.telegram.org/bot{0}/sendVoice?chat_id={1}".format(telegram_token, chat_id)
            with open('speech{0}.ogg'.format(i), 'rb') as f:
                data = f.read()

            file = {'voice': ('Message.ogg', data)}
            requests.post(url, files=file)
    else:
        bot.register_next_step_handler(
            bot.send_message(
                chat_id,
                "Напиши полное название книги, которая тебя интересует",
                reply_markup=types.ReplyKeyboardRemove(selective=False)
            ),
            audio_book_choice
        )


def audio_book_choice(book_message):
    chat_id = book_message.chat.id
    result_dataframe = rc.data[rc.data.apply(
        lambda row: book_message.text.lower() == row['title'].lower(),
        axis=1
    )]
    if result_dataframe.empty:
        bot.register_next_step_handler(
            bot.send_message(
                chat_id,
                "К сожалению, я не знаю такой книги или ты ошибся в её названии:( Попробуй ещё раз"
            ),
            audio_book_choice
        )
    else:
        book = result_dataframe.iloc[0]
        text = book['summary']
        parts_number = make_audio(text)

        if parts_number == 0:
            bot.send_message(
                chat_id,
                "Для этой книги эта функция не поддерживается."
            )
        else:
            print_book(chat_id, book)
            for i in range(parts_number):
                url = 'https://api.telegram.org/bot{0}/sendVoice?chat_id={1}'.format(telegram_token, chat_id)
                with open('speech{0}.ogg'.format(i), 'rb') as f:
                    data = f.read()

                file = {'voice': ('Message.ogg', data)}
                requests.post(url, files=file)


def make_audio(text):
    ydx_token = '{your_yandex_token}'
    ydx_folder_id = '{your_yandex_folder}'

    url = 'https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize'
    headers = {
        'Authorization': 'Bearer ' + ydx_token,
    }

    parts = cut_text_into_chunks(text)

    for i in range(len(parts)):
        data = {
            'text': parts[i],
            'lang': 'ru-Ru',
            'voice': 'filipp',  # filipp, alena, jane, zahar
            'speed': '1.3',
            'folderId': ydx_folder_id
        }

        with requests.post(url, headers=headers, data=data, stream=True) as responce:
            if responce.status_code != 200:
                return 0

            with open('speech{0}.ogg'.format(i), "wb") as output_file:
                for chunk in responce.iter_content(chunk_size=None):
                    output_file.write(chunk)
    return len(parts)


# нужно порезать текст, так как у Yandex SpeechKit ограничение на 5000 символов
def cut_text_into_chunks(text):
    chunks = []

    start = 0
    for i in range(len(text) // 5000):
        end = start + text[start:start + 5000].rfind('\n') + 1
        chunks.append(text[start:end])
        start = end
    chunks.append(text[start:])
    return chunks


# поиск обложки книги с помошью Google Api
def search_cover(book):
    search_url = 'https://www.googleapis.com/customsearch/v1?'

    google_key = '{your_google_key}'
    cx = '9054c95a0ea83381f'
    q = "{0} {1} обложка книги".format(book['title'], book['author'])

    responce = requests.get(search_url + 'key=' + google_key + '&cx=' + cx
                            + '&imgSize=medium' + '&q=' + q + '&searchType=image')
    urls = []
    for item in responce.json()['items']:
        try:
            urls.append(item['link'])
        except:
            continue

    return urls[0]


# отправка сообщения с информацией о книге
def print_book(chat_id, book):
    try:
        bot.send_photo(chat_id, search_cover(book))
    except:
        pass

    text = "Название: {0}\nАвтор: {1}\n".format(book['title'], book['author'])
    text += "" if book.isna()['year'] else "Дата: {0}\n".format(book['year'])
    text += "Тэги: {0}\n".format(book['tags'])
    text += "Краткое содержание: {0}\n".format(book['summary url'])
    text += "" if book.isna()['original url'] else "Полная версия: {0}".format(book['original url'])

    bot.send_message(chat_id, text, disable_web_page_preview=True, reply_markup=create_menu())


bot.polling(none_stop=True)
