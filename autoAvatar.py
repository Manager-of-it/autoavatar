#!/usr/bin/python 

######################################################################
#
# Name: autoavator.py
# Version: 2.0
# Description: Twitter tool written in python and using a python API to select users to follow
# Purpose: Generate a list of possible users to follow on twitter
# Author: Manager_of_it
# Date: November 24, 2016
# Version 2.0: September 4, 2017

# TODOS
# functional: 
#   query non-followers by dates ago followed
#   unFollow by account last activity date
#
# file mangement:
#   store friendProfile in database 
#   store aavatar.log in database
#   refresh friendProfile, friends, followers local file from API
# API management:
#   manage rate limits for getting friends, followers
# auto automation:
#   store list of queries to loop over -- DONE
#   loop over a list of profiles, friend or skip
#   generate activity report of automation
#
#   query non-followers by dates ago followed
#

import datetime
import json
import oauth2
import os
import re
import sys
import time
import twitter
import traceback
from random import randint
from  dictAutoAvatar import *

reload(sys) 
sys.setdefaultencoding('UTF8') #set default encoding from ascii to UTF8

########################
#
# error handling
#
#

def printTwitLimits():
  print "application/rate_limit_status: ", api.CheckRateLimit('https://api.twitter.com/1.1/application/rate_limit_status.json?resources=statuses')
  print "friends/list: ", api.CheckRateLimit('https://api.twitter.com/1.1/friends/list.json?resources=friends')
  print "lists/members: ", api.CheckRateLimit('https://api.twitter.com/1.1/lists/members.json?')
  print "account/verify_creds: ", api.CheckRateLimit('https://api.twitter.com/1.1/account/verify_credentials?')
  print "search/tweets: ", api.CheckRateLimit('https://api.twitter.com/1.1/search/tweets?')
  print "statuses/lookup: ", api.CheckRateLimit('https://api.twitter.com/1.1/statuses/lookup?')
  print "users/search: ", api.CheckRateLimit('https://api.twitter.com/1.1/users/search?')
  print "statuses/user_timeline: ", api.CheckRateLimit('https://api.twitter.com/1.1/statuses/user_timeline?')
#

def inputErrorHandler(bad_input=None, message="", debug=False):
  print bcolors.FAIL + "Invalid input: {}\tMessage: {}".format(bad_input,message) + bcolors.ENDC
def callErrorHandler(message=""):
  print bcolors.FAIL + "Message: {}".format(message) + bcolors.ENDC
  printTwitLimits()
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

#-----------------------------------------------------------------------
# get users, print
#-----------------------------------------------------------------------

def getTL(thisUL,man_limit=0, debug=False):
  thisTL=[]
  if len(thisUL)>=900:
    limit=850
  else: 
    limit=len(thisUL)
  if man_limit != 0: 
    limit=man_limit
  for i in range(limit):
    sys.stdout.write('.')
    if i%10 == 0: sys.stdout.write(str(i))
    sys.stdout.flush()
    thisTL.append(getUserTweets(thisUL[i]))
  print ""
  return thisTL

def getMaxId(my_statusList, debug=False):
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

def getULU(thisUL):  #get unique list of users -- scrub dups
    # order preserving
    uniqueUL = []
    for e in thisUL:
        if e not in uniqueUL:
             uniqueUL.append(e)
    return uniqueUL

#get unexamined list of users -- remove already touched users
def getFreshUL(thisUL,thisTouchedSet):
  print "pre-fresh: "+str(len(thisUL))
  cleanUL=list(thisUL)
  for i in range(len(thisUL)):
    if thisUL[i].screen_name in thisTouchedSet:
      print "remove " + thisUL[i].screen_name + " from User List"
      cleanUL.remove(thisUL[i])
    else: continue
  print "fresh: "+str(len(cleanUL))
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

