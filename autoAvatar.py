#!/usr/bin/python 

######################################################################
#
# Name: autoavator.py
# Description: Twitter tool written in python and using a python API to select users to follow
# Purpose: Generate a list of possible users to follow on twitter
# Author: Manager_of_it
# Date: November 24, 2016

# TODOS
# functional: 
#   query non-followers by dates ago followed
#   unFollow by account last activity date
#   score screen_name in list
#   score location in list
#
#   review profiles, attribs and scores #DONE
#   sort profiles #DONE
#
#
# file mangement:
#   store friendProfile in local file
#   refresh friendProfile, friends, followers local file from API
# API management:
#   manage rate limits for getting friends, followers
# auto automation:
#   loop over a list of profiles, friend or skip
# 
#
# Operations: 
# key word search of users -- DONE
# 
# print report -- list users: name,tweets,frnd, flwrs, pp ratio, spam ratio -- # DONE!
# print user_name, description, #tweets, #followers, #following, ratio, # # location, created, id, verified  #DONE
# format created date 
# make results of queries return unique users -- DONE!
# sort (print) unique users:name,tweets,frnd, flwrs, pp ratio, spam ratio -- # DONE!
#
# print last tweet, date -- DONE
# print last 10 tweets, dates -- DONE
#
# establish work flow--> users (follow, ignore, more info) --DONE
# interactive::(f)ollow,(s)kip,(m)ore -- DONE
#
# add friends selected users -- DONE
#
# by screen_name
# journal friends suggested, added, removed -- DONE
# read sets from files: suggestSet, followSet, unfollowSet -- DONE
# get list friends existing; convert to set(of screen_names): existingSet -- # DONE
# make set, touchedSet: intersection of suggestSet, existingSet, followSet, # unfollowSet -- DONE
# clean list, getFreshUL(): compare new suggestions with touchedSet -- DONE
# provide more inputs for searches -- DONE
#
# get more tweets/users from tweet timeline: manage  max_id -- DONE
# get max_id from list -- DONE
# 
# get followers -- DONE
#   query non-followers by dates ago followed
# remove non-followers -- DONE
#
# generate followScore=100 # DONE
# manage date comparisons: last activity, account created #DONE
#
#   compute retweet ratio -- DONE
#   print user from profile -- DONE

import datetime
import json
import oauth2
import os
import re
import sys
import time
import twitter

reload(sys) 
sys.setdefaultencoding('UTF8') #set default encoding from ascii to UTF8

#-----------------------------------------------------------------------
# create twitter API object
#-----------------------------------------------------------------------

config = {}
try:
  execfile("config.py", config)
except:
  callErrorHandler("Read of config.py failed.")

try: 
  api = twitter.Api(consumer_key=config["consumer_key"], 
                  consumer_secret=config["consumer_secret"],
                  access_token_key=config["access_key"],
                  access_token_secret=config["access_secret"])
except: 
  callErrorHandler("API object creation failed.")

#-----------------------------------------------------------------------
# open data and log files
#-----------------------------------------------------------------------

#def initFiles():
try:
  journal_file = open('aavatar.log', 'a+') 
except:
  callErrorHandler("Open read of avatar.log failed.")
try:
  suggest_file = open('suggest.dat', 'a+')
except:
  callErrorHandler("Open read of suggest.dat failed.")
try:
  follow_file = open('follow.dat', 'a+') 
except:
  callErrorHandler("Open read of follow.dat failed.")
try:
  unfollow_file = open('unfollow.dat', 'a+') 
except:
  callErrorHandler("Open read of unfollow.dat failed.")

#-----------------------------------------------------------------------
# get users, print
#-----------------------------------------------------------------------

def getUfQ(q_term="devops",q_lang="en",q_since="2016-01-01",q_until=str(datetime.date.today()),q_count=20, q_max_id=999999999999999999):
    r=q100(q_term,q_lang,q_since,q_until,q_count,q_max_id) #search
    ul=convertSLtoUL(r) #convert status to users
    ul=getULU(ul) #clean users (remove dups)
    ul=getFreshUL(ul,touchedSet)
    printLU(ul)  #report
    print "Len, ul:",len(ul)
    return ul

def getTL(thisUL):
  thisTL=[]
  for i in range(len(thisUL)):
    thisTL.append(getUserTweets(thisUL[i]))
  return thisTL

def getMaxId(my_statusList):
  thisMaxId=999999999999999999
  for i in range(len(my_statusList)):
    if thisMaxId > my_statusList[i].id:
      thisMaxId=my_statusList[i].id
  return thisMaxId

def convertSLtoUL(my_statusList): #get List of Users from Status List: convert status to users
   print(len(my_statusList))
   my_listUsers=[]
   for i in range(len(my_statusList)):
      if my_statusList[i].user.friends_count == 0 or my_statusList[i].user.followers_count == 0:  # remove no friends/followers
          continue
      my_listUsers.append(my_statusList[i].user)
      continue
   return my_listUsers

def convertULtoSetSNs(thisUL):
  thisSet=set()
  for i in range(len(thisUL)):
    thisSet.add(thisUL[i].screen_name)
    continue
  return thisSet

def getULU(thisUL):  #get unique list of users
    # order preserving
    uniqueUL = []
    for e in thisUL:
        if e not in uniqueUL:
             uniqueUL.append(e)
    return uniqueUL

#get unique list of users -- remove already touched users
def getFreshUL(thisUL,thisTouchedSet):
  print "pre-cleaned: "+str(len(thisUL))
  cleanUL=list(thisUL)
  for i in range(len(thisUL)):
    if thisUL[i].screen_name in thisTouchedSet:
      print "remove " + thisUL[i].screen_name + " from User List"
      cleanUL.remove(thisUL[i])
    else: continue
  print "cleaned: "+str(len(cleanUL))
  return cleanUL

# rid users with a null status
def getRidNullUsers(thisUL): 
  cleanUL=list(thisUL)
  print "pre-rid: "+str(len(thisUL))
  for i in range(len(thisUL)):
      if (thisUL[i].status==None):
        cleanUL.remove(thisUL[i])
      else: continue
  print "rid: "+str(len(cleanUL))
  return cleanUL

def printLU(listOfUsers): #print List Users
    print bcolors.HEADER + "screen_name\ttweets\tfollwers\t  friends\tpop-ratio\tchorus-ratio" + bcolors.ENDC
    for i in range(len(listOfUsers)):
        if listOfUsers[i].friends_count == 0 or listOfUsers[i].followers_count == 0:
            print "{:14}\t{}\t{}\t{}\tNOFOLWERS AND\OR FRIENDS".format(listOfUsers[i].screen_name,listOfUsers[i].statuses_count,listOfUsers[i].friends_count,listOfUsers[i].followers_count)
            continue
        print "{0:14}\t{1}\t{2:8}\t{3:8}\t{4:5.1f}\t\t{5:5.1f}".format(listOfUsers[i].screen_name,listOfUsers[i].statuses_count,listOfUsers[i].followers_count,listOfUsers[i].friends_count,round(float(listOfUsers[i].followers_count)/listOfUsers[i].friends_count,3),round(float(listOfUsers[i].statuses_count)/listOfUsers[i].followers_count,3))


