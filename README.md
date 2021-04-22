# soundStorage
Sound Storage - это сайт для хранения и распространения различных аудиозаписей, разработанный учениками Яндекс.Лицея Абраменко Александром и Шангараевым Владимиром в рамках проекта "WebServer+API". Мы представляем следующую функциональность
1) Регистрация и авторизация пользователей, разделение доступа
2) Зарегистрированный пользователь может загружать/удалять свои звуки и редактировать информацию своего профиля
3) Возможность скачивать звуки, а также оставлять комментарии
4) Делать поиск по звукам по названию и тэгам
5) Использовать свободное API
### Использованные технологии
Flask для самого сервера

SQLAlchemy для работы с базой данных

WTForms для создания и обработки форм

alembic для управления базой данных


### API
(Все параметры передаются в json запроса)

*   /api/auth/register

Метод: **POST**. Регистрация. Обязательные параметры тела запроса: **nickname, email, password**. Необязательные: **profile_description**. Возвращает id созданного пользователя

*   /api/auth/login

Метод: **POST**. Авторизация. Параметры: **email, password**. При успешной авторизации возвращает токен, его необходимо сохранить. Токен действует 7 дней после его получения. Для использования методов, требующих авторизации, в заголовках запроса необходимо указывать `'Authorization': 'Bearer *your_token*'`

*   /api/id

Метод: **GET**. Возвращает id всех звуков. Необязательные параметры в теле запроса: **soundname, searchtype('title', 'tag')**. Без параметров возращает айди всех звуков.

*   /api/sound/int:sound_id

Методы: **GET, DELETE, PUT**. Удалять может только автор, соответственно. DELETE, PUT **требуют авторизацию.**

*   /api/user/int:user_id

Метод: **GET**. Возвращает данные о пользователе, включая аватар. Пример получения аватарки:  
```from requests import get  
from PIL import Image  
import base64  
from io import BytesIO  

response = get('http://soundstorage.herokuapp.com/api/user/1')  
content = response.json()  
s = base64.decodebytes((bytes(content['image'], encoding='utf-8')))  
Image.open(BytesIO(s)).show()
```
Метод: **PUT**. Изменяет информацию о пользователе. **Требует авторизацию.** Параметры: **nickname, profile_description, email, password, picture, delete_picture.**  
picture - Это словарь с двумя ключами: filename(название файла) и content(данные о фото). delete_picture(True, False) - удалить ли существующую фотографию. delete_picture и picture **не могут быть в одном запросе**. Пример загрузки фото:  
```import base64  
import requests  
with open('photo.jpg', mode='rb') as file:  
img = file.read()  
res = base64.encodebytes(img).decode('utf-8')  
token = 'your_token'  
a = requests.put('http://soundstorage.herokuapp.com/api/user/1', json={"picture": {"filename": "a.jpg", "content":  
res}}, headers={'Authorization': 'Bearer ' + token})  
```

Метод: **DELETE**. Удаление профиля человека. **Требует авторизацию.**

*   /api/comments

Метод: **POST**. Пост комментария. Обязательные параметры тела запроса: **content, sound_id**. Где content - сам комментарий. **Требует авторизацию.**

Метод: **GET**. Получает все комментарии

*   /api/comments/int:comment_id

Метод: **GET**. Получает комментарий по заданному id

*   /api/sounds/int:sound_id/download

Метод: **GET**. Возвращает звук в байтовом представлении, закодированном в base64\. **Требует авторизацию.**

*   /api/sounds/

Метод: **POST**. Загружает звук на сервер. Обязательные параметры тела запроса: **filename, title, description, content**. Content должен представлять из себя байтовую строку mp3 или wav файла, закодированную в base64. **Требует авторизацию**
```
from requests import post  
import base64  

with open('example.wav', mode='rb') as file:  
  s = file.read()  
s1 = base64.encodebytes(s).decode('utf-8')  
dct = dict()  
dct['content'] = s1  
dct['title'] = 'title'  
dct['filename'] = 'example.wav'  
dct['description'] = 'desc'  

response = post('http://soundstorage.herokuapp.com/api/sounds', json=dct,  
headers={'x-access-tokens': 'TOKEN',  
'Content-Type': 'application/json'})  
```

### Архитектура
main.py - основной файл сервера, в котором происходит обработка всех запросов

alembic - папка, необходимая для работы alembic

data - основные классы программы (такие как пользователь, звук, т.д)

db - база данных

forms - формы, используемые на сайте

static/images - фотографии, хранимые сервером. В основном фотографии профиля пользователей

static/sounds - звуки, загруженные пользователями

static/css - стили сайта

templates - html, внешний вид
 