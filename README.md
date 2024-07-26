# Яндекс Практикум, курс "Инженер Машинного Обучения" (2024 г.)
# Проект 4-го спринта: "Создание рекомендательной системы"
## Выполнил: Кирилл Н., email: ibnkir@yandex.ru, tg: [Xmg23](https://t.me/Xmg23)

## Описание проекта
Целью проекта является создание системы рекомендаций аудиотреков для
пользователей музыкального сервиса на основе их истории прослушиваний.
В рамках проекта был разработан пайплайн для расчета нескольких типов рекомендаций,
который был интегрирован в веб-сервис на базе FastAPI.

Основные инструменты и Python-библиотеки:
- Visual Studio Code,
- Jupyter Lab,
- implicit.ALS,
- S3,
- FastAPI, 
- uvicorn.

## Как воспользоваться репозиторием
1. Перейдите в домашнюю папку и склонируйте репозиторий на ваш компьютер
   ```bash
   cd ~
   git clone https://github.com/ibnkir/mle-recsys-project
   ```

2. Создайте виртуальное окружение и установите в него необходимые Python-пакеты
    ```
    python3 -m venv env_recsys_start
    . env_recsys_start/bin/activate
    pip install -r requirements.txt
    ```

3. Скачайте три файла с исходными данными в папку репозитория
    - Данные о треках - [tracks.parquet](https://storage.yandexcloud.net/mle-data/ym/tracks.parquet)
    - Имена артистов, названия альбомов, треков и жанров - [catalog_names.parquet](https://storage.yandexcloud.net/mle-data/ym/catalog_names.parquet)
    - Данные о том, какие пользователи прослушали тот или иной трек - [interactions.parquet](https://storage.yandexcloud.net/mle-data/ym/interactions.parquet)
 
    Для удобства можно воспользоваться командой wget:
    ```
    wget https://storage.yandexcloud.net/mle-data/ym/tracks.parquet
    wget https://storage.yandexcloud.net/mle-data/ym/catalog_names.parquet
    wget https://storage.yandexcloud.net/mle-data/ym/interactions.parquet
    ```

4. Запустите Jupyter Lab в командной строке
    ```
    jupyter lab --ip=0.0.0.0 --no-browser
    ```

    Чтобы не выполнять подготовительный код в Jupyter-ноутбуке и 
    сразу перейти к запуску и тестированию проекта, 
    скачайте готовые файлы с рекомендациями по ссылкам:
    - Финальные рекомендации [recommendations.parquet](https://disk.yandex.ru/d/QTuc5JxfzIdKjg)
    - Топ-треки [top_popular.parquet](https://disk.yandex.ru/d/I1YXRqtM-iR6XQ)
    - Похожие треки [similar.parquet](https://disk.yandex.ru/d/QytOSqKu1wHPoQ)

## Этапы и результаты выполнения проекта
1. __Предобработка данных и EDA__
    - Проверили исходные данные на наличие пропусков, дубликатов, некорректных типов, 
    значений и связей между таблицами. Оставили только треки, где были заполнены все четыре категории жанр/артист/альбом/название трека. Из истории взаимодействий убрали прослушивания, соответствующие удаленным трекам;
    - Чтобы уменьшить датасет событий до 1.5-2G, у всех пользователей удалили примерно 2/3 прослушиваний 
    (для этого у каждого пользователя оставили только треки на позициях 1,4,7 итд), 
    после чего удалили колонку `track_seq`;
    - Предобработанные данные о треках и взаимодействиях сохранены в файлах `items.parquet` и `events.parquet` 
    в облачном S3-хранилище.
    
    Код для предварительной обработки и EDA представлен в файле `recommendations.ipynb`.

2. __Расчёт рекомендаций__
    
    Ниже перечислены реализованные подходы для генерации рекомендаций вместе с их метриками на валидации:
    - Рекомендации по умолчанию на основе топ-треков по количеству прослушиваний;
        - Доля событий у "холодных" пользователей, совпавших с рекомендациями по умолчанию: 0.058,
        - Доля холодных пользователей без релевантных рекомендаций: 0.62,
        - Среднее покрытие холодных пользователей: 1.87;
    - Персональные рекомендации на основе коллаборативного подхода и ALS;
        - coverage: 0.006,
        - novelty@5: 0.792,
        - precision: 0.002,
        - recall: 0.004;
    - Рекомендации на основе похожих треков на основе ALS (i2i);
    - Финальные рекомендации на основе ранжирующей catboost-модели по нескольким признакам, 
    включая коллаборативные оценки, кол-во треков, прослушанных каждым пользователем, 
    и парные жанровые оценки
        - coverage: 0.006,
        - novelty@5: 0.792,
        - precision: 0.002,
        - recall: 0.004.

    Код для расчёта рекомендаций представлен в файле `recommendations.ipynb`.

3. __Запуск и тестирование сервиса__
    
    Исходный код основного и вспомогательных сервисов содержится в файлах:
    - `recommendations_service.py` - основной сервис для генерации оффлайн- и онлайн-рекомендаций;
    - `features_service.py` - вспомогательный сервис для поиска похожих треков;
    - `events_service.py` - вспомогательный сервис для сохранения и получения 
    последних прослушанных треков пользователя.
    
    Для запуска сервисов необходимо выполнить три команды (по одной на каждый сервис) в трех разных терминалах, находясь в папке проекта:
    ```
    uvicorn recommendations_service:app
    uvicorn events_service:app --port 8020
    uvicorn features_service:app --port 8010
    ```
    
    Исходный код для тестирования сервисов находится в файле `test_service.py`.
    Ниже перечислены три тестовых сценария и команды для их запуска (данные команды
    нужно выполнять в терминале, находясь в папке проекта):
    - Получение рекомендаций по умолчанию

    - Получение персональных рекомендаций без онлайн-истории

    - Получение персональных рекомендаций с онлайн-историей.