def printLUfProf(thisLP): #print list of auto-avatar user profiles
    print bcolors.HEADER + "screen_name\ttweets\tfollwers\t  friends\tpop-ratio\tchorus-ratio\tfriendScore" + bcolors.ENDC
    for i,prof in enumerate(thisLP):
        if thisLP[prof]['friends'] == 0 or thisLP[prof]['followers'] == 0:
          print "screen_name: {}\tNO FOLLOWERS AND\OR FRIENDS".format(prof)
          continue
        print "{0:14}\t{1}\t{2:8}\t{3:8}\t{4:5.1f}\t\t{5:5.1f}\t\t{6:5}".format(prof,thisLP[prof]['tweets'],thisLP[prof]['followers'],thisLP[prof]['friends'],thisLP[prof]['pratio'],thisLP[prof]['sratio'],thisLP[prof]['friendScore'])

def printSLUfProf(thisLP, thisSortedL): #print list of auto-avatar user profiles
    print bcolors.HEADER + "screen_name\ttweets\tfollwers\t  friends\tpop-ratio\tchorus-ratio\tfriendScore" + bcolors.ENDC
    for i in range(len(thisSortedL)):
#        print i
        if thisLP[thisSortedL[i]]['friends'] == 0 or thisLP[thisSortedL[i]]['followers'] == 0:
          print "screen_name: {}\tNO FOLLOWERS AND\OR FRIENDS".format(thisSortedL[i])
          continue
        print "{0:14}\t{1}\t{2:8}\t{3:8}\t{4:5.1f}\t\t{5:5.1f}\t\t{6:5}".format(thisSortedL[i],thisLP[thisSortedL[i]]['tweets'],thisLP[thisSortedL[i]]['followers'],thisLP[thisSortedL[i]]['friends'],thisLP[thisSortedL[i]]['pratio'],thisLP[thisSortedL[i]]['sratio'],thisLP[thisSortedL[i]]['friendScore'])

###############################################
#
# sort list users:
#  screen_name = n #  statuses_count = t #  friends_count = fr #  followers_count = f #  pratio = p #  sratio = s

def sortLU(thisULUlist,thisSortType='p'):
  sortedLU=False
  while not sortedLU:
    thisSortType=raw_input("Sort options: screen_(n)ame, (t)weets, (f)ollowers, (fr)iends, (p)op-ratio, (s)pam-ratio: ")
    if thisSortType=="f":
      ulS=sorted(thisULUlist, key=lambda myusers: myusers.followers_count, reverse=True)
    elif thisSortType=="n":
      ulS=sorted(thisULUlist, key=lambda myusers: myusers.screen_name)
    elif thisSortType=="s":
      ulS=sorted(thisULUlist, key=lambda myusers: myusers.statuses_count/myusers.followers_count, reverse=True)
    elif thisSortType=="t":
      ulS=sorted(thisULUlist, key=lambda myusers: myusers.statuses_count, reverse=True)
    elif thisSortType=="fr":
      ulS=sorted(thisULUlist, key=lambda myusers: myusers.friends_count, reverse=True)
    elif thisSortType=="p":
      ulS=sorted(thisULUlist, key=lambda myusers: (myusers.followers_count/myusers.friends_count), reverse=True)
    else:
      inputErrorHandler(thisSortType,"invalid sort type!")
      continue
    sortedLU=True
  return ulS

def sortPs(thisPL):
# listOfProfilesDict(key=screen_name, profileDict(keys=attribs, attribsValues)))
  sortedLU=False
  while not sortedLU:
    thisSortType=raw_input("Sort options: screen_(n)ame, (t)weets, (f)ollowers, (fr)iends, (p)op-ratio, (s)pam-ratio, fr(i)endScore: ")
    if thisSortType=="f":
      ulS=sorted(thisPL, key=lambda x: thisPL[x]['followers'])
    elif thisSortType=="n":
      ulS=sorted(thisPL, key=lambda x: x, reverse=False)
    elif thisSortType=="s":
      ulS=sorted(thisPL, key=lambda x: thisPL[x]['sratio'])
    elif thisSortType=="t":
      ulS=sorted(thisPL, key=lambda x: thisPL[x]['tweets'])
    elif thisSortType=="fr":
      ulS=sorted(thisPL, key=lambda x: thisPL[x]['friends'])
    elif thisSortType=="p":
      ulS=sorted(thisPL, key=lambda x: thisPL[x]['pratio'])
    elif thisSortType=="i":
      ulS=sorted(thisPL, key=lambda x: thisPL[x]['friendScore'])
    else:
      inputErrorHandler(thisSortType,"invalid sort type!")
      continue
    sortedLU=True
  return ulS

###############################################
#
#screen_name:
#   'description'
#tweets: #followers: #friends:
#pop-ratio: #s-ratio:
#   'created_at' #   'id' #   'location' #   'verified'

def printUser(oneUser):
  if oneUser.friends_count == 0 or  oneUser.followers_count == 0:
    print "{:14}\t{}\t{}\t{} NOFLW and/or NOFRIENDS".format(oneUser.screen_name,oneUser.statuses_count,oneUser.followers_count,oneUser.friends_count)
  print bcolors.HEADER + "Screen_name: " + bcolors.ENDC \
  + "{:14}".format(oneUser.screen_name) + "\nName:{:14}\nDescription: \
  {}\nTweets:\t{}\tFollowers:\t{}\tFriends:\t{}\n".format(oneUser.name,oneUser.description,oneUser.statuses_count,oneUser.followers_count,oneUser.friends_count) \
  + bcolors.OKBLUE + "pop-ratio: " + bcolors.ENDC \
  + "{:7.2f}".format(round(float(oneUser.followers_count)/oneUser.friends_count,3)) \
  + bcolors.OKBLUE + "\tchorus-ratio: " + bcolors.ENDC \
  + "{:7.2f}".format(round(float(oneUser.statuses_count)/oneUser.followers_count,3)) \
  + "\ncreatead: {}\tid:{}\tlocation: {}\tverified: {}\n".format(time.strftime('%Y-%m-%d %H:%M', time.strptime(oneUser.created_at,'%a %b %d %H:%M:%S +0000 %Y')),oneUser.id,oneUser.location,oneUser.verified)
#  ts = time.strftime('%Y-%m-%d %H:%M', time.strptime(tweetL[0].created_at,'%a %b %d %H:%M:%S +0000 %Y'))

