from models import User, UserDay, db
from flask import session


def update_user_settings(form, user):
    db.session.execute(db.delete(UserDay).where(UserDay.user == user.id))  # delete all the user's days
    userdays = form.data  # get the days from the form
    days = [
        (0, userdays['sunday']),
        (1, userdays['monday']),
        (2, userdays['tuesday']),
        (3, userdays['wednesday']),
        (4, userdays['thursday']),
        (5, userdays['friday']),
        (6, userdays['saturday']),
    ]
    for day in days:  # for each day
        if day[1] is True:
            user_day = UserDay(user=user.id, day=day[0])  # create a new user day
            db.session.add(user_day)  # add the user day to the database
    db.session.commit()  # commit changes to the database