def printLUfProf(thisLP, debug=False): #print list of auto-avatar user profiles
    print bcolors.HEADER + "screen_name\ttweets\tfollwers\t  friends\tpop-ratio\tchorus-ratio\tfriendScore" + bcolors.ENDC
    for i,prof in enumerate(thisLP):
        if debug==True: print "DEBUG: i, prof: ", i, prof
        if debug==True: print "DEBUG: type(thisLP)", type(thisLP), "thisLP[prof]: ", thisLP[prof]
        if thisLP[prof]['friends'] == 0 or thisLP[prof]['followers'] == 0:
          print "screen_name: {}\tNO FOLLOWERS AND\OR FRIENDS".format(prof)
          continue
        print "{0:14}\t{1}\t{2:8}\t{3:8}\t{4:5.1f}\t\t{5:5.1f}\t\t{6:5}".format(prof,thisLP[prof]['tweets'],thisLP[prof]['followers'],thisLP[prof]['friends'],thisLP[prof]['pratio'],thisLP[prof]['sratio'],thisLP[prof]['friendScore'])

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

def sortPs(thisPL, debug=False):
# listOfProfilesDict(key=screen_name, profileDict(keys=attribs, attribsValues)))
  sortedLU=False
  if debug==True: print "DEBUG: sortPs() type(thisPL): ", type(thisPL)
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
  if debug==True: print "DEBUG: sortPs() type(ulS): ", type(ulS)
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

def journal(j_fileHandle, userID, j_action, search_term="not_specified"):
  # capture uid and action (suggested, followed, unfollowed) and write to file
  if j_action in {"a","f","u","s"}:
    j_fileHandle.write(str(datetime.datetime.now()) + "," +  userID + "," + j_action + "," + search_term + "\n")
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
    theseFriends = api.GetFriends(total_count=2500)
  except: 
    traceback.print_exc()
    traceback.print_stack()
    callErrorHandler("Get friends failed!")
    theseFriends = {}
  return theseFriends

def getFollowers(user={}): #get a user's followers from twitter
#  some_user = api.GetUser(screen_name="Manager_of_it")
#get list of followers
  try:
    theseFollowers = api.GetFollowers(total_count=2500)
  except: 
    traceback.print_exc()
    traceback.print_stack()
    callErrorHandler("Get followers failed!")
    theseFollowers = {}
  return theseFollowers

# convert epoch to date time:
# datetime.datetime.fromtimestamp(1479877104).strftime('%c')
#
# endpoint table:
# https://dev.twitter.com/rest/public/rate-limits
## 

def getFrRL():
  limit = api.CheckRateLimit('https://api.twitter.com/1.1/friends/list.json?resources=search')
  print datetime.datetime.fromtimestamp(limit.reset).strftime('%c') # convert epoch to readable time
  return limit

#####
#
# search foo
#


def q100(q_term="devops",q_lang="en",q_since="2016-01-01",q_until=str(datetime.date.today()),q_count=100,q_max_id=999999999999999999, debug=False):
  print "searching: q100(q_term="+q_term+",q_lang="+q_lang+",q_since="+q_since+",q_until="+q_until+",q_count="+str(q_count)+",q_max_id="+str(q_max_id)+")"
  try:
    my_results = api.GetSearch(term=q_term, lang=q_lang, since=q_since, until=q_until, count=q_count, max_id=q_max_id)
  except: 
    traceback.print_exc()
    traceback.print_stack()
    callErrorHandler("Get search failed!")
    my_results = [] #null
    return my_results
#  print "len: ",len(my_results)
  return my_results

#############
#
# adding/removing followers 
#

def followUser(fU=None,id="",f_screen_name="", search_term="not_specified"):
  if f_screen_name=="":
    f_screen_name=fU.screen_name
  try: 
    api.CreateFriendship(screen_name=f_screen_name, follow=True)
  except:
    traceback.print_exc()
    traceback.print_stack()
    callErrorHandler("Create friendship failed!")
    return False
  print bcolors.BOLD + "Awesome! You are now following: {}\n".format(f_screen_name) + bcolors.ENDC 
  return True

