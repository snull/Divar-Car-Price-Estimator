import ML
import crawler
import inquirer
import os

mode = [
    inquirer.List(
        "mode",
        message="What do you want to do?",
        choices=["Fetch data", "Estimate car price", "Exit"],
    ),
]

confirmation = [
    inquirer.Confirm("continue", message="Should I continue"),
]

crawl_questions = [
    inquirer.Text("city", message="please enter the city name that you want to fetch data from(for example: tehran)"),
    inquirer.Text("car", message="please enter the car brand and model that you want to fetch its data"
                                 "(in this format: peugeot/206, if you don't want a specific car leave it blank)"),
]


def menu(db_host, db_user, db_password):
    selected_mode = inquirer.prompt(mode)["mode"]
    os.system("cls")

    if "Fetch data" in selected_mode:
        car, city = crawler.user_input()
        os.system("cls")
        crawl_data(db_host, db_user, db_password, car, city)
    elif "Estimate car price" in selected_mode:
        new_data = ML.user_input()
        os.system("cls")
        ML.estimate(db_host, db_user, db_password, new_data)
        state = inquirer.prompt(confirmation)
        if state["continue"]:
            os.system("cls")
            menu(db_host, db_user, db_password)
        else:
            os.system("cls")
            exit()

    elif "Exit" in selected_mode:
        exit()


def crawl_data(db_host, db_user, db_password, car, city):
    trigger = crawler.crawl(db_host, db_user, db_password, car, city)
    if trigger:
        state = inquirer.prompt(confirmation)
        if state["continue"]:
            crawl_data(db_host, db_user, db_password, car, city)
        else:
            os.system("cls")
            menu(db_host, db_user, db_password)


def main():
    db_host, db_user, db_password = crawler.db_data_input()
    menu(db_host, db_user, db_password)


if __name__ == '__main__':
    main()