def printUfP(screen_name, oneUserProfile):
  if oneUserProfile['friends'] == 0 or oneUserProfile['followers'] == 0:
    print "{:14}\t{}\t{}\t{}\t{:6.2f}\t\t{:6.2f}NOFLW and/or NOFRIENDS".format(screen_name,oneUserProfile['tweets'],oneUserProfile['followers'],oneUserProfile['friends'])
  print bcolors.HEADER + "Screen_name: " + bcolors.ENDC \
  + "{:14}".format(screen_name) + "\nName:{:14}\nDescription: \
  {}\nTweets:\t{}\tFollowers:\t{}\tFriends:\t{}\n".format(screen_name,oneUserProfile['description'],oneUserProfile['tweets'],oneUserProfile['followers'],oneUserProfile['friends']) \
  + bcolors.BROWN + "pop-ratio: \t" + bcolors.ENDC  + "{:7.2f}".format(oneUserProfile['pratio']) \
  + bcolors.BROWN + "\tchorus-ratio: \t" + bcolors.ENDC  + "{:7.1f}".format(oneUserProfile['sratio']) \
  + bcolors.BROWN + "\ntweets/day: \t" + bcolors.ENDC  + "{:7.2f}".format(oneUserProfile['freqRatio']) \
  + bcolors.BROWN + "\tVolume: \t" + bcolors.ENDC  + "{:7}".format(oneUserProfile['volumeRatio']) \
  + bcolors.BROWN + "\nretweetScale: \t" + bcolors.ENDC  + "{:7.1f}".format(oneUserProfile['retweetRatio']) \
  + bcolors.BROWN + "\tdays10tweets: \t" + bcolors.ENDC  + "{:7}".format(oneUserProfile['timeFnumTweets']) \
  + "\ncreatead: {}\tid:{}\tlocation: {}\tverified: {}\n".format(oneUserProfile['account_create_datetime'],oneUserProfile['id'],oneUserProfile['location'],oneUserProfile['verified']) + bcolors.WHITE + "friendScore: " + bcolors.ENDC \
  + "{:7}".format(oneUserProfile['friendScore'])

###############################################
#
# journal and store actions
#
# by screen_name
# journal friends suggested, added, removed
# list friends existing, suggested, removed
# compare new suggestions with (existing||suggested||removed)

def getSets(file_handle):   # read file into set 
  my_set=set()
  file_handle.seek(0)
  my_set=set(line.strip() for line in file_handle)
  return my_set

def journal(j_fileHandle, userID, j_action):
  # capture uid and action (suggested, followed, unfollowed) and write to file
  if j_action in {"a","f","u","s"}:
    j_fileHandle.write(str(datetime.datetime.now()) + "," +  userID + "," + j_action + "\n")
    j_fileHandle.flush()
    return
  else: inputErrorHandler(j_action, "Cannot log. Invalid journal action!")

def storeAction(userID, myStoreAction):
  if myStoreAction in {"s", "f", "u"}:
    if myStoreAction=="s":
      if not userID in suggestSet:
        suggestSet.add(userID)
        suggest_file.write(userID + "\n")
        suggest_file.flush()
    elif myStoreAction=="f":
      if not userID in followSet:
        followSet.add(userID)
        follow_file.write(userID + "\n")
        follow_file.flush()
    else: #no valid options left, except unfollow
      if not userID in unfollowSet:
        unfollowSet.add(userID)
        unfollow_file.write(userID + "\n")
        unfollow_file.flush()
    return
  else: inputErrorHandler(myStoreAction, "Cannot store action. Invalid store action!")
  return

def getFriends(user={}): #get a user's friends from twitter
#  some_user = api.GetUser(screen_name="Manager_of_it")
#get list of friends
  try:
    theseFriends = api.GetFriends(total_count=2000)
  except: 
    callErrorHandler("Get friends failed!")
    theseFriends = {}
  return theseFriends

def getFollowers(user={}): #get a user's followers from twitter
#  some_user = api.GetUser(screen_name="Manager_of_it")
#get list of followers
  try:
    theseFollowers = api.GetFollowers(total_count=2900)
  except: 
    callErrorHandler("Get followers failed!")
    theseFollowers = {}
  return theseFollowers

###############################################
#
# review Users
#

def reviewUL(reviewUL):
  for i in range(len(reviewUL)): 
    printUser(reviewUL[i])
    validInputaI1 = False # validate input
    while not validInputaI1:
      actionInput = raw_input("(f)ollow, (s)kip, (m)ore info, e(x)it: ")
      if actionInput not in {'f','s','m','x'}:
        inputErrorHandler(actionInput, "Invalid option!")
      else:
        validInputaI1 = True
    if actionInput=='f': #process input
      followUser(reviewUL[i])
      journal(journal_file,reviewUL[i].screen_name,actionInput)
      storeAction(reviewUL[i].screen_name, actionInput)
      continue
    elif actionInput=='s':
      journal(journal_file,reviewUL[i].screen_name,actionInput)
      storeAction(reviewUL[i].screen_name, actionInput)
      continue
    elif actionInput=='m':
      tweetL=getUserTweets(reviewUL[i])
      printUserTweets(tweetL)
      validInputaI2 = False
      while not validInputaI2: #validate more input
        actionInput2= raw_input("(f)ollow, (s)kip: ")
        if actionInput2 not in {'f','s'}: 
          inputErrorHandler(actionInput2, "Invalid option!")
        else:
          validInputaI2 = True
      if actionInput2=='f':
        followUser(reviewUL[i])
      journal(journal_file,reviewUL[i].screen_name,actionInput2) 
      storeAction(reviewUL[i].screen_name, actionInput2)
      continue 
    break #only option left is exit, so get to it
                       
####################
#
# using Streams
#

def trackUsers():
    with open('output.txt', 'a') as f:
        # api.GetStreamFilter will return a generator that yields one status
        # message (i.e., Tweet) at a time as a JSON dictionary.
        for line in api.GetStreamFilter(track=USERS):
            f.write(json.dumps(line))
            f.write('\n')

#####
# rate limit foo
#
#
# convert epoch to date time:
# datetime.datetime.fromtimestamp(1479877104).strftime('%c')
#
# endpoint table:
# https://dev.twitter.com/rest/public/rate-limits
## 
# sample checks
# foo = api.CheckRateLimit('https://api.twitter.com/1.1/application/rate_limit_status.json')

def getFrRL():
  limit = api.CheckRateLimit('https://api.twitter.com/1.1/friends/list.json?resources=search')
  print datetime.datetime.fromtimestamp(limit.reset).strftime('%c') # convert epoch to readable time
  return limit

#####
#
# search foo
#
# results = api.GetSearch(raw_query="q=devops%20lang%3Aen%20since%3A2016-11-09%20until%3A2016-11-10&src=typd") # devops, language - english, since 2016-11-09 until 2016-11-10 

