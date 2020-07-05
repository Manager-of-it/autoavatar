# slimfriends.py
# Purporse: unfollow friends based upon conditions
# Description: supposed friends get the boot if they don't follow me or are inactive
#
#
import sqlite3
from twitObj import *
from config import *


conn = sqlite3.connect('db/aavatar.db')
c = conn.cursor()

myTwitObj = createTwitObj(consumer_key, consumer_secret, access_token, access_token_secret)


try:
    print("get twit_friends")
    c.execute('''SELECT id FROM twit_friends''')
except sqlite3.Error as e:
    print("Database error: %s" % e)
twit_friends_ids = c.fetchall()
print("list friends_ids ...", twit_friends_ids)

try:
    print("get twit_followers")
    c.execute('''SELECT id FROM twit_followers''')
except sqlite3.Error as e:
    print("Database error: %s" % e)
twit_followers_ids = c.fetchall()
print("list follower_ids ...", twit_followers_ids)

print("make sets ")
set_twit_flwr_ids = set([i[0] for i in twit_followers_ids])
print("set followers is:", set_twit_flwr_ids)
set_twit_friends_ids = set([i[0] for i in twit_friends_ids])
print("set friends is:", set_twit_friends_ids)

list_not_friends_ids = (set_twit_friends_ids.difference(set_twit_flwr_ids))
print("list NOT friends...", list_not_friends_ids)
i = 0
for not_friend_id in list_not_friends_ids:
    i = i + 1
    print("Destroy friendship: ", not_friend_id, "\tcount: ", i)
    try:
        myTwitObj.destroy_friendship(not_friend_id)
    except tweepy.TweepError as e:
        print("Destroy friendship error:", e)