def unfollowP(unf_screen_name=""):
  # api.GetSearch(term=q_term, lang=q_lang, since=q_since, until=q_until, count=q_count, max_id=q_max_id)
  try:
    api.DestroyFriendship(screen_name=unf_screen_name)
  except:
    traceback.print_exc()
    traceback.print_stack()
    callErrorHandler("Remove friendship failed!")
    return False
  print bcolors.BOLD + "Goodbye! You have unfollowed: {}\n".format(unf_screen_name) + bcolors.ENDC 
  return True

def unfollowUser(unfU=None,id="",unf_screen_name=""):
  if unf_screen_name=="":
    unf_screen_name=unfU.screen_name
  try:
    api.DestroyFriendship(screen_name=unf_screen_name)
  except:
    traceback.print_exc()
    traceback.print_stack()
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

def reviewFriends(thisFriendsUL,thisFriendsSet,thisNotFollowingBackSet, debug=False):
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

def unfollowUserCount(thisFriendsRwUL,thisFriendsRwSet,thisNotFollowingBackRwSet, unfollowCount):
  notFBackUL=[]
  unfollowCount=int(unfollowCount)
  for i in range(len(thisFriendsRwUL)):
    if thisFriendsRwUL[i].screen_name in thisNotFollowingBackRwSet:
      notFBackUL.append(thisFriendsRwUL[i])
      continue
    else: continue
  if len(notFBackUL)<unfollowCount:
    print "You only have ", len(notFBackUL), "tweeters not following you back. Setting that to unfollowCount."
    unfollowCount=len(notFBackUL)
  debug=True
  if debug==True: print "DEBUG: unfollow loop() notFBackUL:", notFBackUL, "type(notFBackUL): ", type(notFBackUL)
  if debug==True: print "DEBUG: unfollow loop() untouchedSet: ", untouchedSet
  for i in range(unfollowCount):
    print "unfollow loop() i:",i, "type(i): ", type(i)
    print "unfollow loop() notFBackUL[i].screen_name: ", notFBackUL[i].screen_name
    print "unfollow loop() unfollowCount", unfollowCount
    if notFBackUL[i].screen_name not in untouchedSet:
      unfollowUser(notFBackUL[i]) # remove user from followers
      journal(journal_file,notFBackUL[i].screen_name,"u")
      storeAction(notFBackUL[i].screen_name, "u")
      chillOut()
      continue
    else: 
      print bcolors.UNDERLINE + "You have followed: {}. Not Touching!\n".format(notFBackUL[i].screen_name) + bcolors.ENDC

def getFriendReviewUL(thisFriendsRwUL,thisFriendsRwSet,thisNotFollowingBackRwSet):
  friendReviewFilterInput=False
  while not friendReviewFilterInput:
    friendReviewFilterOpt=raw_input("review which list of followers: (a)ll, (n)ot following back, (c)ountLIFO, (l)ast status, e(x)it: ")
    if friendReviewFilterOpt not in {"a","n","c","l","x"}:
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
    elif friendReviewFilterOpt=="c": #UNFOLLOW COUNT
      unfollowCount=raw_input("unfollow how many of the latest not following back. unfollowCount= ")
      while (not unfollowCount.isdigit()) or unfollowCount<=0:
        unfollowCount=raw_input("Invalid entry! unfollowCount must be a number >0. Input unfollowCount= ")
      gettingConfirm=True
      while gettingConfirm:
        confirm_list=raw_input("You entered unfollowCount="+str(unfollowCount)+" please (c)onfirm or (d)iscard: ")
        if confirm_list=='d':
          print "discarding list and starting over."
          return
        if confirm_list=='c':
          unfollowUserCount(thisFriendsRwUL,thisFriendsRwSet,thisNotFollowingBackRwSet,unfollowCount)
        else:
          inputErrorHandler(confirm_list, "Invalid option!")
        gettingConfirm=False
    elif friendReviewFilterOpt=="l":  #last status
      inputLastAction()
      # make UL with filter by last action
      # review lastActionFilterUL
      friendReviewFilterInput=True
    elif friendReviewFilterOpt=="x": #exit
      break
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