def q100(q_term="devops",q_lang="en",q_since="2016-01-01",q_until=str(datetime.date.today()),q_count=100,q_max_id=999999999999999999):
  print "searching: q100(q_term="+q_term+",q_lang="+q_lang+",q_since="+q_since+",q_until="+q_until+",q_count="+str(q_count)+",q_max_id="+str(q_max_id)+")"
  try:
    my_results = api.GetSearch(term=q_term, lang=q_lang, since=q_since, until=q_until, count=q_count, max_id=q_max_id)
  except: 
    callErrorHandler("Get search failed!")
    my_results = [] #null
    return my_results
#  print "len: ",len(my_results)
  return my_results

#############
#
# adding/removing followers 
#

def followUser(fU=None,id="",f_screen_name=""):
  if f_screen_name=="":
    f_screen_name=fU.screen_name
  try: 
    api.CreateFriendship(screen_name=f_screen_name, follow=True)
  except:
    callErrorHandler("Create friendship failed!")
    return
  print bcolors.BOLD + "Awesome! You are now following: {}\n".format(f_screen_name) + bcolors.ENDC 

def unfollowP(unf_screen_name=""):
  # api.GetSearch(term=q_term, lang=q_lang, since=q_since, until=q_until, count=q_count, max_id=q_max_id)
  try:
    api.DestroyFriendship(screen_name=unf_screen_name)
  except:
    callErrorHandler("Remove friendship failed!")
    return
  print bcolors.BOLD + "Goodbye! You have unfollowed: {}\n".format(unf_screen_name) + bcolors.ENDC 

def unfollowUser(unfU=None,id="",unf_screen_name=""):
  if unf_screen_name=="":
    unf_screen_name=unfU.screen_name
  try:
    api.DestroyFriendship(screen_name=unf_screen_name)
  except:
    callErrorHandler("Remove friendship failed!")
    return
  print bcolors.BOLD + "Goodbye! You have unfollowed: {}\n".format(unf_screen_name) + bcolors.ENDC 

####################
#
# Review followers
#
# Description:
#   followers User List
#   set followers by screen_name, subset not-following back by screen_name

# sort by: use existing sortLU()

# select review list:
#   all followers
#   not following back
#   filtered by last action

# Review list:
#   skip, more, unfollow, exit
#

def reviewFriends(thisFriendsUL,thisFriendsSet,thisNotFollowingBackSet):
  friendInput=False
  while not friendInput:
    friendOpt=raw_input("friend input: (s)ort, (r)eview, e(x)it: ")
    if friendOpt not in {"s","r","x"}:
       inputErrorHandler(friendOpt, "Try again!")
    elif friendOpt == "s":
      thisFriendsUL=sortLU(thisFriendsUL)
      printLU(thisFriendsUL)
    elif friendOpt =="r":
      getFriendReviewUL(thisFriendsUL,thisFriendsSet,thisNotFollowingBackSet)
      friendInput=True
    else: break #nothing left to do but exit
  return

def getFriendReviewUL(thisFriendsRwUL,thisFriendsRwSet,thisNotFollowingBackRwSet):
  friendReviewFilterInput=False
  while not friendReviewFilterInput:
    friendReviewFilterOpt=raw_input("review which list of followers: (a)ll, (n)ot following back, (l)ast status: ")
    if friendReviewFilterOpt not in {"a","n","l"}:
      inputErrorHandler(friendReviewFilterOpt, "Try again!")
    elif friendReviewFilterOpt=="a": # review for unfollow all followers
      print "reviewing all friends...\n"
      reviewFriendsAction(thisFriendsRwUL)
      friendReviewFilterInput=True
    elif friendReviewFilterOpt=="n":
      print "reviewing not following back...\n"
      # make UL from notFollowingBackSet
      notFBackUL=[]
      for i in range(len(thisFriendsRwUL)):
        if thisFriendsRwUL[i].screen_name in thisNotFollowingBackRwSet:
          notFBackUL.append(thisFriendsRwUL[i])
          continue
        else: continue
      reviewFriendsAction(notFBackUL)
      friendReviewFilterInput=True
    else: #nothing left but last action
      inputLastAction()
      # make UL with filter by last action
      # review lastActionFilterUL
      friendReviewFilterInput=True
  return 

def inputLastAction():
  print "figure out this last action, stuff\n"
  return

#def printSLUfProf(thisLP, thisSortedL): #print list of auto-avatar user profiles
#  print bcolors.HEADER + "screen_name\ttweets\tfollwers\t  friends\tpop-ratio\tspam-ratio\tfriendScore" + bcolors.ENDC
#  for i in range(len(thisSortedL)):
#            #        print i
#    if thisLP[thisSortedL[i]]['friends'] == 0 or thisLP[thisSortedL[i]]['followers'] == 0:
#      print "screen_name: {}\tNO FOLLOWERS AND\OR FRIENDS".format(thisSortedL[i])
#      continue
#    print "{0:14}\t{1}\t{2:8}\t{3:8}\t{4:5.1f}\t\t{5:5.1f}\t\t{6:5}".format(thisSortedL[i],thisLP[thisSortedL[i]]['tweets'],thisLP[thisSortedL[i]]['followers'],thisLP[thisSortedL[i]]['friends'],thisLP[thisSortedL[i]]['pratio'],thisLP[thisSortedL[i]]['sratio'],thisLP[thisSortedL[i]]['friendScore'])

def reviewPsU(this_p):
  thisSortedL=sortPs(this_p)
  for i in range(len(thisSortedL)):
    printUfP(thisSortedL[i], this_p[thisSortedL[i]])
    reviewPsOpt=raw_input("friend list review option: (s)kip, (u)nfollow, (m)ore, e(x)it: ")
    if reviewPsOpt not in {"s","u","m","x"}:
      inputErrorHandler(reviewPsOpt, "Invlid Entry.  Try again!")
    elif reviewPsOpt=='u':
      unfollowUser(unf_screen_name=prof) # remove user from followers
      journal(journal_file,prof,reviewPsOpt)
      storeAction(thisSortedL[i], reviewPsOpt)
      continue
    elif reviewPsOpt=='m':
      print "not implemented, sorry\n"
#      reviewFriendsMoreAction(this_friendActionUL[i])
      continue
    elif reviewPsOpt=='s':
      print "skip\n"
      continue
    else: break #nothing left to do but exit
  return

