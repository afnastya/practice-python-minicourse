# код веб-скрапинга, с помощью которого были получены все таблицы в csv файлах в этом проекте

import requests
from bs4 import BeautifulSoup
import pandas as pd

url = 'https://briefly.ru'

responce = requests.get(url + '/authors/')
soup = BeautifulSoup(responce.content, 'html.parser')

authors_html_block = soup.find('div', 'alphabetic-index')
authors = authors_html_block.find_all('a')

authors_codes2names = dict()
author_codes = []

for author in authors:
    if 'surnames' not in author['href']:
        author_codes.append(author['href'])
        authors_codes2names[author['href']] = author.text
        continue
    
    surnames_responce = requests.get(url + author['href'])
    surnames_soup = BeautifulSoup(surnames_responce.content, 'html.parser')
    
    for author_html_block in surnames_soup.find_all('div', 'author'):
        author_code = author_html_block.find('a')['href']
        author_codes.append(author_code)
        authors_codes2names[author_code] = author.text

# блок c скрапингом сайта может работать до 5 - 10 минут
main_tags = []
book_titles = []
book_authors = []
book_years = []
book_tags = []
book_summary_urls = []
book_original_urls = []
book_texts = []

for author_code in author_codes:
    print(author_code)

    author_responce = requests.get(url + author_code)
    author_soup = BeautifulSoup(author_responce.content, 'html.parser')

    author_name = author_soup.find(
        'span',
        'author_name normal' if author_soup.find('span', 'author_name normal') else 'author_name long'
    ).text.replace('\xa0', ' ')

    tags = [tag.text.replace('\xa0', ' ') for tag in author_soup.find('ol', 'breadcrumbs-compact').find_all('span')]
    main_tags.append(tags[0])

    # если у автора нет книг
    if author_soup.find('section', "author_works").find('div', 'noworks'):
        continue

    # определяем есть ли на странице блок "все пересказы по алфавиту"
    if author_soup.find('section', "works_index"):
        has_works_index_section = True
        book_html_blocks = author_soup.find('section', "works_index").find_all('li')
    else:
        has_works_index_section = False
        book_html_blocks = author_soup.find('section', 'author_works').find_all('div', 'w-featured')

    # перебираем все книги автора
    for book_html_block in book_html_blocks:
        if "requested" in book_html_block['class'] or "pending" in book_html_block['class']:
            continue
        
        book_code = book_html_block.find('a')['href']

        # переходим на суп страницы с книгой
        book_responce = requests.get(url + book_code)
        book_soup = BeautifulSoup(book_responce.content, 'html.parser')

        # парсим краткое содержание
        book_paragraphs = []
        if book_soup.find('p', 'microsummary'):
            book_paragraphs.append(book_soup.find('p', 'microsummary').get_text())
        book_paragraphs.extend([paragraph.text for paragraph in book_soup.find('div', id='text').find_all(
            ['h2', 'h3', 'p', 'blockquote', 'li']
        )])
        text = '\n'.join(book_paragraphs).replace('\xad', '').replace('\xa0', ' ')
        book_texts.append(text)
        
        # добавляем всю остальную информации по книге
        book_tag = book_soup.find('div', 'breadcrumb__content').text.replace('\xa0', ' ')
        main_tags.append(book_tag)
        book_tags.append(', '.join(tags + [book_tag]))
        book_authors.append(author_name)
        book_years.append(book_soup.find('span', 'date').text if book_soup.find('span', 'date') else None)
        book_summary_urls.append(url + book_code)
        book_original_urls.append(book_soup.find('div', 'readingtime').find('a')['href']
                                  if book_soup.find('div', 'readingtime').find('a')
                                  else None)
        book_titles.append(book_html_block.find('a').text.replace('\xa0', ' ')
                           if has_works_index_section
                           else book_html_block.find('div', 'w-title').text.replace('\xa0', ' '))

books_table = pd.DataFrame(
    {
        "title": book_titles,
        "author": book_authors,
        "year": book_years,
        "tags": book_tags,
        "summary": book_texts,
        "summary url": book_summary_urls,
        "original url": book_original_urls
    }
)

tags_table = pd.DataFrame({"tag": sorted(list(set(main_tags)))})
tags_table = tags_table[tags_table.apply(
    lambda row: 'Проч' not in row['tag'],
    axis=1
)]
tags_table.to_csv('tags_table.csv', encoding='utf-8', index=False)

books_table.to_csv('books_table.csv', encoding='utf-8', index=False)
