import logging
import logging.handlers
import json
import os
import sys
import re
import datetime
import time
from twilio.rest import Client as SMSClient
import requests
import copy

CurrentDir = os.getcwd()

#The only thing not configurable
LOG_CONFIG_FILE = CurrentDir + '\\log.conf'

#Logging configuration variables
LOG_FILE = CurrentDir + '\\EXGymTracker.log'
LOG_FILE_COUNT = 20
LOG_FORMAT = '%(asctime)s %(name)s %(levelname)-8s line %(lineno)d %(message)s'
LOG_FILE_SIZE = 1048576
LOG_LEVEL = logging.INFO

#Config values
CACHE_FILE = CurrentDir + '\\EXGymTracker.json'
EGG_BODY = 'GYM RAID ALERT {name} {startTime}-{endTime} Tier {tier} google.com/maps/search/?api=1&query={lat},{long}'
HATCH_BODY = 'GYM RAID ALERT {name} {startTime}-{endTime} {pokemon} google.com/maps/search/?api=1&query={lat},{long}'
NIGHT_TIME_END = 5
NIGHT_TIME_START = 21
POKEDEX_FILE = CurrentDir + '\\Pokedex.json'
RAID_URL = ''
RAID_URL_REFERER = ''
SCAN_INTERVAL = 60 #seconds
SMS_FROM_NUMBER = 0
TESTING_MODE = True
TWILIO_SID = ''
TWILIO_AUTH_TOKEN = ''
USER_FILE = CurrentDir + '\\Users.json'

#Global variables filled and used later
GYMS = []
POKEDEX = []
SMS_CLIENT = None
USERS = []

#TODO Use Lat/Long or gym id to track GYMS.


#Config File Support
def checkForConfigs():
    logger = logging.getLogger()
    configFiles = [f for f in os.listdir(CurrentDir) if os.path.isfile(f) and re.match('.+\.conf', f)]

    bIsGoodConfig = False
    config = None
    if len(configFiles) > 0:
        for i in configFiles:
            logger.info('Checking %s config file', i)
            bIsGoodConfig, config = isGoodConfig(i)
            if bIsGoodConfig:
                break
    else:
        logger.info('No config files found')
    return bIsGoodConfig, config

def isGoodConfig(configFileDir):
    logger = logging.getLogger()
    bIsGoodConfig = False
    config = None

    with open(configFileDir, "r") as f:
        try:
            config = json.load(f)
            if (config['CACHE_FILE'] is not None and
                    config['EGG_BODY'] is not None and
                    config['HATCH_BODY'] is not None and
                    config['NIGHT_TIME_END'] is not None and
                    config['NIGHT_TIME_START'] is not None and 
                    config['POKEDEX_FILE'] is not None and
                    config['RAID_URL'] is not None and 
                    config['RAID_URL_REFERER'] is not None and
                    config['SCAN_INTERVAL'] is not None and
                    config['SMS_FROM_NUMBER'] is not None and
                    config['TESTING_MODE'] is not None and
                    config['TWILIO_SID'] is not None and
                    config['TWILIO_AUTH_TOKEN'] is not None and
                    config['USER_FILE'] is not None):
                bIsGoodConfig = True
            else:
                config = None
        except Exception as ex:
            logger.exception(ex)
            
    return bIsGoodConfig, config

def importConfigSettings(logResults):
    global CACHE_FILE
    global EGG_BODY
    global HATCH_BODY
    global NIGHT_TIME_END
    global NIGHT_TIME_START
    global POKEDEX_FILE
    global RAID_URL
    global RAID_URL_REFERER
    global SCAN_INTERVAL
    global SMS_FROM_NUMBER
    global TESTING_MODE
    global TWILIO_SID
    global TWILIO_AUTH_TOKEN
    global USER_FILE
    
    logger = logging.getLogger()
    bSuccess, config = checkForConfigs()
    
    if bSuccess: #success
        logger.info('read in a config file...')
        CACHE_FILE = CurrentDir + config['CACHE_FILE']
        EGG_BODY = config['EGG_BODY']
        HATCH_BODY = config['HATCH_BODY']
        NIGHT_TIME_END = int(config['NIGHT_TIME_END'])
        NIGHT_TIME_START = int(config['NIGHT_TIME_START'])
        POKEDEX_FILE = CurrentDir + config['POKEDEX_FILE']
        RAID_URL = config['RAID_URL']
        RAID_URL_REFERER = config['RAID_URL_REFERER']
        SCAN_INTERVAL = int(config['SCAN_INTERVAL'])
        SMS_FROM_NUMBER = int(config['SMS_FROM_NUMBER'])
        TESTING_MODE = config['TESTING_MODE']
        TWILIO_SID = config['TWILIO_SID']
        TWILIO_AUTH_TOKEN = config['TWILIO_AUTH_TOKEN']
        USER_FILE = CurrentDir + config['USER_FILE']
        
        if logResults:
            logger.info('CACHE_FILE: %s', CACHE_FILE)
            logger.info('EGG_BODY: %s', EGG_BODY)
            logger.info('HATCH_BODY: %s', HATCH_BODY)
            logger.info('NIGHT_TIME_END: %d o\'clock', NIGHT_TIME_END)
            logger.info('NIGHT_TIME_START: %d o\'clock', NIGHT_TIME_START)
            logger.info('POKEDEX_FILE: %s', POKEDEX_FILE)
            logger.info('RAID_URL: %s', RAID_URL)
            logger.info('RAID_URL_REFERER: %s', RAID_URL_REFERER)
            logger.info('SCAN_INTERVAL: %d sec', SCAN_INTERVAL)
            logger.info('SMS_FROM_NUMBER: %d', SMS_FROM_NUMBER)
            logger.info('TESTING_MODE: %s', TESTING_MODE)
            logger.info('TWILIO_SID: %s', TWILIO_SID)
            logger.info('TWILIO_AUTH_TOKEN: %s', TWILIO_AUTH_TOKEN)
            logger.info('USER_FILE: %s', USER_FILE)