def reviewPsU(this_p, this_tl):
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
      if debug==True: print "DEBUG: reviewPsF() type(thisSortedL[i]: ", type(thisSortedL[i]), "\nthis_tl[i]: ", this_tl[i], "\nthis_tl[i][1]", this_tl[i][0].user.screen_name
      for r in range(len(thisSortedL)):
        if thisSortedL[i]==this_tl[r][0].user.screen_name:
          reviewMoreFromP(thisSortedL[i], this_tl[r]) # i is index of thisSortedL in sort order, but this_tl is in retrieved order
      continue
    elif reviewPsOpt=='s':
      print "not implemented, sorry\n"
#      reviewFriendsMoreAction(this_friendActionUL[i])
      continue
    elif reviewPsOpt=='s':
      print "skip\n"
      continue
    else: break #nothing left to do but exit
  return


def reviewPsF(this_p, this_tl, debug=False):
  thisSortedL=sortPs(this_p)
  for i in range(len(thisSortedL)):
    printUfP(thisSortedL[i], this_p[thisSortedL[i]])
    reviewPsOpt=raw_input("friend list review option: (s)kip, (f)ollow, (m)ore, e(x)it: ")
    if reviewPsOpt not in {"s","f","m","x"}:
      inputErrorHandler(reviewPsOpt, "Invlid Entry.  Try again!")
    elif reviewPsOpt=='f':
      followUser(f_screen_name=thisSortedL[i])
      journal(journal_file,thisSortedL[i],reviewPsOpt)
      storeAction(thisSortedL[i], reviewPsOpt)
      continue
    elif reviewPsOpt=='m':
      if debug==True: print "DEBUG: reviewPsF() type(thisSortedL[i]: ", type(thisSortedL[i]), "\nthis_tl[i]: ", this_tl[i], "\nthis_tl[i][1]", this_tl[i][0].user.screen_name
      for r in range(len(thisSortedL)):
        if thisSortedL[i]==this_tl[r][0].user.screen_name:
          reviewMoreFromP(thisSortedL[i], this_tl[r]) # i is index of thisSortedL in sort order, but this_tl is in retrieved order
      continue
    elif reviewPsOpt=='s':
      journal(journal_file,thisSortedL[i],reviewPsOpt)
      storeAction(thisSortedL[i], reviewPsOpt)
      print "skip\n"
      continue
    else: break #nothing left to do but exit
  return

def reviewMoreFromP(this_p, this_tl, debug=False):
  printUserTweets(this_tl)
  validInput = False
  while not validInput:
    actionOpt2=raw_input("(f)ollow, (s)kip: ")
    if actionOpt2 not in {"f","s"}: 
      inputErrorHandler(actionOpt2, "Invalid option!")
    else: validInput = True
    if actionOpt2=="f":
      if debug==True: print "DEBUG: reviewMoreFromP() this_p: ", this_p
      followUser(f_screen_name=this_p) 
      journal(journal_file,this_p,actionOpt2)
      storeAction(this_p, actionOpt2)
  return

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


def printBanner(debug=False):
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

def printUserTweets(p_utl, debug=False):
  if debug==True: print "DEBUG: printUserTweets() len(p_utl):", len(p_utl)
  print "screen_name: {0}".format(p_utl[0].user.screen_name)
  for i in range(len(p_utl)):
    print "Tweet: {0}\tDate: {1}".format(p_utl[i].text,time.strftime('%Y-%m-%d %H:%M', time.strptime(p_utl[i].created_at,'%a %b %d %H:%M:%S +0000 %Y')))
#    ts = time.strftime('%Y-%m-%d %H:%M', time.strptime(tweetL[0].created_at,'%a %b %d %H:%M:%S +0000 %Y'))
    continue

