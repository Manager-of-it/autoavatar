# twitObj.py
# Purporse: segregation of Twitter object creation
# Description: seems like a good idea to just stuff creating my twitter object into its own file.
#
#
import tweepy

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

