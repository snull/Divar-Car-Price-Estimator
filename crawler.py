import json
import re
import requests
from bs4 import BeautifulSoup
import persian
import urllib
import time
import random
import mysql.connector
import inquirer

db_questions = [
    inquirer.Text("db_host", message="Database host"),
    inquirer.Text("db_user", message="Database user"),
    inquirer.Text("db_password", message="Database password"),
]
crawl_questions = [
    inquirer.Text("city",
                  message="please enter the city name that you want to fetch data from(for example: tehran)"),
    inquirer.Text("car", message="please enter the car brand and model that you want to fetch its data"
                                 "(in this format: peugeot/206, if you don't want a specific car leave it blank)"),
]
engine_condition_dict = {
    "": 0,
    "سالم": 3,
    "تعویض شده": -1,
    "نیاز به تعمیر": -3
}
chassis_condition_dict = {
    "": 0,
    "سالم و پلمپ": 3,
    "ضربه‌خورده": -2,
    "رنگ‌شده": -3
}
f_chassis_condition_dict = {
    "": 0,
    "سالم و پلمپ": 3,
    "ضربه‌خورده": -2,
    "رنگ‌شده": -3
}
b_chassis_condition_dict = {
    "": 0,
    "سالم و پلمپ": 3,
    "ضربه‌خورده": -2,
    "رنگ‌شده": -3
}
body_condition_dict = {
    "": 0,
    "اوراقی": -40,
    "تصادفی": -30,
    "تمام‌رنگ": -20,
    "دوررنگ": -14,
    "رنگ‌شدگی، در چند ناحیه": -10,
    "صافکاری بی‌رنگ": -2,
    "خط و خش جزیی": 2,
    "سالم و بی‌خط و خش": 10,

    "رنگ‌شدگی در 1 ناحیه": -3, "رنگ‌شدگی در 2 ناحیه": -4.5, "رنگ‌شدگی در 3 ناحیه": -6,
    "رنگ‌شدگی در 4 ناحیه": -7.5, "رنگ‌شدگی در 5 ناحیه": -9, "رنگ‌شدگی در 6 ناحیه": -10.5,
    "رنگ‌شدگی در 7 ناحیه": -12, "رنگ‌شدگی در 8 ناحیه": -13.5, "رنگ‌شدگی در 9 ناحیه": -15, "رنگ‌شدگی در 10 ناحیه": -16.5,

    "رنگ‌شدگی، در 1 ناحیه": -3, "رنگ‌شدگی، در 2 ناحیه": -4.5, "رنگ‌شدگی، در 3 ناحیه": -6,
    "رنگ‌شدگی، در 4 ناحیه": -7.5, "رنگ‌شدگی، در 5 ناحیه": -9, "رنگ‌شدگی، در 6 ناحیه": -10.5,
    "رنگ‌شدگی، در 7 ناحیه": -12, "رنگ‌شدگی، در 8 ناحیه": -13.5, "رنگ‌شدگی، در 9 ناحیه": -15,
    "رنگ‌شدگی، در 10 ناحیه": -16.5,

    "صافکاری بی‌رنگ، در 1 ناحیه": -1, "صافکاری بی‌رنگ، در 2 ناحیه": -2, "صافکاری بی‌رنگ، در 3 ناحیه": -3,
    "صافکاری بی‌رنگ، در 4 ناحیه": -4, "صافکاری بی‌رنگ، در 5 ناحیه": -5, "صافکاری بی‌رنگ، در 6 ناحیه": -6,
    "صافکاری بی‌رنگ، در 7 ناحیه": -7, "صافکاری بی‌رنگ، در 8 ناحیه": -8, "صافکاری بی‌رنگ، در 9 ناحیه": -9,
    "صافکاری بی‌رنگ، در 10 ناحیه": -10,

}
gearbox_dict = {
    "": 0,
    "دنده‌ای": 0,
    "اتوماتیک": 1,
}


def crawl(db_host, db_user, db_password, car, city):
    add_car, cnx, cursor = db_handler(db_host, db_password, db_user)
    page = 0
    counter = 0
    try :
        while True:
            print("[    ---PAGE--- : " + str(page) + "    ]")
            try:
                stuffs, r = page_request(page, car, city)
                find_car(add_car, cnx, counter, cursor, stuffs)

            except Exception as e:
                print("\n@@@@@ ERROR @@@@@\n" + str(page) + "\n" + "\n" + repr(
                    e) + "\n@@@@@ ERROR @@@@@\n")
                pass

            page += 1
    except KeyboardInterrupt:
        print("STOPPED!")
        trigger = True
    cnx.close()
    return trigger