def getUserTweets(g_utl,gUTcount=10): 
  try:
    utl=api.GetUserTimeline(screen_name=g_utl.screen_name,count=gUTcount)
  except:
    traceback.print_exc()
    traceback.print_stack()
    callErrorHandler("Get user timeline failed!")
    return
  return utl

def getUserTweetsFromP(g_screen_name, gUTcount=10):
  try:
    utl=api.GetUserTimeline(screen_name=g_screen_name,count=gUTcount)
  except:
    traceback.print_exc()
    traceback.print_stack()
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

def getListProfileDicts(userList, statusList, pLims, pLists, debug=True):
  thisListProfiles={}
  for i in range(len(userList)):
    if debug==True: print i, "screen_name: ",  userList[i].screen_name
    try:
      thisProfileDict=buildProfileDict(userList[i], statusList[i])
    except:
      if debug==True: print "DEBUG: getListProfileDicts - buildProfileDict failed"
      return thisListProfiles
    thisFriendScore=computeFriendScore(thisProfileDict, pLims, pLists)
    if debug==True: print "DEBUG: getListProfileDicts thisFriendScore: ", thisFriendScore
    thisProfileDict=storeFriendScore(thisProfileDict,thisFriendScore)
    thisListProfiles[userList[i].screen_name]=thisProfileDict
  return thisListProfiles

def inputListSearches(debug=True):
  max_follows=50
  gettingSearches=True
  gettingSearchList=True
  ils_listSearches=[]
  max_follows=raw_input("input max_follows (default=500): ")
  if debug==True: print "DEBUG: inputListSearches() ils_listSearches, max_follows: ", ils_listSearches, max_follows
  while (not max_follows.isdigit()) or max_follows<=0:
    max_follows=raw_input("Invalid entry! max_follows must be a number >0. Input max_follows: ")
  while gettingSearches:  
     gettingConfirm=True
     ils_search=raw_input("input search term, (s)ubmit, (l)ist or e(x)it: ") ### --- or read from a file, list
     if ils_search=="x":
       return "bogus", 0
     elif ils_search=="s":
       print ils_listSearches
       ######### outer while ####################
       while gettingConfirm:
         confirm_list=raw_input("this is the list of searches you have queued, please (c)onfirm or (d)iscard: ")
         if confirm_list=='c':
           return ils_listSearches, max_follows
         elif confirm_list=='d':
           print "discarding list and starting over."
           ils_listSearches=[]
         else:
           inputErrorHandler(confirm_list, "Invalid option!")
         gettingConfirm=False
     elif ils_search=="l":
         ######### inner while ####################
         while gettingSearchList:
            searchList_opts=raw_input("Input name of file to read search terms or (enter) to accept the default (searchlist.txt): ")
            if searchList_opts!="":
                searchList_file=searchList_opts
            else:
                searchList_file="searchlist.txt"
            try:
              searchList_fileH = open(searchList_file, 'r') 
            except:
              traceback.print_exc()
              traceback.print_stack()
              callErrorHandler("Open read of "+searchList_file+" failed.")
              break
            searchList_set=getSets(searchList_fileH)
            ils_listSearches=list(searchList_set)
            print "searchList len: ", len(ils_listSearches)
            gettingSearchList=False
     elif not ils_search=="":
       ils_listSearches.append(ils_search)
     else:
       inputErrorHandler(ils_search, "Invalid option!")
  if debug==True: print "DEBUG: inputListSearches() ils_listSearches, max_follows: ", ils_listSearches, max_follows
  return ils_listSearches, max_follows