def reviewPsF(this_p):
  thisSortedL=sortPs(this_p)
  for i in range(len(thisSortedL)):
    printUfP(thisSortedL[i], this_p[thisSortedL[i]])
    reviewPsOpt=raw_input("friend list review option: (s)kip, (f)ollow, (m)ore, e(x)it: ")
    if reviewPsOpt not in {"s","f","m","x"}:
      inputErrorHandler(reviewPsOpt, "Invlid Entry.  Try again!")
    elif reviewPsOpt=='f':
      followUser(f_screen_name=thisSortedL[i]) # remove user from followers
      journal(journal_file,thisSortedL[i],reviewPsOpt)
      storeAction(thisSortedL[i], reviewPsOpt)
      continue
    elif reviewPsOpt=='m':
      print "not implemented, sorry\n"
#      reviewFriendsMoreAction(this_friendActionUL[i])
      continue
    elif reviewPsOpt=='s':
      journal(journal_file,thisSortedL[i],reviewPsOpt)
      storeAction(thisSortedL[i], reviewPsOpt)
      print "skip\n"
      continue
    else: break #nothing left to do but exit
  return

#def reviewPs(this_p):
#  for i,prof in enumerate(this_p):
#    printUfP(prof, this_p[prof])
#    reviewPsOpt=raw_input("friend list review option: (s)kip, (u)nfollow, (m)ore, e(x)it: ")
#    if reviewPsOpt not in {"s","u","m","x"}:
#      inputErrorHandler(reviewPsOpt, "Invlid Entry.  Try again!")
#    elif reviewPsOpt=='u':
#      unfollowUser(unf_screen_name=prof) # remove user from followers
#      journal(journal_file,prof,reviewPsOpt)
#      storeAction(prof, reviewPsOpt)
#      continue
#    elif reviewPsOpt=='m':
#      print "not implemented, sorry\n"
##      reviewFriendsMoreAction(this_friendActionUL[i])
#      continue
#    elif reviewPsOpt=='s':
#      print "skip\n"
#      continue
#    else: break #nothing left to do but exit
#  return

def reviewFriendsAction(this_friendActionUL):
  for i in range(len(this_friendActionUL)):
    printUser(this_friendActionUL[i])
    friendReviewActionOpt=raw_input("friend list review option: (s)kip, (u)nfollow, (m)ore, e(x)it: ")
    if friendReviewActionOpt not in {"s","u","m","x"}:
      inputErrorHandler(friendeviewActionOpt, "Try again!")
    elif friendReviewActionOpt=='u':
      unfollowUser(this_friendActionUL[i]) # remove user from followers
      journal(journal_file,this_friendActionUL[i].screen_name,friendReviewActionOpt)
      storeAction(this_friendActionUL[i].screen_name, friendReviewActionOpt)
      continue
    elif friendReviewActionOpt=='m':
      reviewFriendsMoreAction(this_friendActionUL[i])
      continue
    elif friendReviewActionOpt=='s':
      print "skip\n"
      continue
    else: break #nothing left to do but exit
  return

def reviewFriendsMoreAction(this_friendActionMoreUser):
  tweetL=getUserTweets(this_friendActionMoreUser)
  printUserTweets(tweetL)
  validInputaI2 = False
  while not validInputaI2: #validate more input
    actionOpt2=raw_input("(u)nfollow, (s)kip: ")
    if actionOpt2 not in {"u","s"}: 
      inputErrorHandler(actionOpt2, "Invalid option!")
    else: validInputaI2 = True
    if actionOpt2=="u":
      unfollowUser(this_friendActionMoreUser)
      journal(journal_file,this_friendActionMoreUser.screen_name,actionOpt2)
      storeAction(this_friendActionMoreUser.screen_name, actionOpt2)
  return

def printBanner():
  print "\n\n\n\n\n\n\n"
  print bcolors.BOLD + "   _____          __              _____                __                  " + bcolors.ENDC
  print bcolors.BOLD + "  /  _  \  __ ___/  |_  ____     /  _  \___  _______ _/ |______ _______   " + bcolors.ENDC
  print bcolors.BOLD + " /  /_\  \|  |  \   __\/  _ \   /  /_\  \  \/ /\__  \\\ __\__   \\\_  __ \ " + bcolors.ENDC
  print bcolors.BOLD + "/    |    \  |  /|  | (  <_> ) /    |    \   /  / __ \| |  / _ \|  |  \/   " + bcolors.ENDC
  print bcolors.BOLD + "\____|__  /____/ |__|  \____/  \____|__  /\_/  (____ /__| (___  /__|      " + bcolors.ENDC
  print bcolors.BOLD + "        \/                             \/           \/        \/          " + bcolors.ENDC
  print bcolors.BOLD + "\n\n"

#############
#
# get and print tweets for a user
#

def printUserTweets(p_utl):
  print "screen_name: {0}".format(p_utl[0].user.screen_name)
  for i in range(len(p_utl)):
    print "Tweet: {0}\tDate: {1}".format(p_utl[i].text,time.strftime('%Y-%m-%d %H:%M', time.strptime(p_utl[i].created_at,'%a %b %d %H:%M:%S +0000 %Y')))
#    ts = time.strftime('%Y-%m-%d %H:%M', time.strptime(tweetL[0].created_at,'%a %b %d %H:%M:%S +0000 %Y'))
    continue

def getUserTweets(g_utl,gUTcount=10): 
  try:
    utl=api.GetUserTimeline(screen_name=g_utl.screen_name,count=gUTcount)
  except:
    callErrorHandler("Get user timeline failed!")
    return
  return utl

# Profile Management
#
#
#
def getPs(gPq_term="devops", gPq_count="20"):
#  125 def getUfQ(q_term="devops",q_lang="en",q_since="2016-01-01",q_until=str(datetime.date.today()),q_count=20, q_max_id=99999999     9999999999):
  # q100(q_term="devops",q_lang="en",q_since="2016-01-01",q_until=str(datetime.date.today()),q_count=100,q_max_id=9999999999     99999999):
  ul=getUfQ(q_term=gPq_term, q_count=gPq_count)
  tl=getTL(ul)
  pLims=getProfileLimitsPoints()
  pLists=getProfileLists()
  thisListProfs=getListProfileDicts(ul,tl,pLims,pLists)
  return thisListProfs

def getProfileDict(userObject, userStatusObject, pLims, pLists):
  thisProfileDict=buildProfileDict(userObject, userStatusObject)
  thisFriendScore=computeFriendScore(thisProfileDict, pLims, pLists)
  thisProfileDict=storeFriendScore(thisProfileDict,thisFriendScore)
  return thisProfileDict

# profileListDicts=[key=screen_name, profileDict]
def getListProfileDicts(userList, statusList, pLims, pLists):
  thisListProfiles={}
  for i in range(len(userList)):
    print i, "screen_name: ",  userList[i].screen_name
    thisProfileDict=buildProfileDict(userList[i], statusList[i])
    thisFriendScore=computeFriendScore(thisProfileDict, pLims, pLists)
    thisProfileDict=storeFriendScore(thisProfileDict,thisFriendScore)
    thisListProfiles[userList[i].screen_name]=thisProfileDict
  return thisListProfiles