def importPokedex():
    global POKEDEX
    global POKEDEX_FILE
    
    POKEDEX = []
    
    logger = logging.getLogger()
    with open(POKEDEX_FILE, "r") as f:
        try:
            POKEDEX = json.load(f)
        except Exception as ex:
            logger.exception(ex)

def importUsers():
    global USERS
    global USER_FILE
    global GYMS
    
    USERS = []
    GYMS = []
    
    logger = logging.getLogger()
    with open(USER_FILE, "r") as f:
        try:
            #Load the users file
            USERS = json.load(f)
            #Fill the gyms array
            for user in USERS:
                if user['Gyms']:
                    if user['Active Perks']:
                        for userGym in user['Gyms']:
                            foundGym = False
                            for gym in GYMS:
                                if gym['Name'] == userGym['Name']:  #TODO Match on Gym id
                                    foundGym = True
                                    if userGym['EggNotification']:
                                        gym['Egg Numbers'].append(user['Phone Number'])
                                    if userGym['HatchNotification']:
                                        gym['Hatch Numbers'].append(user['Phone Number'])
                                #TODO if we match gym id or lat long we will need to include those here instead.
                            if not foundGym:
                                newGym = {
                                    'Egg Numbers': [],
                                    'Hatch Numbers': [],
                                    'Latitude': userGym['Latitude'],
                                    'Longitude': userGym['Longitude'],
                                    'Name': userGym['Name']
                                }
                                if userGym['EggNotification']:
                                    newGym['Egg Numbers'].append(user['Phone Number'])
                                if userGym['HatchNotification']:
                                    newGym['Hatch Numbers'].append(user['Phone Number'])
                                GYMS.append(newGym)
        except Exception as ex:
            logger.exception(ex)

def getLogConfig():
    global LOG_FILE
    global LOG_FILE_COUNT
    global LOG_FILE_SIZE
    global LOG_FORMAT
    global LOG_LEVEL
    global LOG_CONFIG_FILE
    
    config = None

    with open(LOG_CONFIG_FILE, "r") as f:
        try:
            config = json.load(f)
            if config is not None:
                LOG_FILE = (CurrentDir + config['LOG_FILE']) if config['LOG_FILE'] is not None else LOG_FILE
                LOG_FILE_COUNT = int(config['LOG_FILE_COUNT']) if config['LOG_FILE_COUNT'] is not None else LOG_FILE_COUNT
                LOG_FILE_SIZE = int(config['LOG_FILE_SIZE']) if config['LOG_FILE_SIZE'] is not None else LOG_FILE_SIZE
                LOG_FORMAT = config['LOG_FORMAT'] if config['LOG_FORMAT'] is not None else LOG_FORMAT
                if config['LOG_LEVEL']:
                    if config['LOG_LEVEL'] == 'CRITICAL':
                        LOG_LEVEL = logging.CRITICAL
                    elif config['LOG_LEVEL'] == 'ERROR':
                        LOG_LEVEL = logging.ERROR
                    elif config['LOG_LEVEL'] == 'WARNING':
                        LOG_LEVEL = logging.WARNING
                    elif config['LOG_LEVEL'] == 'INFO':
                        LOG_LEVEL = logging.INFO
                    elif config['LOG_LEVEL'] == 'DEBUG':
                        LOG_LEVEL = logging.DEBUG
                    elif config['LOG_LEVEL'] == 'NOTSET':
                        LOG_LEVEL = logging.NOTSET
        except Exception as ex:
            logger.exception(ex)