def autoAvatar(aa_searchList, aa_max_follows=500, debug=True):
  if aa_searchList=="bogus":
    print "No list. Exiting\n"
    return
  aa_results={}
  m_examined=0
  m_flw=0
  for i in range(len(aa_searchList)):
    if debug==True: print "DEBUG: autoAvatar() aa_searchList[i]: ", aa_searchList[i]
    print "autoAvatar() aa_max_follows, m_flw: ",aa_max_follows, m_flw
    aa_max_id=999999999999999999
    for ii in range(3):
      if m_flw>=aa_max_follows: break
      q_term=aa_searchList[i]
      r=q100(q_term, q_max_id=aa_max_id, q_count=100)
      aa_max_id=getMaxId(r) #get max_id from a list of statuses
      ul=convertSLtoUL(r) #convert status to users
      ul=getULU(ul) #clean: remove dup users
      ul=getFreshUL(ul,touchedSet) #clean: remove already examined users
      m_examined=m_examined+len(ul)
      try: 
        tl=getTL(ul) #get tweets of selected users
      except:
        print "that's a mess..."
        return aa_results
      pLims=getProfileLimitsPoints()
      pLists=getProfileLists()
      listProfs=getListProfileDicts(ul,tl,pLims,pLists)
      if debug==True: print "DEBUG: autoAvatar() type(listProfs)", type(listProfs)
      listUsers=sorted(listProfs, key=lambda x: listProfs[x]['friendScore'], reverse=True)
      if debug==True: print "DEBUG: autoAvatar() listUsers: ", listUsers
      if debug==True: print "DEBUG: autoAvatar() len(listUsers): ", len(listUsers)
      follow_status=True
      follow_fails=0
      for r in range(len(listUsers)):
          if listProfs[listUsers[r]]['friendScore']>0:
            if debug==True: print "DEBUG: autoAvatar() user: ", listUsers[r], " friendScore: ",listProfs[listUsers[r]]['friendScore'] 
            follow_status=followUser(f_screen_name=listUsers[r])
            if follow_status==False:
                follow_fails=follow_fails+1
                if follow_fails > 2:
                    return aa_results
#   store friendProfile in database 
            action_aa='f'
            m_flw=m_flw+1
            if debug==True: print "DEBUG: autoAvatar() aa_max_follows, m_flw: ",aa_max_follows, m_flw
            if m_flw>=aa_max_follows: break
            chillOut()
          else:
            action_aa='s'
          journal(journal_file,listUsers[r],action_aa, search_term=q_term)
          storeAction(listUsers[r], action_aa)
      if debug==True: print "DEBUG: autoAvatar() outside loop - aa_max_follows, m_flw: ",aa_max_follows, m_flw
    if m_flw>=aa_max_follows: break
  if debug==True: print "search list length: ", len(aa_searchList), "\tusers examined: ", m_examined, "\tusers followed: ", m_flw
  return aa_results

def showSearchOptions(show_term, show_lang, show_since, show_until, show_count, max_id, debug=False):
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
## goMain
#
#


def goMain(debug=False):
  printBanner()
  print bcolors.HEADER + "Hi, I'm your auto-avatar, bitxh!\n" + bcolors.ENDC
  print "I will help you engage users on twitter.\n\n \
      I can do these things:\n \
         (g)et a list of tweeters\n \
         (s)ort a list of tweeters\n \
         (f)ollow users\n \
         (u)nfollow friends\n \
         (a)utoAvatar\n \
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
          q_max_id=getMaxId(r) #get max_id from a list of statuses #
          ul=convertSLtoUL(r) #convert status to users
          ul=getULU(ul) #clean: remove dup users #
          ul=getFreshUL(ul,touchedSet) #clean: remove already examined users
