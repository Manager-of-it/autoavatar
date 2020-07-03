# slimfriends.py
# Purporse: unfollow friends based upon conditions
# Description: supposed friends get the boot if they don't follow me or are inactive
#
#
import tweepy
import traceback
from config import *


def createTwitObj(consumer_key, consumer_secret, access_token, access_token_secret):
    print("Twitter API object: creating...")
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth_handler=auth, wait_on_rate_limit=True)
    try:
        api.rate_limit_status()  # make an API call to validate access
    except:
        print("Twitter API object: creation FAILED!")
        exit(1)
    print("Twitter API object: created.\n")
    return api


# t = Twitter(auth=OAuth(token, token_secret, consumer_key, consumer_secret))
i = 0
myTwitObj = createTwitObj(consumer_key, consumer_secret, access_token, access_token_secret)

not_friends = 0
yes_friends = 0

for user in tweepy.Cursor(myTwitObj.friends, screen_name="Manager_of_it").items():
    print('friend: ' + user.screen_name + "\t--\tuser_id: " + str(user.id))
    try:
        friendShipObj = myTwitObj.show_friendship(source_screen_name="Manager_of_it", target_id=user.id)
        friendShipObj = myTwitObj.show_friendship()
    except:
        traceback.print_exc()
        traceback.print_stack()
        break
    if friendShipObj[0].following != True:
        not_friends = not_friends+1
        print("You are not my friend! Not friends count: ", not_friends)
    else:
        yes_friends = yes_friends+1
        print("You're with me, friend! Yes friends count: ", yes_friends)
    i = i + 1

print("Summary -- yes_friends:", yes_friends, "\tno_friends:", not_friends)
