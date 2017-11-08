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

LOG_FILE = CurrentDir + '\\EXGymTracker.log'
CACHE_FILE = CurrentDir + '\\EXGymTracker.json'
LOG_LEVEL = logging.INFO

SCAN_INTERVAL = 60 #seconds
EX_RAID_GYMS = ['Memorial Student Center', 'FREE TEAM PHONE SKIN', 'War for Texas Independence']
URLS_TO_SCAN = ['https://pokemasterbcs.com/core/process/aru.php?type=raids&page=%d']
EMAILS = []
TEXT_NUMBERS = []
TWILIO_SID = ''
TWILIO_AUTH_TOKEN = ''
SMS_CLIENT = None
SMS_FROM_NUMBER = 0
TESTING_MODE = True

POKEDEX = [
'Bulbasaur',
'Ivysaur',
'Venusaur',
'Charmander',
'Charmeleon',
'Charizard',
'Squirtle',
'Wartortle',
'Blastoise',
'Caterpie',
'Metapod',
'Butterfree',
'Weedle',
'Kakuna',
'Beedrill',
'Pidgey',
'Pidgeotto',
'Pidgeot',
'Rattata',
'Raticate',
'Spearow',
'Fearow',
'Ekans',
'Arbok',
'Pikachu',
'Raichu',
'Sandshrew',
'Sandslash',
'Nidoran♀',
'Nidorina',
'Nidoqueen',
'Nidoran♂',
'Nidorino',
'Nidoking',
'Clefairy',
'Clefable',
'Vulpix',
'Ninetales',
'Jigglypuff',
'Wigglytuff',
'Zubat',
'Golbat',
'Oddish',
'Gloom',
'Vileplume',
'Paras',
'Parasect',
'Venonat',
'Venomoth',
'Diglett',
'Dugtrio',
'Meowth',
'Persian',
'Psyduck',
'Golduck',
'Mankey',
'Primeape',
'Growlithe',
'Arcanine',
'Poliwag',
'Poliwhirl',
'Poliwrath',
'Abra',
'Kadabra',
'Alakazam',
'Machop',
'Machoke',
'Machamp',
'Bellsprout',
'Weepinbell',
'Victreebel',
'Tentacool',
'Tentacruel',
'Geodude',
'Graveler',
'Golem',
'Ponyta',
'Rapidash',
'Slowpoke',
'Slowbro',
'Magnemite',
'Magneton',
'Farfetch’d',
'Doduo',
'Dodrio',
'Seel',
'Dewgong',
'Grimer',
'Muk',
'Shellder',
'Cloyster',
'Gastly',
'Haunter',
'Gengar',
'Onix',
'Drowzee',
'Hypno',
'Krabby',
'Kingler',
'Voltorb',
'Electrode',
'Exeggcute',
'Exeggutor',
'Cubone',
'Marowak',
'Hitmonlee',
'Hitmonchan',
'Lickitung',
'Koffing',
'Weezing',
'Rhyhorn',
'Rhydon',
'Chansey',
'Tangela',
'Kangaskhan',
'Horsea',
'Seadra',
'Goldeen',
'Seaking',
'Staryu',
'Starmie',
'Mr. Mime',
'Scyther',
'Jynx',
'Electabuzz',
'Magmar',
'Pinsir',
'Tauros',
'Magikarp',
'Gyarados',
'Lapras',
'Ditto',
'Eevee',
'Vaporeon',
'Jolteon',
'Flareon',
'Porygon',
'Omanyte',
'Omastar',
'Kabuto',
'Kabutops',
'Aerodactyl',
'Snorlax',
'Articuno',
'Zapdos',
'Moltres',
'Dratini',
'Dragonair',
'Dragonite',
'Mewtwo',
'Mew',
'Chikorita',
'Bayleef',
'Meganium',
'Cyndaquil',
'Quilava',
'Typhlosion',
'Totodile',
'Croconaw',
'Feraligatr',
'Sentret',
'Furret',
'Hoothoot',
'Noctowl',
'Ledyba',
'Ledian',
'Spinarak',
'Ariados',
'Crobat',
'Chinchou',
'Lanturn',
'Pichu',
'Cleffa',
'Igglybuff',
'Togepi',
'Togetic',
'Natu',
'Xatu',
'Mareep',
'Flaaffy',
'Ampharos',
'Bellossom',
'Marill',
'Azumarill',
'Sudowoodo',
'Politoed',
'Hoppip',
'Skiploom',
'Jumpluff',
'Aipom',
'Sunkern',
'Sunflora',
'Yanma',
'Wooper',
'Quagsire',
'Espeon',
'Umbreon',
'Murkrow',
'Slowking',
'Misdreavus',
'Unown',
'Wobbuffet',
'Girafarig',
'Pineco',
'Forretress',
'Dunsparce',
'Gligar',
'Steelix',
'Snubbull',
'Granbull',
'Qwilfish',
'Scizor',
'Shuckle',
'Heracross',
'Sneasel',
'Teddiursa',
'Ursaring',
'Slugma',
'Magcargo',
'Swinub',
'Piloswine',
'Corsola',
'Remoraid',
'Octillery',
'Delibird',
'Mantine',
'Skarmory',
'Houndour',
'Houndoom',
'Kingdra',
'Phanpy',
'Donphan',
'Porygon2',
'Stantler',
'Smeargle',
'Tyrogue',
'Hitmontop',
'Smoochum',
'Elekid',
'Magby',
'Miltank',
'Blissey',
'Raikou',
'Entei',
'Suicune',
'Larvitar',
'Pupitar',
'Tyranitar',
'Lugia',
'Ho-Oh',
'Celebi',
'Treecko',
'Grovyle',
'Sceptile',
'Torchic',
'Combusken',
'Blaziken',
'Mudkip',
'Marshtomp',
'Swampert',
'Poochyena',
'Mightyena',
'Zigzagoon',
'Linoone',
'Wurmple',
'Silcoon',
'Beautifly',
'Cascoon',
'Dustox',
'Lotad',
'Lombre',
'Ludicolo',
'Seedot',
'Nuzleaf',
'Shiftry',
'Taillow',
'Swellow',
'Wingull',
'Pelipper',
'Ralts',
'Kirlia',
'Gardevoir',
'Surskit',
'Masquerain',
'Shroomish',
'Breloom',
'Slakoth',
'Vigoroth',
'Slaking',
'Nincada',
'Ninjask',
'Shedinja',
'Whismur',
'Loudred',
'Exploud',
'Makuhita',
'Hariyama',
'Azurill',
'Nosepass',
'Skitty',
'Delcatty',
'Sableye',
'Mawile',
'Aron',
'Lairon',
'Aggron',
'Meditite',
'Medicham',
'Electrike',
'Manectric',
'Plusle',
'Minun',
'Volbeat',
'Illumise',
'Roselia',
'Gulpin',
'Swalot',
'Carvanha',
'Sharpedo',
'Wailmer',
'Wailord',
'Numel',
'Camerupt',
'Torkoal',
'Spoink',
'Grumpig',
'Spinda',
'Trapinch',
'Vibrava',
'Flygon',
'Cacnea',
'Cacturne',
'Swablu',
'Altaria',
'Zangoose',
'Seviper',
'Lunatone',
'Solrock',
'Barboach',
'Whiscash',
'Corphish',
'Crawdaunt',
'Baltoy',
'Claydol',
'Lileep',
'Cradily',
'Anorith',
'Armaldo',
'Feebas',
'Milotic',
'Castform',
'Kecleon',
'Shuppet',
'Banette',
'Duskull',
'Dusclops',
'Tropius',
'Chimecho',
'Absol',
'Wynaut',
'Snorunt',
'Glalie',
'Spheal',
'Sealeo',
'Walrein',
'Clamperl',
'Huntail',
'Gorebyss',
'Relicanth',
'Luvdisc',
'Bagon',
'Shelgon',
'Salamence',
'Beldum',
'Metang',
'Metagross',
'Regirock',
'Regice',
'Registeel',
'Latias',
'Latios',
'Kyogre',
'Groudon',
'Rayquaza',
'Jirachi',
'Deoxys'
]

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

    matchesCount = 0
    with open(configFileDir, "r") as f:
        try:
            config = json.load(f)
            if (config['SCAN_INTERVAL'] is not None and 
                    config['EX_RAID_GYMS'] is not None and 
                    config['URLS_TO_SCAN'] is not None and 
                    config['EMAILS'] is not None and 
                    config['TEXT_NUMBERS'] is not None and
                    config['TWILIO_SID'] is not None and
                    config['TWILIO_AUTH_TOKEN'] is not None and
                    config['SMS_FROM_NUMBER'] is not None and
                    config['TESTING_MODE'] is not None):
                bIsGoodConfig = True
            else:
                config = None
        except Exception as ex:
            logger.exception(ex)
            
    return bIsGoodConfig, config