# profileDict:
# user object: empirical, 7 items: list[tweets, followers, friends, account_create_datetime, pic, bio, verified]
# status object: last_status_datetime, offset_status_datetime, retweets]
#
# calculated 1st order, pratio(followers/friends), sratio(tweets/followers), daysOld(now-account create),
# calculated 2nd order, freqRatio(tweets/daysOld),   daysLast(now-last status),timeFnumTweets(now-offset_status_datetime)  volumeRatio(numTweets/timeFnumTweets), retweetRatio(retweets/numTweets)
# calculted 3rd order, friendsScore(baysean),

def buildProfileDict(userObject, userStatusObject):
  thisProfileDict={
  # 1st order profile attributes
      'id': userObject.id,
      'screen_name': userObject.screen_name,
      'tweets': userObject.statuses_count,
      'followers': userObject.followers_count,
      'friends': userObject.friends_count,
      'account_create_datetime': datetime.datetime.strptime(userObject.created_at,'%a %b %d %H:%M:%S +0000 %Y'),
      'picBool': getPicState(userObject.profile_image_url),
      'bioBool': getBioState(userObject.description),
      'description': userObject.description,
      'verified': userObject.verified,
      'last_status_datetime': datetime.datetime.strptime(userStatusObject[0].created_at,'%a %b %d %H:%M:%S +0000 %Y'),
      'offset_status_datetime': datetime.datetime.strptime(userStatusObject[len(userStatusObject)-1].created_at,'%a %b %d %H:%M:%S +0000 %Y'),
      'retweets': getRetweets(userStatusObject),
      'pratio': userObject.followers_count/float(userObject.friends_count),
      'sratio': userObject.statuses_count/float(userObject.followers_count),
      'location': userObject.location,
      }
  # 2nd order profile attributes
  thisProfileDict['daysOld']=getDaysOld(thisProfileDict['account_create_datetime'])
  thisProfileDict['freqRatio']=userObject.statuses_count/float(thisProfileDict['daysOld'])
  thisProfileDict['daysLast']=(datetime.datetime.now()-thisProfileDict['last_status_datetime']).days
  thisProfileDict['timeFnumTweets']=getTimeFnumTweets(thisProfileDict['offset_status_datetime'])
  thisProfileDict['volumeRatio']=len(userStatusObject)/thisProfileDict['timeFnumTweets']
  thisProfileDict['retweetRatio']=(thisProfileDict['retweets'])/float(len(userStatusObject))
  return thisProfileDict

def getDaysOld(thisAcdt):
  if (datetime.datetime.now()-thisAcdt).days <= 0:
    return 1
  else: return (datetime.datetime.now()-thisAcdt).days 

def getTimeFnumTweets(offsetDT):
  thisTimeFnumTweets=(datetime.datetime.now()-offsetDT).days
  if thisTimeFnumTweets<=0:
    thisTimeFnumTweets=1
  return thisTimeFnumTweets

def getRetweets(statusObject):
  thisNumRetweets=0
  for i in range(len(statusObject)):
    if not re.match('^RT', statusObject[i].text):
      thisNumRetweets=thisNumRetweets+1
      continue
  return thisNumRetweets

def getPicState(thisProfileImage): #TODOs: define
  if re.match('.*default.*', thisProfileImage):
    thisPicState=False
  else: 
    thisPicState=True
  return thisPicState

def getBioState(description):
  if description == "": 
    thisBioState=False
  else: thisBioState=True
  return thisBioState

def storeFriendScore(thisProfileDict, thisScore):
  thisProfileDict['friendScore']=thisScore
  return thisProfileDict

# profileLimits:
# dict[key=attributeName, value=value]
#
#def getProfileLimits():
#  thisProfileLimits = {
#      'friendMin': 20,
#      'followersMin': 20,
#      'pratioMax': 15,
#      'sratioMax': 15,
#      'retweetRatioMax': 0.9,
#      'tweetsMax': 100000, #100,000
#      'tweetsMin': 100,
#      'volumeRatioMin': 0,
#      'volumeRatioMax': 50,
#      'freqRatioMax': 10,
#      'accountAgeMax': 1825, #5 years in days
#      'accountAgeMin': 90,
#      'activeMax': 30,
#      'activeMin': 2,
#      'timeFnumTweetsMax': 45, #days
#      'timeFnumTweetsMin': 5 #days
#      }
#  return thisProfileLimits

# profileLists:
# dict[key=listName, value=list]
#        2x2 items:  "list{In,Not}": location, screen_name
#
def getProfileLists():
  thisProfileLists = {
      'screen_namesNot': ['tmj', 'job', 'anon', 'bot'],
      'locationIn': ['Cambridge', 'Massachusetts', 'San Francisco', 'California', 'Providence', 'SF', 'RI', 'CA', 'MA']
      }
  return thisProfileLists

# profileLimitsPoints:
# dict[key=attributeName, tuple(limit,points)]
#
def getProfileLimitsPoints():
  thisLimitsPointsList = {
      'screen_nameBool': ("Boolean",-99),
      'friendMin': (20,-99),
      'followersMin': (20,-99),
      'pratioMax': (15,-99), #pop-ratio
      'sratioMax': (15,-99), #chorus-ratio
      'activeMax': (30,-99),
      'retweetRatioMax': (0.9,-99), #retweetScale
      'tweetsMax': (200000,-80), #100,000,
      'volumeRatioMax': (9,-75),
      'timeFnumTweetsMax': (15,-70), #days
      'picBool': ("Boolean",-50),
      'timeFnumTweetsMin': (1,-50), #days
      'bioBool': ("Boolean",-40),
      'volumeRatioMin': (0,-15), #tweets/day
      'freqRatioMax': (10,-20), #tweets/day
      'accountAgeMin': (90,-10),
      'tweetsMin': (100,-10),
      'activeMin': (2,-10),
      'verified': ("Boolean",10),
      'locationBool': ("Boolean",20),
      'accountAgeMax': (1825,30) #5 years in days
      }
  return thisLimitsPointsList

def printShowWork(limitName, thisLims,  runFriendScore):
  print "item: ", limitName, ",\tLimit: ", thisLims[limitName][0], ",\tPoints: ", thisLims[limitName][1], ",\tScore: ", runFriendScore
  return