def prepLogger():
    global LOG_FILE_SIZE
    global LOG_FILE_COUNT
    global LOG_LEVEL
    global LOG_FORMAT
    
    getLogConfig()
    
    logger = logging.getLogger()
    f = logging.Formatter(LOG_FORMAT)
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(f)
    logger.addHandler(h)
    
    h2 = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes=LOG_FILE_SIZE, backupCount=LOG_FILE_COUNT)
    h2.setFormatter(f)
    logger.addHandler(h2)
    
    logger.setLevel(LOG_LEVEL)

def prepSMS():
    global SMS_CLIENT
    global TWILIO_AUTH_TOKEN
    global TWILIO_SID
    global TESTING_MODE
    
    logger = logging.getLogger()
    if not TESTING_MODE:
        SMS_CLIENT = SMSClient(TWILIO_SID, TWILIO_AUTH_TOKEN)

def getEXGymData():
    global GYMS
    
    logger = logging.getLogger()
    gyms = [gym for gym in getAllGyms() if gym['gymname'].strip() in [masterGym['Name'] for masterGym in GYMS]] #TODO Filter BY LAT/LONG
    return gyms

def getAllGyms():
    global RAID_URL
    global RAID_URL_REFERER
    global POKEDEX
    
    logger = logging.getLogger()
    gyms = []
    response = {'raids':[0,1,2,3,4,5,6,7,8,9]}
    i = 0
    while response is not None and response['raids'] is not None and len(response['raids']) >= 10:
        url = RAID_URL % i
        response = json.loads(requests.get(url, headers={'Referer': RAID_URL_REFERER}).text)
        if len(response['raids']) > 0:
            for id, raid in response['raids'].items():
                gyms.append({
                    'gymname': raid['name'],
                    'id': raid['gym_id'],
                    'spawnTime': datetime.datetime.strptime(raid['spawn'], '%Y-%m-%d %H:%M:%S'),
                    'startTime': datetime.datetime.strptime(raid['start'], '%Y-%m-%d %H:%M:%S'),
                    'endTime': datetime.datetime.strptime(raid['end'], '%Y-%m-%d %H:%M:%S'),
                    'tier': int(raid['level']),
                    'pokemon': POKEDEX[int(raid['pokemon_id'])-1] if raid['pokemon_id'] else None,
                    'lat': raid['latitude'],
                    'long': raid['longitude'],
                    'type': 'Egg' if raid['pokemon_id'] is None else 'Pokemon'
                })
        i += 1
    return gyms

def saveCache(Hatches, Eggs):
    global CACHE_FILE
    
    logger = logging.getLogger()
    
    with open(CACHE_FILE, 'w') as file:
        try:
            allData = copy.deepcopy(Hatches) + copy.deepcopy(Eggs)
            logger.debug('%d raids saved to cache', len(allData))
            for gym in allData:
                gym['spawnTime'] = gym['spawnTime'].strftime('%Y-%m-%d %H:%M:%S')
                gym['startTime'] = gym['startTime'].strftime('%Y-%m-%d %H:%M:%S')
                gym['endTime'] = gym['endTime'].strftime('%Y-%m-%d %H:%M:%S')
            json.dump(allData, file)
        except Exception as ex:
            logger.exception(ex)

def loadCache():
    global CACHE_FILE
    
    logger = logging.getLogger()
        
    Hatches = []
    Eggs = []
    
    try:
        with open(CACHE_FILE, "r") as file:
            allData = json.load(file)
            logger.debug('%d raids loaded from cache', len(allData))
            for gym in allData:
                gym['spawnTime'] = datetime.datetime.strptime(gym['spawnTime'], '%Y-%m-%d %H:%M:%S')
                gym['startTime'] = datetime.datetime.strptime(gym['startTime'], '%Y-%m-%d %H:%M:%S')
                gym['endTime'] = datetime.datetime.strptime(gym['endTime'], '%Y-%m-%d %H:%M:%S')
            Hatches = [gym for gym in allData if gym['type'] != 'Egg']
            Eggs = [gym for gym in allData if gym['type'] == 'Egg']
    except Exception as ex:
        logger.exception(ex)\
    
    
    return Hatches, Eggs