def db_handler(db_host, db_password, db_user):
    cnx = mysql.connector.connect(user=db_user, password=db_password, host=db_host)
    cursor = cnx.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS divar;")
    cursor.execute("USE divar  ;")
    cursor.execute(" CREATE TABLE IF NOT EXISTS`divar`.`car` (`car_id` CHAR(8) NOT NULL ,"
                   " `link` VARCHAR(500) NOT NULL , `price` INT(16) NOT NULL ,"
                   " `model` VARCHAR(200) NOT NULL , `model_year` INT NOT NULL ,"
                   " `milage` INT NOT NULL , `color` VARCHAR(100) NOT NULL ,"
                   " `engine_condition` INT NOT NULL , `chassis_condition` INT NOT NULL ,"
                   " `body_condition` INT NOT NULL , `gearbox` INT NOT NULL ,"
                   " `f_chassis_condition` INT NOT NULL ,"
                   " `b_chassis_condition` INT NOT NULL , PRIMARY KEY (`car_id`)) ENGINE = InnoDB;")
    add_car = (f"INSERT IGNORE INTO car "
               "(car_id, link, price, model, model_year, milage, color, engine_condition,"
               " chassis_condition, body_condition, gearbox, f_chassis_condition, b_chassis_condition) "
               "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
    return add_car, cnx, cursor


def page_request(page, car, city):
    r = requests.get('https://divar.ir/s/%s/car/%s?page=%d' % (city, car, page))
    soup = BeautifulSoup(r.text, 'html.parser')
    stuffs = soup.find_all("div", attrs={'class': 'post-card-item-af972 kt-col-6-bee95 kt-col-xxl-4-e9d46'})
    return stuffs, r


def find_car(add_car, cnx, counter, cursor, stuffs):
    for stuff in stuffs:
        print("[    " + str(counter) + "    ]")
        link, car_id = find_car_id(stuff)
        car_info = car_data_request(car_id)

        try:
            price, model, milage, model_year, color = main_data_extractor(car_info)

            engine_condition = chassis_condition = body_condition = gearbox = f_chassis_condition = b_chassis_condition = 0
            car_data = car_info["widgets"]["list_data"]

            for data in car_data:
                engine_condition, chassis_condition, body_condition, gearbox, f_chassis_condition, b_chassis_condition = specs_data_extractor(
                    data, engine_condition, chassis_condition, body_condition, gearbox, f_chassis_condition,
                    b_chassis_condition)

            cursor.execute(add_car, (
                car_id, link, price, model, model_year, milage, color, engine_condition, chassis_condition,
                body_condition,
                gearbox, f_chassis_condition, b_chassis_condition))


        except Exception as e:
            print("\n#####################     ERROR     #####################\n" + link + "\n" + repr(
                e) + "\n#####################     ERROR     #####################\n")
            pass

        print("[    " + str(counter) + "    ]")
        print("-------------------------------------------------")
        cnx.commit()
        counter += 1
        time.sleep(random.randrange(2, 5))


def find_car_id(stuff):
    print(stuff.text)
    link = stuff.find("a")
    link_regex = re.compile(r'href="([^"$]+)"')
    link = str(link)
    link = link_regex.search(link)[1]
    car_id = link[-8:]
    link = urllib.parse.quote(link)
    link = "https://divar.ir" + link
    print('id : ' + car_id)
    print('لینک : ' + link)
    return link, car_id


def car_data_request(car_id):
    r_car = requests.get(f"https://api.divar.ir/v8/posts/{car_id}")
    if r_car.status_code == 200:
        car_info = r_car.text
        car_info = json.loads(car_info)
        return (car_info)
    else:
        print("\n ~~~~~~~~~~~~~~~~~~~~~~~~~~~ " + str(r_car) + " ~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
        print("\n ~~~~~~~~~~~~~~~~~~~~~~~~~~~ RATE LIMIT, WAITING 20 SEC ~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
        time.sleep(20)
        return car_data_request(car_id)


def main_data_extractor(car_info):
    price = car_info["data"]["webengage"]["price"]
    print('قیمت : ' + str(price))

    model = car_info["data"]["brand_model"]
    print('مدل : ' + model)

    milage = car_info["widgets"]["list_data"][0]["items"][0]["value"]
    milage = persian.convert_fa_numbers(milage)
    milage_reg = re.compile(r'\d+')
    milage = milage_reg.findall(milage)
    milage = int("".join(milage))
    print('کارکرد : ' + str(milage))

    model_year = car_info["widgets"]["list_data"][0]["items"][1]["value"]
    model_year = persian.convert_fa_numbers(model_year)
    model_year_reg = re.compile(r'[\d]+')
    model_year = model_year_reg.findall(model_year)
    model_year = int(model_year[0])
    print('سال : ' + str(model_year))

    color = car_info["widgets"]["list_data"][0]["items"][2]["value"]
    print('رنگ : ' + color)
    return price, model, milage, model_year, color


def specs_data_extractor(data, engine_condition, chassis_condition, body_condition, gearbox, f_chassis_condition,
                         b_chassis_condition):
    if 'وضعیت موتور' in data.values():
        engine_condition = engine_condition_dict[data["value"]]
        print('وضعیت موتور : ' + str(engine_condition))

    elif 'وضعیت شاسی‌ها' in data.values():
        chassis_condition = chassis_condition_dict[data["value"]]
        print('وضعیت شاسی‌ها : ' + str(chassis_condition))

    elif 'وضعیت بدنه' in data.values():
        body_condition = data["value"]
        body_condition = persian.convert_fa_numbers(body_condition)
        body_condition = body_condition_dict[body_condition]
        print('وضعیت بدنه : ' + str(body_condition))

    elif 'گیربکس' in data.values():
        gearbox = gearbox_dict[data["value"]]
        print('گیربکس : ' + str(gearbox))

    elif 'وضعیت شاسی جلو' in data.values():
        f_chassis_condition = f_chassis_condition_dict[data["value"]]
        print('شاسی جلو : ' + str(f_chassis_condition))

    elif 'وضعیت شاسی عقب' in data.values():
        b_chassis_condition = b_chassis_condition_dict[data["value"]]
        print('شاسی عقب : ' + str(b_chassis_condition))

    return engine_condition, chassis_condition, body_condition, gearbox, f_chassis_condition, b_chassis_condition


def db_data_input():
    db = inquirer.prompt(db_questions)
    db_host = db["db_host"]
    db_user = db["db_user"]
    db_password = db["db_password"]
    return db_host, db_user, db_password


def user_input():
    answers = inquirer.prompt(crawl_questions)
    car = answers["car"]
    city = answers["city"]
    return car, city


if __name__ == '__main__':
    db_host, db_user, db_password = db_data_input()
    car, city = user_input()
    crawl(db_host, db_user, db_password, car, city)
