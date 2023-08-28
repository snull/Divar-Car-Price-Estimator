from sklearn import tree
from sklearn import preprocessing
import mysql.connector
import inquirer
from crawler import engine_condition_dict, body_condition_dict, chassis_condition_dict, gearbox_dict, \
    f_chassis_condition_dict, b_chassis_condition_dict, db_data_input

learn_questions = [
    inquirer.Text("model", message="Car brand and model (For example: Peugeot 206 2)"),
    inquirer.Text("model_year", message="Model year(For example: 1396)"),
    inquirer.Text("milage", message="Milage(For example: 73000)"),
]
engine_condition_list = [
    inquirer.List(
        "engine_condition",
        message="Engine condition :",
        choices=engine_condition_dict.keys(),
    ),
]
body_condition_list = [
    inquirer.List(
        "body_condition",
        message="Body condition :",
        choices=body_condition_dict.keys(),
    ),
]
chassis_condition_list = [
    inquirer.List(
        "chassis_condition",
        message="Chassis condition :",
        choices=chassis_condition_dict.keys(),
    ),
]
f_chassis_condition_list = [
    inquirer.List(
        "f_chassis_condition",
        message="Front chassis condition :",
        choices=f_chassis_condition_dict.keys(),
    ),
]
b_chassis_condition_list = [
    inquirer.List(
        "b_chassis_condition",
        message="Back chassis condition :",
        choices=b_chassis_condition_dict.keys(),
    ),
]
gearbox_list = [
    inquirer.List(
        "gearbox",
        message="Gearbox :",
        choices=gearbox_dict.keys(),
    ),
]


def labeling(specs, index, le):
    labels = {""}
    for i in range(len(specs)):
        labels.add(specs[i][index])

    labels = list(labels)
    le.fit(labels)

    for i in range(len(specs)):
        specs[i][index] = le.transform([specs[i][index]])[0]

    return le


def estimate(db_host, db_user, db_password, new_data):
    cnx = mysql.connector.connect(user=db_user, password=db_password, host=db_host)
    cursor = cnx.cursor()
    cursor.execute(f"USE divar  ; ")
    query = ("SELECT * FROM car ;")
    cursor.execute(query)

    specs = list()
    prices = list()
    for (
            car_id, link, price, model, model_year, milage, color, engine_condition, chassis_condition, body_condition,
            gearbox,
            f_chassis_condition, b_chassis_condition) in cursor:
        specs.append([model, model_year, milage, color, engine_condition, chassis_condition, body_condition, gearbox,
                      f_chassis_condition, b_chassis_condition])
        prices.append(price)

    new_data[0][4] = engine_condition_dict[new_data[0][4]]
    new_data[0][5] = body_condition_dict[new_data[0][5]]
    new_data[0][6] = chassis_condition_dict[new_data[0][6]]
    new_data[0][7] = f_chassis_condition_dict[new_data[0][7]]
    new_data[0][8] = b_chassis_condition_dict[new_data[0][8]]
    new_data[0][9] = gearbox_dict[new_data[0][9]]

    le = preprocessing.LabelEncoder()
    # Labeling Models
    try:
        le = labeling(specs, 0, le)
        new_data[0][0] = le.transform([new_data[0][0]])[0]
    except ValueError or KeyError:
        print("Sorry, there is no data about your car model in the database!")
        return

    # Labeling Colors
    try:
        le = labeling(specs, 3, le)
        new_data[0][3] = le.transform([new_data[0][3]])[0]
    except ValueError or KeyError:
        print("Sorry, there is no data about your car color in the database!")

    try:
        clf = tree.DecisionTreeClassifier()
        clf = clf.fit(specs, prices)
        answer = clf.predict(new_data)
        print("".center(50, "-"))
        print(("\033[1;34m [ Estimated price : " + str(answer) + " ] \033[0m").center(61, "-"))
        print("".center(50, "-"))
    except KeyError or ValueError:
        print("Sorry, there is no data about your car in the database!")
        return


def user_input():
    new_data = [[]]
    car_specs = inquirer.prompt(learn_questions)
    for spec in car_specs.values():
        new_data[0].append(spec)
    new_data[0].append(input("[\033[1;33m?\033[0m] Color(For example: سفید): "))
    new_data[0].append(inquirer.prompt(engine_condition_list)["engine_condition"])
    new_data[0].append(inquirer.prompt(body_condition_list)["body_condition"])
    new_data[0].append(inquirer.prompt(chassis_condition_list)["chassis_condition"])
    new_data[0].append(inquirer.prompt(f_chassis_condition_list)["f_chassis_condition"])
    new_data[0].append(inquirer.prompt(b_chassis_condition_list)["b_chassis_condition"])
    new_data[0].append(inquirer.prompt(gearbox_list)["gearbox"])
    return new_data


if __name__ == '__main__':
    db_host, db_user, db_password = db_data_input()
    new_data = user_input()
    estimate(db_host, db_user, db_password, new_data)