#          ul=getRidNullUsers(ul) #clean: protected users and any other miscreants
          tl=getTL(ul) #get tweets of selected users
          pLims=getProfileLimitsPoints() #
          pLists=getProfileLists() #
          listProfs=getListProfileDicts(ul,tl,pLims,pLists)
          if debug==True: print "DEBUG: type(listProfs)", type(listProfs)
          printLUfProf(listProfs)  #report #
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
              inputErrorHandler(optToChange, "Try again!") #
            showSearchOptions(q_term,q_lang,q_since,q_until,q_count,q_max_id) #

    elif thisTodo == "f":
      if ul == []:
        print bcolors.FAIL + "Hey genius! You need to (g)et a list BEFORE you begin to follow!\n" + bcolors.ENDC
      else:
        reviewPsF(listProfs, tl) #
    elif thisTodo == "s":
      if ul == []:
        print bcolors.FAIL + "Hey genius! You need to (g)et a list BEFORE you try to sort!\n" + bcolors.ENDC
      else:
        listProfs=sortPs(listProfs) #returns list, where listProfs is actual a dict #
        if debug==True: print "DEBUG: type(listProfs)", type(listProfs)
        printLUfProf(listProfs)
#        ul=sortPs(ul)
#        printLU(ul)
    elif thisTodo == "q":
      print bcolors.BOLD + bcolors.HEADER + "How's that?\n" + bcolors.ENDC
      exit()
    elif thisTodo == "u":
      reviewFriends(followingUL,followersSet,notFollowingBackSet) #
    elif thisTodo == "a":
      searchList, limit_follows=inputListSearches() #
      my_results=autoAvatar(aa_searchList=searchList,aa_max_follows=int(limit_follows), debug=True) #
    else:
      inputErrorHandler(thisTodo,"Try again!") 
    thisTodo = raw_input("\nMain options: (g)et, (s)ort, (f)ollow, (u)nfollow, (a)utoAvatar or (q)uit: ")

def chillOut():
  rand=randint(0,7)+randint(0,7)
  print "dont choke twitter, wait: ",rand," seconds. time: ",datetime.datetime.now().time()
  time.sleep(rand)

def closeFiles():
  journal_file.close()
  suggest_file.close()
  follow_file.close()

#############################
#
## getReady
#
#
#-----------------------------------------------------------------------
# create twitter API object
#-----------------------------------------------------------------------
config = {}
print "Twitter API object: creating..."
try:
  execfile("config.py", config)
except:
  traceback.print_exc()
  traceback.print_stack()
  callErrorHandler("Read of config.py failed.")
try: 
  api = twitter.Api(consumer_key=config["consumer_key"], 
                  consumer_secret=config["consumer_secret"],
                  access_token_key=config["access_key"],
                  access_token_secret=config["access_secret"])
#                  sleep_on_rate_limit=True)
except: 
  traceback.print_exc()
  traceback.print_stack()
  callErrorHandler("API object creation failed.")
print "Twitter API object: created.\n"
#-----------------------------------------------------------------------
# open data and log files
#-----------------------------------------------------------------------
#def initFiles():
try:
  journal_file = open('aavatar.log', 'a+') 
except:
  traceback.print_exc()
  traceback.print_stack()
  callErrorHandler("Open read of avatar.log failed.")
try:
  suggest_file = open('suggest.dat', 'a+')
except:
  traceback.print_exc()
  traceback.print_stack()
  callErrorHandler("Open read of suggest.dat failed.")
try:
  follow_file = open('follow.dat', 'a+') 
except:
  traceback.print_exc()
  traceback.print_stack()
  callErrorHandler("Open read of follow.dat failed.")
try:
  unfollow_file = open('unfollow.dat', 'a+') 
except:
  traceback.print_exc()
  traceback.print_stack()
  callErrorHandler("Open read of unfollow.dat failed.")
followingUL = {}
#from Files
suggestSet=getSets(suggest_file)
print "suggestSet len: ", len(suggestSet)
followSet=getSets(follow_file)
print "followSet len: ", len(followSet)
unfollowSet=getSets(unfollow_file)
print "unfollowSet len: ", len(unfollowSet)
aaSet=set.union(suggestSet,followSet,unfollowSet)
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
untouchedSet=friendsSet.difference(aaSet)
print "untouchedSet len: ", len(untouchedSet)
    
printTwitLimits()
goMain(debug=True)
closeFiles()