def importConfigSettings(logResults):
    global SCAN_INTERVAL
    global EX_RAID_GYMS
    global URLS_TO_SCAN
    global EMAILS
    global TEXT_NUMBERS
    global TWILIO_SID
    global TWILIO_AUTH_TOKEN
    global SMS_FROM_NUMBER
    global TESTING_MODE
    
    logger = logging.getLogger()
    bSuccess, config = checkForConfigs()

    if bSuccess: #success
        logger.info('read in a config file...')
        SCAN_INTERVAL = int(config['SCAN_INTERVAL'])
        EX_RAID_GYMS = config['EX_RAID_GYMS']
        URLS_TO_SCAN = config['URLS_TO_SCAN']
        EMAILS = config['EMAILS']
        TEXT_NUMBERS = config['TEXT_NUMBERS']
        TWILIO_SID = config['TWILIO_SID']
        TWILIO_AUTH_TOKEN = config['TWILIO_AUTH_TOKEN']
        SMS_FROM_NUMBER = config['SMS_FROM_NUMBER']
        TESTING_MODE = config['TESTING_MODE']
        
        if logResults:
            logger.info('SCAN_INTERVAL: %d sec', SCAN_INTERVAL)
            logger.info('EX_RAID_GYMS: %s', EX_RAID_GYMS)
            logger.info('URLS_TO_SCAN: %s', URLS_TO_SCAN)
            logger.info('EMAILS: %s', EMAILS)
            logger.info('TEXT_NUMBERS: %s', TEXT_NUMBERS)
            logger.info('TWILIO_SID: %s', TWILIO_SID)
            logger.info('TWILIO_AUTH_TOKEN: %s', TWILIO_AUTH_TOKEN)
            logger.info('SMS_FROM_NUMBER: %d', SMS_FROM_NUMBER)
            logger.info('TESTING_MODE:%s', TESTING_MODE)

