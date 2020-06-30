# profileDict:
# user object: empirical, 7 items: list[tweets, followers, friends, account_create_datetime, pic, bio, verified]
# status object: last_status_datetime, offset_status_datetime, retweets]
#
# calculated 1st order, pratio(followers/friends), sratio(tweets/followers), daysOld(now-account create),
# calculated 2nd order, freqRatio(tweets/daysOld),   daysLast(now-last status),timeFnumTweets(now-offset_status_datetime)  volumeRatio(numTweets/timeFnumTweets), retweetRatio(retweets/numTweets)
# calculted 3rd order, friendsScore(baysean),

import datetime, re

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
    if re.match('^RT', statusObject[i].text):
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


def getProfileLists():
  thisProfileLists = {
      'screen_namesNot': ['tmj', 'job', 'anon', 'bot', 'career', 'MAGA' ],
      'locationIn': ['Cambridge', 'Massachusetts', 'San Francisco', 'California', 'Providence', 'SF', 'RI', 'CA', 'MA']
      }
  return thisProfileLists


def getProfileLimitsPoints():
  thisLimitsPointsList = {
      #black marks
      'screen_nameBool': ("Boolean",-109),
      'friendMin': (20,-99),
      'followersMin': (20,-99),
      'pratioMax': (15,-99), #pop-ratio
      'sratioMax': (15,-99), #chorus-ratio
      'activeMax': (30,-99),
      'retweetRatioMax': (0.9,-99), #retweetScale
      #blue marks
      'tweetsMax': (200000,-80), #200,000,
      'volumeRatioMax': (9,-75),
      'timeFnumTweetsMax': (15,-70), #days
      'picBool': ("Boolean",-50),
      'timeFnumTweetsMin': (1,-50), #days
      'bioBool': ("Boolean",-40),
      #yellow marks
      'volumeRatioMin': (0,-15), #tweets/day
      'freqRatioMax': (10,-20), #tweets/day
      'accountAgeMin': (90,-10),
      'tweetsMin': (100,-10),
      'activeMin': (2,-10),
      #gree marks
      'verified': ("Boolean",10),
      'locationBool': ("Boolean",20),
      'accountAgeMax': (1825,30) #5 years in days
      }
  return thisLimitsPointsList

def printShowWork(limitName, thisLims,  runFriendScore):
  print "item:", limitName, "\tLimit:", thisLims[limitName][0], "\tPoints:", thisLims[limitName][1], "\tScore:", runFriendScore
  return

def computeFriendScore(profileDict, pLims, pLists, showWork=True):
  thisFriendScore=100
  if showWork: print "Friend score init:", thisFriendScore
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
