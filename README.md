# Яндекс Практикум, курс "Инженер Машинного Обучения" (2024 г.)
# Проект 4-го спринта: "Создание рекомендательной системы"
## Выполнил: Кирилл Н., email: ibnkir@yandex.ru

### Описание проекта
Целью проекта является создание системы персональных рекомендаций для музыкального сервиса, 
которая будет предлагать пользователям треки или подборки треокв на основе их вкусов и предпочтений. 
В рамках проекта был разработан пайплайн для расчета рекомендаций и интегрирован в веб-сервис.

Основные инструменты и Python-библиотеки:
- Visual Studio Code,
- FastAPI, 
- uvicorn,
- Jupyter Lab,
- surprise.


### Как воспользоваться репозиторием:
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

### Этапы и результаты выполнения проекта
__Предобработка и EDA данных__

Код для предварительной обработки данных находится в файле `part_1_preprocess_eda.ipynb`.

__Расчёт рекомендаций__

Код для расчёта рекомендаций находится в файле `part_2_recs.ipynb`.

<*укажите здесь значения полученных метрик для оффлайн-рекомендаций*>

__Запуск и тестирования сервиса__

Код сервиса рекомендаций находится в файле `recommendations_service.py`.

<*укажите здесь необходимые шаги для запуска сервиса рекомендаций*>

Код для тестирования сервиса находится в файле `part_3_test.ipynb`.

<*укажите здесь необходимые шаги для тестирования сервиса рекомендаций*>