def main():
    global SMS_CLIENT
    global USERS
    
    global EGG_BODY
    global HATCH_BODY
    global NIGHT_TIME_END
    global NIGHT_TIME_START
    global SCAN_INTERVAL
    global SMS_FROM_NUMBER
    global TESTING_MODE
    
    prepLogger()
    logger = logging.getLogger()
    logger.info('Loading Config Values...')
    importConfigSettings(True)
    logger.info('Loading Pokedex...')
    importPokedex()
    logger.info('Loading Users...')
    importUsers()
    prepSMS()
    
    fromNumber = '+1' + str(SMS_FROM_NUMBER)
    
    Hatches = []
    Eggs = []
    
    logger.info('Loading Cache...')
    Hatches, Eggs = loadCache()
    
    while True:
        #Get current time
        now = datetime.datetime.now()
        try:
            
            #Clean up hatches
            removedData = False
            logger.info('Cleaning up Eggs and Hatches...')
            for Hatch in Hatches:
                if now > Hatch['endTime']:
                    Hatches.remove(Hatch)
                    removedData = True
            #Clean up eggs
            for Egg in Eggs:
                if now > Egg['startTime']:
                    Eggs.remove(Egg)
                    removedData = True
            newHatches = []
            newEggs = []
            #Get gym data
            logger.info('Getting gym data...')
            gymData = getEXGymData()
            
            logger.debug('Hatches:%s', Hatches)
            logger.debug('Eggs:%s', Eggs)
            #Determine if we have a new raid at a EX raid gym
            #Have we seen it before (key off of hatch time, long, lat)
            newHatches = [gym for gym in gymData if gym['type'] != 'Egg' and gym not in Hatches]
            newEggs = [gym for gym in gymData if gym['type'] == 'Egg' and gym not in Eggs]
            logger.debug('New Hatches:%s', newHatches)
            logger.debug('New Eggs:%s', newEggs)
            for newEgg in newEggs:
                if now < newEgg['startTime']:
                    body= EGG_BODY.format(
                        name=newEgg['gymname'],
                        startTime=newEgg['startTime'].strftime('%H:%M'),
                        endTime=newEgg['endTime'].strftime('%H:%M'),
                        tier=newEgg['tier'],
                        lat=newEgg['lat'],
                        long=newEgg['long'])
                    
                    for gym in GYMS:
                        if gym['Name'] == newEgg['gymname']:
                            for number in gym['Egg Numbers']:
                                toNumber = '+1' + str(number)
                                if not TESTING_MODE:
                                    SMS_CLIENT.messages.create(
                                        to=toNumber,
                                        from_=fromNumber,
                                        body=body)
                                else:
                                    logger.info('from:%s, to: %s, body:%s', fromNumber, toNumber, body)
                            logger.info('from:%s, body:%s', fromNumber, body)
                    #Add newEgg to Eggs
                    Eggs.append(newEgg)
                        
            for newHatch in newHatches:
                if now < newHatch['endTime']:
                    body= HATCH_BODY.format(
                        name=newHatch['gymname'],
                        startTime=newHatch['startTime'].strftime('%H:%M'),
                        endTime=newHatch['endTime'].strftime('%H:%M'),
                        pokemon=newHatch['pokemon'],
                        lat=newHatch['lat'],
                        long=newHatch['long'])
                    
                    for gym in GYMS:
                        if gym['Name'] == newHatch['gymname']:
                            for number in gym['Hatch Numbers']:
                                toNumber = '+1' + str(number)
                                if not TESTING_MODE:
                                    SMS_CLIENT.messages.create(
                                        to=toNumber,
                                        from_=fromNumber,
                                        body=body)
                                else:
                                    logger.info('from:%s, to: %s, body:%s', fromNumber, toNumber, body)
                            logger.info('from:%s, body:%s', fromNumber, body)
                    #add newHatch to Hatches
                    Hatches.append(newHatch)
            
            newData = False
            if len(newHatches) == 0 and len(newEggs) == 0:
                logger.info('No new Ex Raid Gym Eggs/Hatches')
            else:
                newData = True
                
            updatedData = newData or removedData
            if updatedData:
                #updated Hatches/Eggs->write data to cache
                logger.info('Saving to cache...')
                saveCache(Hatches, Eggs)
        
        except (KeyboardInterrupt, SystemExit) as ex:
            logger.exception(ex)
            break
        except Exception as ex:
            logger.exception(ex)
        if now.time() >= datetime.time(NIGHT_TIME_START, 0) or now.time() < datetime.time(NIGHT_TIME_END,0):
            nightly_timer = (datetime.timedelta(hours=24) - (now - now.replace(hour=NIGHT_TIME_END, minute=0, second=0, microsecond=0))).total_seconds() % (86400)
            logger.info("Sleeping %d secs until %d AM", nightly_timer, NIGHT_TIME_END)
            time.sleep(nightly_timer)
        time.sleep(SCAN_INTERVAL)
        #Reload config settings but no need to reprep Twilio client or reload the cache.
        logger.info('Reloading Config Values...')
        importConfigSettings(False)
        logger.info('Reloading Pokedex...')
        importPokedex()
        logger.info('Reloading Users...')
        importUsers()
    
    sys.exit(0)

if __name__ == '__main__':
    main()