def computeFriendScore(profileDict, pLims, pLists, showWork=True):
  thisFriendScore=100
  if showWork: print "Friend score init: ", thisFriendScore
  if profileDict['friends'] < pLims['friendMin'][0]:
    thisFriendScore=thisFriendScore+pLims['friendMin'][1]
    if showWork: printShowWork('friendMin', pLims, thisFriendScore)
  if profileDict['followers'] < pLims['followersMin'][0]:
    thisFriendScore=thisFriendScore+pLims['followersMin'][1]
    if showWork: printShowWork('followersMin', pLims, thisFriendScore)
  if profileDict['pratio'] > pLims['pratioMax'][0]:
    thisFriendScore=thisFriendScore+pLims['pratioMax'][1]
    if showWork: printShowWork('pratioMax', pLims, thisFriendScore)
  if profileDict['sratio'] > pLims['sratioMax'][0]:
    thisFriendScore=thisFriendScore+pLims['sratioMax'][1]
    if showWork: printShowWork('sratioMax', pLims, thisFriendScore)
  if profileDict['retweetRatio'] > pLims['retweetRatioMax'][0]:
    thisFriendScore=thisFriendScore+pLims['retweetRatioMax'][1]
    if showWork: printShowWork('retweetRatioMax', pLims, thisFriendScore)
  if profileDict['tweets'] > pLims['tweetsMax'][0]:
    thisFriendScore=thisFriendScore+pLims['tweetsMax'][1]
    if showWork: printShowWork('tweetsMax', pLims, thisFriendScore)
  if profileDict['tweets'] < pLims['tweetsMin'][0]:
    thisFriendScore=thisFriendScore+pLims['tweetsMin'][1]
    if showWork: printShowWork('tweetsMin', pLims, thisFriendScore)
  if profileDict['volumeRatio'] <  pLims['volumeRatioMin'][0]:
    thisFriendScore=thisFriendScore+pLims['volumeRatioMin'][1]
    if showWork: printShowWork('volumeRatioMin', pLims, thisFriendScore)
  if profileDict['volumeRatio'] >  pLims['volumeRatioMax'][0]:
    thisFriendScore=thisFriendScore+pLims['volumeRatioMax'][1]
    if showWork: printShowWork('volumeRatioMax', pLims, thisFriendScore)
  if profileDict['freqRatio'] > pLims['freqRatioMax'][0]:
    thisFriendScore=thisFriendScore+pLims['freqRatioMax'][1]
    if showWork: printShowWork('freqRatioMax', pLims, thisFriendScore)
#  if profileDict['volumeRatio'] > pLims['volumeRatioMax'][0]:
#    thisFriendScore=thisFriendScore+pLims['volumeRatioMax'][1]
#    if showWork: printShowWork('volumeRatioMax', pLims, thisFriendScore)
  if profileDict['daysOld'] > pLims['accountAgeMax'][0]:
    thisFriendScore=thisFriendScore+pLims['accountAgeMax'][1]
    if showWork: printShowWork('accountAgeMax', pLims, thisFriendScore)
  if profileDict['daysOld'] < pLims['accountAgeMin'][0]:
    thisFriendScore=thisFriendScore+pLims['accountAgeMin'][1]
    if showWork: printShowWork('accountAgeMin', pLims, thisFriendScore)
  if profileDict['daysLast'] > pLims['activeMax'][0]:
    thisFriendScore=thisFriendScore+pLims['activeMax'][1]
    if showWork: printShowWork('activeMax', pLims, thisFriendScore)
  if profileDict['daysLast'] > pLims['activeMin'][0]:
    thisFriendScore=thisFriendScore+pLims['activeMin'][1]
    if showWork: printShowWork('activeMin', pLims, thisFriendScore)
  if profileDict['timeFnumTweets'] > pLims['timeFnumTweetsMax'][0]:
    thisFriendScore=thisFriendScore+pLims['timeFnumTweetsMax'][1]
    if showWork: printShowWork('timeFnumTweetsMax', pLims, thisFriendScore)
  if profileDict['timeFnumTweets'] < pLims['timeFnumTweetsMin'][0]:
    thisFriendScore=thisFriendScore+pLims['timeFnumTweetsMin'][1]
    if showWork: printShowWork('timeFnumTweetsMin', pLims, thisFriendScore)
  if listBool(profileDict['location'],pLists['locationIn']): #location
    thisFriendScore=thisFriendScore+pLims['locationBool'][1]
    if showWork: printShowWork('locationBool', pLims, thisFriendScore)
  if listBool(profileDict['screen_name'],pLists['screen_namesNot']): #screen_name
    thisFriendScore=thisFriendScore+pLims['screen_nameBool'][1]
    if showWork: printShowWork('screen_nameBool', pLims, thisFriendScore)
  if not profileDict['picBool']:
    thisFriendScore=thisFriendScore+pLims['picBool'][1]
    if showWork: printShowWork('picBool', pLims, thisFriendScore)
  if not profileDict['bioBool']:
    thisFriendScore=thisFriendScore+pLims['bioBool'][1]
    if showWork: printShowWork('bioBool', pLims, thisFriendScore)
  if profileDict['verified']:
    thisFriendScore=thisFriendScore+pLims['verified'][1]
    if showWork: printShowWork('verified', pLims, thisFriendScore)
  return thisFriendScore

def listBool(thisAttrib, thisList):
  listBool=False
  for i in range(len(thisList)):
    regex=".*" + thisList[i] + ".*"
    if re.match(regex, thisAttrib, re.IGNORECASE):
      listBool=True
  return listBool

def locationIn(thisLocation, thisLocationList):
  locationInBool=False
  for i in range(len(thisLocationList)):
    regex=".*" + thisLocationList[i] + ".*"
    if re.match(regex, thisLocation, re.IGNORECASE):
      locationInBool=True
  return locationInBool

def screen_namesNot(thisScreen_name, thisScreenNameList):
  screen_nameNotBool=False
  for i in range(len(thisScreenNameList)):
    regex=".*" + thisScreenNameList[i] + ".*"
    if re.match(regex, thisScreen_name, re.IGNORECASE):
      screenNameBool=True
  return screen_nameNotBool

# rulesList: 
#    friends < friendMin: -20
#    followers < followersMin: -20
#    pratio > pratioMax: -99
#    sratio > sratioMax: -99

#    retweetRatio > retweetRatioMax: -90       --> need query, retweets per last 20 tweets
#    tweets > tweetsMax: -10
#    tweets < tweetsMin: -10
#    volumeRatio <  volumeRatioMin: -15
#    volumeRatio >  volumeRatioMax: -75
#    freqRatio > freqRatioMax: -20
#    volumeRatio > volumeRatioMax: -20
#    daysOld > accountAgeMax: +20    --> need query, created at time
#    daysOld < accountAgeMin: -10
#    daysLast > activeMax: -99    --> need query, last active date
#    daysLast > activeMin: -10
#    timeFnumTweets > timeFnumTweetsMax: -20
#    timeFnumTweets < timeFnumTweetsMin: -50

#
#    screen_name in {'job', 'anon' , 'bot'}: -99 --> need query, screen_name
#    location in {SF, BOS, RI}: +20    --> need query, location
#    no bio pic: -50              --> need query, bio pic
#    no bio: -20                  --> bio
#    verified: +10                --> verified

