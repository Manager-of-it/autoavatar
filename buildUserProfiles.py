# buildUserProfiles.py
# Purporse: collect user profile information from following list
# Description: we have a lot of users that we're following. We need to to gather and store their details.
#
#
import traceback
import sqlite3
from sqlite3.dbapi2 import Error
from datetime import datetime

from config import *
from twitObj import *

print(datetime.now(), "BEGIN!")
conn = sqlite3.connect('db/aavatar.db')
c = conn.cursor()
myTwitObj = createTwitObj(consumer_key, consumer_secret, access_token, access_token_secret)

i = 0
j = 0
not_friends = 0
yes_friends = 0
for user in tweepy.Cursor(myTwitObj.friends, screen_name="Manager_of_it").items():
    i = i + 1
    print(datetime.now(), 'friend: ' + user.screen_name + "\t--\tuser_id: " + str(user.id) + "\trecords processed: ", i)
    e: Error
    try:
        c.execute('''INSERT INTO twit_friends VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', (user.id, user.id_str, user.name, user.screen_name, user.location, user.description, "NULL", user.protected, user.followers_count, user.friends_count, user.listed_count, user.created_at, "NULL", user.verified, user.statuses_count, user.lang))
    except sqlite3.Error as e:
        print("Database error: %s" % e)
    conn.commit()

for user in tweepy.Cursor(myTwitObj.followers, screen_name="Manager_of_it").items():
    j = j + 1
    print(datetime.now(), 'follower: ' + user.screen_name + "\t--\tuser_id: " + str(user.id) + "\trecords processed", j)
    e: Error
    try:
        c.execute('''INSERT INTO twit_followers VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', (user.id, user.id_str, user.name, user.screen_name, user.location, user.description, "NULL", user.protected, user.followers_count, user.friends_count, user.listed_count, user.created_at, "NULL", user.verified, user.statuses_count, user.lang))
    except sqlite3.Error as e:
        print("Database error: %s" % e)
    conn.commit()






 #   try:
 #       friendShipObj = myTwitObj.show_friendship(source_screen_name="Manager_of_it", target_id=user.id)
 #   except:
 #       traceback.print_exc()
 #       traceback.print_stack()
 #       break
 #   print("following:", friendShipObj[0].following, "friends:", friendShipObj[0].followed_by)
 #   if friendShipObj[0].followed_by is True:
 #       yes_friends = yes_friends+1
 #       print("You're with me, friend! Yes friends count: ", yes_friends)
 #   else:
 #       not_friends = not_friends + 1
 #       print("You are not my friend! Not friends count: ", not_friends)

 #   try:
 #       c.execute('''INSERT INTO aa_users VALUES (?,?,?,?)''', (user.id, "today", friendShipObj[0].following, friendShipObj[0].followed_by))
 #   except sqlite3.Error as e:
 #       print("Database error: %s" % e)
 #   conn.commit()
 #   i = i + 1
 #   if i > 4:
 #       break

print(datetime.now(), "END!")
# print("Summary -- yes_friends:", yes_friends, "\tno_friends:", not_friends)