def prepLogger():
    logger = logging.getLogger()
    f = logging.Formatter('%(asctime)s %(name)s %(levelname)-8s line %(lineno)d %(message)s')
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(f)
    logger.addHandler(h)
    
    h2 = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes=1048576, backupCount=20)
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
    global EX_RAID_GYMS
    
    logger = logging.getLogger()
    gyms = [gym for gym in getAllGyms() if gym['gymname'].strip() in EX_RAID_GYMS] #TODO Filter BY LAT/LONG
    return gyms

def getAllGyms():
    global URLS_TO_SCAN
    global POKEDEX
    
    logger = logging.getLogger()
    gyms = []
    response = {'raids':[True]}
    i = 0
    while response is not None and response['raids'] is not None and len(response['raids']) > 0:
        url = URLS_TO_SCAN[0] % i
        response = json.loads(requests.get(url, headers={'Referer':'http://pokemasterbcs.com/'}).text)
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
        logger.exception(ex)
    #Read from file
    #Separate into Hatches vs Eggs
    
    
    return Hatches, Eggs

def main():
    global SMS_CLIENT
    global TEXT_NUMBERS
    global EX_RAID_GYMS
    global SCAN_INTERVAL
    global SMS_FROM_NUMBER
    global TESTING_MODE
    
    prepLogger()
    logger = logging.getLogger()
    importConfigSettings(True)
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
                    body='EX RAID GYM ALERT {name} {startTime}-{endTime} Tier {tier} google.com/maps/search/?api=1&query={lat},{long}'.format(
                        name=newEgg['gymname'],
                        startTime=newEgg['startTime'].strftime('%H:%M'),
                        endTime=newEgg['endTime'].strftime('%H:%M'),
                        tier=newEgg['tier'],
                        lat=newEgg['lat'],
                        long=newEgg['long'])
                    if not TESTING_MODE:
                        for number in TEXT_NUMBERS:
                            toNumber = '+1' + str(number)
                            SMS_CLIENT.messages.create(
                                to=toNumber,
                                from_=fromNumber,
                                body=body)
                        logger.info('from:%s, body:%s', fromNumber, body)
                    else:
                        logger.info('Outgoing body:%s', body)
                    #Add newEgg to Eggs
                    Eggs.append(newEgg)
                        
            for newHatch in newHatches:
                if now < newHatch['endTime']:
                    body='EX RAID GYM ALERT {name} {startTime}-{endTime} {pokemon} google.com/maps/search/?api=1&query={lat},{long}'.format(
                        name=newHatch['gymname'],
                        startTime=newHatch['startTime'].strftime('%H:%M'),
                        endTime=newHatch['endTime'].strftime('%H:%M'),
                        pokemon=newHatch['pokemon'],
                        lat=newHatch['lat'],
                        long=newHatch['long'])
                    
                    if not TESTING_MODE:
                        for number in TEXT_NUMBERS:
                            toNumber = '+1' + str(number)
                            SMS_CLIENT.messages.create(
                                to=toNumber,
                                from_=fromNumber,
                                body=body)
                        logger.info('from:%s, body:%s', fromNumber, body)
                    else:
                        logger.info('Outgoing body:%s', body)
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
        if now.time() >= datetime.time(21, 0) or now.time() < datetime.time(6,0):
            nightly_timer = (datetime.timedelta(hours=24) - (now - now.replace(hour=6, minute=0, second=0, microsecond=0))).total_seconds() % (86400)
            logger.info("Sleeping %d secs until 6 AM", nightly_timer)
            time.sleep(nightly_timer)
        time.sleep(SCAN_INTERVAL)
        #Reload config settings but no need to reprep Twilio client or reload the cache.
        importConfigSettings(False)
    
    sys.exit(0)

if __name__ == '__main__':
    main()