#    location not USA(optional, if country specified AND NOT "usa" )
#    language not english: -99 
#    location unspecified: -10 



########################
#
# error handling
#
#
def inputErrorHandler(bad_input=None, message=""):
  print bcolors.FAIL + "Invalid input: {}\tMessage: {}".format(bad_input,message) + bcolors.ENDC

def callErrorHandler(message=""):
  print bcolors.FAIL + "Message: {}".format(message) + bcolors.ENDC

class bcolors:
      HEADER = '\033[95m'
      OKBLUE = '\033[94m'
      OKGREEN = '\033[92m'
      BROWN = '\033[33m'
      WHITE = '\033[37m'
      WARNING = '\033[93m'
      FAIL = '\033[91m'
      ENDC = '\033[0m'
      BOLD = '\033[1m'
      UNDERLINE = '\033[4m'

def showSearchOptions(show_term, show_lang, show_since, show_until, show_count, max_id):
  print "\nCurrent search options:"
  print "search_term=", show_term
  print "lang=", show_lang
  print "since=", show_since
  print "until=", show_until
  print "count=", show_count
  print "max_id=", max_id
  return


#############################
#
## getReady
#
#

#from Files
suggestSet=getSets(suggest_file)
print "suggestSet len: ", len(suggestSet)
followSet=getSets(follow_file)
print "followSet len: ", len(followSet)
unfollowSet=getSets(unfollow_file)
print "unfollowSet len: ", len(unfollowSet)
touchedSet=set.union(suggestSet,followSet,unfollowSet)

#from API
friendsSet=set()
getMyFriends=raw_input("(g)et friends? ")
if getMyFriends == "g":
  followingUL=getFriends()
  friendsSet=convertULtoSetSNs(followingUL)
  print "friendSet len: ", len(friendsSet)
  touchedSet=set.union(suggestSet,followSet,unfollowSet,friendsSet)
  print "touchedSet len: ", len(touchedSet)
else: followingUL = {}

followersSet=set()
getMyFollowers=raw_input("(g)et followers? ")
if getMyFollowers == "g":
  followersUL=getFollowers()
  followersSet=convertULtoSetSNs(followersUL)
  print "followersSet len: ", len(followersSet)
else: followersUL = {}

notFollowingBackSet=set()
notFollowingBackSet=friendsSet.difference(followersSet)
print "notFollowngBackSet len: ", len(notFollowingBackSet)

#############################
#
## goMain
#
#

def goMain():
  printBanner()
  print bcolors.HEADER + "Hi, I'm your auto-avatar, bitxh!\n" + bcolors.ENDC
  print "I will help you engage users on twitter.\n\n \
      I can do these things:\n \
         (g)et a list of tweeters\n \
         (s)ort a list of tweeters\n \
         (f)ollow users\n \
         (u)nfollow friends\n \
         (q)uit\n"
  ul=[]
  q_term="devops"
  q_lang="en"
  q_since="2016-01-01"
  q_until=str(datetime.date.today())
  q_count=20
  q_max_id=999999999999999999
  thisTodo = raw_input("What do you want auto-avatar to do? ")
  while True:
    if thisTodo == 'g':
      showSearchOptions(q_term,q_lang,q_since,q_until,q_count,q_max_id)
      touchedSet=set.union(suggestSet,followSet,unfollowSet,friendsSet)
      print "touchedSet len: ", len(touchedSet)
      searching=False
      while not searching:
        searchOrChange=raw_input("input search term or (c)hange search options: ")
        if not searchOrChange=="c":
          if not searchOrChange=="":
            q_term=searchOrChange
            print "search: ", searchOrChange
            q_max_id=999999999999999999 #reset max_id for new search query
          print "search: q100(q_term="+q_term+",q_lang="+q_lang+",q_since="+q_since+",q_until="+q_until+",q_count="+str(q_count)+",q_max_id="+str(q_max_id)+")"
          r=q100(q_term,q_lang,q_since,q_until,q_count,q_max_id)
          q_max_id=getMaxId(r) #get max_id from a list of statuses
          ul=convertSLtoUL(r) #convert status to users
          ul=getULU(ul) #clean: remove dup users
          ul=getFreshUL(ul,touchedSet) #clean: remove already examined users
#          ul=getRidNullUsers(ul) #clean: protected users and any other miscreants
          tl=getTL(ul) 
          pLims=getProfileLimitsPoints()
          pLists=getProfileLists()
          listProfs=getListProfileDicts(ul,tl,pLims,pLists)
          printLUfProf(listProfs)  #report
          print "Len, ul:",len(ul)
          searching=True
        else:
          optInput=False
          while not optInput:
            optToChange=raw_input("change search options:(l)ang, (s)ince, (u)ntil, (c)ount: ")
            if optToChange == "l":
              q_langInp=raw_input("langauge("+ q_lang+"): ")
              if not q_langInp=="":
                q_lang=q_langInp
              optInput=True
            elif optToChange == "s":
              q_sinceInp=raw_input("since("+ q_since+"): ")
              if not q_sinceInp=="":
                q_since=q_sinceInp
              optInput=True
            elif optToChange == "u":
              q_untilInp=raw_input("until("+q_until+"): ")
              if not q_untilInp=="":
                q_input=q_untilInp
              optInput=True
            elif optToChange == "c":
              q_countInp=raw_input("count("+str(q_count)+"): ")
              if not q_countInp=="":
                q_count=q_countInp
              optInput=True
            else:
              inputErrorHandler(optToChange, "Try again!")
            showSearchOptions(q_term,q_lang,q_since,q_until,q_count,q_max_id)

    elif thisTodo == "f":
      if ul == []:
        print bcolors.FAIL + "Hey genius! You need to (g)et a list BEFORE you begin to follow!\n" + bcolors.ENDC
      else:
        reviewPsF(listProfs)
    elif thisTodo == "s":
      if ul == []:
        print bcolors.FAIL + "Hey genius! You need to (g)et a list BEFORE you try to sort!\n" + bcolors.ENDC
      else:
        listProfs=sortPs(listProfs)
        printLUfProf(listProfs)
#        ul=sortPs(ul)
#        printLU(ul)
    elif thisTodo == "q":
      print bcolors.BOLD + bcolors.HEADER + "How's that?\n" + bcolors.ENDC
      exit()
    elif thisTodo == "u":
      reviewPsU(listProfs)
#      reviewFriends(followingUL,followersSet,notFollowingBackSet)
    else:
      inputErrorHandler(thisTodo,"Try again!") 
    thisTodo = raw_input("\nMain options: (g)et, (s)ort, (f)ollow, (u)nfollow or (q)uit: ")

def closeFiles():
  journal_file.close()
  suggest_file.close()
  follow_file.close()
    
goMain()
closeFiles()
