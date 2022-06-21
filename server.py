import os
import sys
from io import StringIO
import time
import threading
import requests
import uuid
import asyncio
from aiohttp import web
import jinja2
import aiohttp_jinja2
import socket
import socketio
import json
from pythonosc import osc_message_builder
from pythonosc import udp_client
from pythonosc.osc_server import AsyncIOOSCUDPServer
from pythonosc.dispatcher import Dispatcher
import matplotlib.pyplot as plt
import librosa
import librosa.display
import wave
from PIL import Image
from pick import pick
import webbrowser
import concurrent.futures

def background(f):
    '''
    a threading decorator
    use @background above the function you want to run in the background
    '''
    def backgrnd_func(*a, **kw):
        threading.Thread(target=f, args=a, kwargs=kw).start()
    return backgrnd_func

# check for names in samples dir
with open('config.json') as config_file:
    config = json.load(config_file)

manifest = {}
profile = {}
loopsToLoad = []
defaultPreset = {}
messages = []

def loadManifest(profileName=None):
    global manifest
    # load the samples manifest
    manifest_path = str(config['samplesDir']) + '/manifest.json'
    with open(manifest_path) as manifest_file:
        manifest = json.load(manifest_file)

def loadDefaultPreset():
    global defaultPreset
    template_path = './templates/presetTemplate.json'
    with open(template_path) as template_file:
        defaultPreset = json.load(template_file)

def saveManifest():
    manifest_path = str(config['samplesDir']) + '/manifest.json'
    with open(manifest_path, 'w') as outfile:
        json.dump(manifest, outfile)

def getAllSamples():
    all_samples = []
    with os.scandir(config['samplesDir']) as entries:
        for entry in entries:
            ext = getExtension(entry.name)
            if ext == 'wav':
                all_samples.append(entry.name)
    return all_samples

def getSampleRecord(sample):
    global manifest
    return manifest['samples'][sample]

def loadPresets(presets,loopID,defaultPre):
    IDs = ['A','B','C','D','E','F','G','H']
    for ID in IDs:
        if ID not in presets:
            presets[ID] = defaultPre
        presets[ID]['loopID'] = loopID
    return presets
 
## sstart socket.io and attach web server
sio = socketio.AsyncServer(async_mode='aiohttp', cors_allowed_origins='*')
SPio = socketio.Client()
app = web.Application()
sio.attach(app)

# osc server connection
sender = udp_client.SimpleUDPClient('127.0.0.1', 4560)

## configure templates
aiohttp_jinja2.setup(app,loader=jinja2.FileSystemLoader('./templates'))

@aiohttp_jinja2.template('index.html')
async def index(request):
    if 'ID' not in profile:
        messages.append('No profile loaded! Please either load a profile or create a new profile.')
    return {
        'myIP': socket.gethostbyname(socket.gethostname()),
        'loops': loopsToLoad,
        'messages': messages
    }

def getExtension(filename):
    parts = filename.split(".")
    return str(parts[-1]).strip().lower()

@aiohttp_jinja2.template('newProfile.html')
async def newProfile(request):
    messages = []
    if 'messages' in profile:
        messages = messages + profile['messages']
    all_samples = getAllSamples()
    return {
        'myIP': socket.gethostbyname(socket.gethostname()),
        'allSamples': all_samples,
        'timestamp': time.time(),
        'messages': messages
    }

@aiohttp_jinja2.template('profiles.html')
async def profiles(request):
    global messages
    profileList = getProfiles()
    all_samples = getAllSamples()
    return {
        'myIP': socket.gethostbyname(socket.gethostname()),
        'profileList': profileList,
        'timestamp': time.time(),
        'messages': messages
    }

@aiohttp_jinja2.template('loop-ctrls.html')
async def getControls(request):
    return {'myIP': socket.gethostbyname(socket.gethostname())}

@aiohttp_jinja2.template('loop-ctrls.html')
async def getLoop(request):
    id = request.match_info.get('id', "Unknkown")
    print(f"ID={id}")
    loop_profile = None
    try:
        loop_profile = profile['loops'][id]
    except KeyError:
        print(f"Loop {id} is not in the loaded profile!")
    defaultPre = defaultPreset
    if 'A' in loop_profile['presets']:
        defaultPre = loop_profile['presets']['A']
    presets = loadPresets(loop_profile['presets'],id,defaultPre)
    sample_record = getSampleRecord(loop_profile['sample'])
    sample_image = sample_record['img_path']
    return {
        'myIP': socket.gethostbyname(socket.gethostname()),
        'sample_image':sample_image,
        'presets': presets
    }

async def loadNextLoop(request):
    global loopsToLoad
    if len(loopsToLoad) > 0:
        loopID = loopsToLoad[-1]
        loopsToLoad = loopsToLoad[:-1]
    url = f"/loop/{loopID}"
    raise web.HTTPFound(url)

@sio.on('message')
async def test_message(sid, message):
    await sio.emit('my response', {'data': message['data']})


@sio.on('my broadcast event', namespace='/test')
async def test_broadcast_message(sid, message):
    print(sid)
    print(message)
    await sio.emit('my response', {'data': message['data']}, namespace='/test')


def save_settings(key,settings):
    with open('all_settings.json') as json_file:
        all_settings = json.load(json_file)
    if key not in all_settings:
        all_settings[key] = settings
    json_string = json.dumps(all_settings)
    with open('all_settings.json', 'w') as outfile:
        json.dump(json_string, outfile)

@sio.on('play')
async def play(sid, message):
    global sidByLoopID
    request = json.loads(message)
    if 'loopID' not in request:
        print("Warning: no loopID key found!")
        return False
    #save_settings(request['loopID'],request)
    print(f"Entering room: {request['loopID']} with sid: {sid}")
    sio.enter_room(sid, request['loopID'])
    msgBase = str(request['loopID']) + "/"
    sample_record = getSampleRecord(profile['loops'][request['loopID']]['sample'])
    full_sample_path = str(config['samplesDir']) + '/' + str(sample_record['wavFile'])
    msgName = str(msgBase) + 'sample'
    sender.send_message(msgName,full_sample_path)
    for k in request:
        if k == 'effects':
            # TBD
            continue
        if k == 'loopID':
            continue
        msgName = str(msgBase) + str(k)
        print(f"Sending {msgName} with value: {request[k]}")
        sender.send_message(msgName,request[k])

def createWavImage(filename):
    global profile, warnings
    parts = filename.split(".")
    fileBase = '.'.join(parts[:-1])
    wavFile = str(config['samplesDir']) + '/' + str(filename)
    img_path = str(config['sampleImagesDir']) + '/' + str(fileBase) + '.png'
    x, sr = librosa.load(wavFile, sr=44100)
    duration = librosa.get_duration(y=x, sr=sr)
    duration = round(duration,2)
    plt.figure(figsize=(14, 5))
    plt.box(False)
    plt.axis('off')
    plt.tick_params(top='off', bottom='off', left='off', right='off', labelleft='off', labelbottom='off')
    try:
        librosa.display.waveshow(x, sr=sr, color='k')
    except ValueError:
        raise Exception(f"Wav file {wavFile} is too large.")
    plt.savefig(img_path)
    img = Image.open(img_path) 
    w, h = img.size
    cropLeft = w*0.16
    cropRight = w - (w*0.135)
    left = cropLeft
    top = 0
    right = cropRight
    bottom = 500
    img_res = img.crop((left, top, right, bottom))
    img_res.save(img_path)
    return wavFile, img_path, duration

def initProfile():
    handle = str(uuid.uuid4())[:8]
    profile_path = './profiles/' + str(handle) + '.json'
    if os.path.isfile(profile_path):
        return initProfile()
    return handle, profile_path

def getSampleLengths(samples):
    sampleLengths = {}
    allLengths = []
    maxLength = 0 
    minLength = 0
    for sample in samples:
        record = getSampleRecord(sample)
        sampleLengths[sample] = record['duration']
        allLengths.append(record['duration'])
    maxLength = sorted(allLengths)[-1]
    minLength = sorted(allLengths)[0]
    return sampleLengths, minLength, maxLength

def createProfile(profile):
    all_samples = getAllSamples()
    handle, profile_path = initProfile()
    profile['ID'] = handle
    # create a sample dictionary
    samplesDict = {}
    # create four loops
    sampleCount = len(profile['samples'])
    sampleLengths, minLength, maxLength = getSampleLengths(profile['samples'])
    # assign counts to samples
    loopCnts = {}
    if sampleCount == 1:
        for sample in profile['samples']:
            loopCnts[sample] = 4
    elif sampleCount == 2:
        for sample in profile['samples']:
            loopCnts[sample] = 2
    elif sampleCount == 3:
        loopCnts[profile['samples'][0]] = 2 
        loopCnts[profile['samples'][1]] = 1 
        loopCnts[profile['samples'][2]] = 1
    elif sampleCount == 4:
        for sample in profile['samples']:
            loopCnts[sample] = 1
    else:
        print(f"ERROR: There should only be 1 to 4 samples.  Found {sampleCount}")
        return False 
    i = 1
    profile['loops'] = {}
    for sample in loopCnts:
        sampleLength = sampleLengths[sample]
        loopCnt = loopCnts[sample]
        samplesDict[sample] = {'loopCount':loopCnt}
        n = 0
        while n < loopCnt:
            loopID = 'l' + str(i)
            a_preset = defaultPreset.copy()
            a_preset['sampleLength'] = sampleLength
            # since the default run is 0.25 of the sample, set the default sleep to 0.25 of sample length
            sl = sampleLength*0.25
            a_preset['sleep'] = [sl,sl,sl,sl,sl,sl,sl,sl]
            profile['loops'][loopID] = {
                            'sample':sample,
                            'presets':{
                                'A': a_preset
                            }
                        }
            i = i + 1
            n = n + 1
    profile['samples'] = samplesDict
    with open(profile_path, 'w') as outfile:
        json.dump(profile, outfile)
    return profile_path

@sio.on('saveProfile')
async def saveProfile(sid, message):
    global profile, messages
    messages = []
    new_profile = json.loads(message)
    profile_samples = []
    if 'samples' in new_profile:
        for filename in new_profile['samples']:
            try:
                wavFile, img_path, duration = createWavImage(filename)
            except Exception as e:
                messages.append(str(e))
                continue
            # save new sample to manifest
            manifest['samples'][filename] = {'wavFile': filename,'img_path':img_path,'duration':duration}
            saveManifest()
            profile_samples.append(filename)
    profile['samples'] = profile_samples
    profile_keys = ['name']
    for k in profile_keys:
        profile[k] = new_profile[k]
    if len(messages) > 0:
        profile['messages'] = messages
    else:
        profilePath = createProfile(profile)
        msg = f"Created profile {profile['name']} at {profilePath}"
        profile['messages'] = [msg]

@sio.on('loadProfile')
async def loadProfileHandler(sid, message):
    global messages
    print(f"message: {message}")
    messages = []
    profileID = json.loads(message)
    loadProfile(profileID)
    messages.append(f"Loaded profile {profileID}")


@sio.on('*')
def catch_all(event, data):
    print(f"event: {event} data: {data}")

@sio.on('leave', namespace='/test')
async def leave(sid, message):
    sio.leave_room(sid, message['room'], namespace='/test')
    await sio.emit('my response', {'data': 'Left room: ' + message['room']},
                   room=sid, namespace='/test')


@sio.on('close room', namespace='/test')
async def close(sid, message):
    await sio.emit('my response',
                   {'data': 'Room ' + message['room'] + ' is closing.'},
                   room=message['room'], namespace='/test')
    await sio.close_room(message['room'], namespace='/test')


@sio.on('my room event', namespace='/test')
async def send_room_message(sid, message):
    await sio.emit('my response', {'data': message['data']},
                   room=message['room'], namespace='/test')


@sio.on('disconnect request', namespace='/test')
async def disconnect_request(sid):
    await sio.disconnect(sid, namespace='/test')


@sio.on('connect', namespace='/test')
async def test_connect(sid, environ):
    await sio.emit('my response', {'data': 'Connected', 'count': 0}, room=sid,
                   namespace='/test')

@sio.on('disconnect', namespace='/test')
def test_disconnect(sid):
    print('Client disconnected')

def checkClassyServer():
    try:
        url = "http://localhost:8080"
        r = requests.get(url)
    except:
        return False
    if 'ClassyIndex' in r.text:
        return True 

@background
def startBrowser():
    serverStatus = False 
    while not serverStatus:
        time.sleep(2)
        print("Waiting on server to start ...")
        serverStatus = checkClassyServer()
    if serverStatus:
        messages = []
        print("Server has started!")
    webbrowser.open("http://localhost:8080/profiles")

def getProfiles():
    profiles = []
    with os.scandir('./profiles/') as entries:
        for entry in entries:
            ext = getExtension(entry.name)
            if ext == 'json':
                profile_path = './profiles/' + str(entry.name)
                with open(profile_path) as profile_file:
                    a_profile = json.load(profile_file)
                    # add sample names to a description
                    sampleNames = '; '.join(list(a_profile['samples'].keys()))
                    optionDesc = str(a_profile['name']) + ": samples include " + str(sampleNames)
                    a_profile['optionDesc'] = optionDesc
                    profiles.append(a_profile)
    return profiles

def loadProfile(profileName='ADMIN'):
    global profile, loopsToLoad
    if profileName == 'ADMIN':
        profile = {}
        return True 
    profile_path = './profiles/' + str(profileName)
    # check for .json
    if '.json' not in profile_path:
        profile_path = str(profile_path) + '.json'
    with open(profile_path) as profile_file:
        profile = json.load(profile_file)
    loopsToLoad = []
    loopsToLoad = list(profile['loops'].keys())
    print(loopsToLoad)
    return True 

def startServer():
    # give sonic Pi time to register a couple of heartbeats
    time.sleep(2)
    SonicPiStatus = checkSonicPi()
    if SonicPiStatus:
        startBrowser()
        loadManifest()
        loadDefaultPreset()
        web.run_app(app)
    else:
        print("Sonic Pi is not running!  Please start Sonic Pi with the collaborative_loop_controller.rb program.")

# Sonic Pi Listener
lastSPheartbeat = 0

async def getSP(request):
    #get loop ID
    loopID = None
    try:
        loopID = f"l{request.rel_url.query['loop']}"
    except KeyError:
        return web.Response(status=204)
    if not loopID:
        return web.Response(status=204)
    #print(f"query params: {request.rel_url.query}")
    data = {
        'loop': loopID,
        'start': request.rel_url.query['start'],
        'rate': request.rel_url.query['rate'],
        'finish': request.rel_url.query['finish'],
        'amp': request.rel_url.query['amp']
    }
    #print(f"In getSP, room={loopID}")
    await sio.emit('fromSonicPi', {'data': data},room=loopID)
    return web.Response(status=200)

def getPlayParams(address: str, *args: list) -> None:
    #print(args)
    params = {
        'loop': args[0],
        'start': args[1],
        'rate': args[2],
        'finish': args[3],
        'amp': args[4]
    }
    try:
        r = requests.get('http://127.0.0.1:8080/getSP', params=params)
    except requests.exceptions.ConnectionError as e:
        print(f"Connect Error:{e}")
        return None

def getHeartBeat(*args):
    global lastSPheartbeat
    lastSPheartbeat = time.time()

def checkSonicPi():
    global lastSPheartbeat
    nowTS = time.time()
    if lastSPheartbeat == 0:
        return False 
    if (nowTS - lastSPheartbeat) > 10:
        return False 
    return True


OSCip = "127.0.0.1"
OSCport = 12000

dispatcher = Dispatcher()
dispatcher.map("/sonicpi/im_here", getHeartBeat)
dispatcher.map("/sonicpi/playing", getPlayParams)
server = AsyncIOOSCUDPServer((OSCip, OSCport), dispatcher, asyncio.get_event_loop())


async def OSCloop():
    i = 0
    while True:
        await asyncio.sleep(1)
        i = i + 1

async def initSonicPi():
    print("Starting Sonic Pi listener.")
    server = AsyncIOOSCUDPServer((OSCip, OSCport), dispatcher, asyncio.get_event_loop())
    transport, protocol = await server.create_serve_endpoint()  # Create datagram endpoint and start serving
    await OSCloop()  # Enter main loop of program
    transport.close()  # Clean up serve endpoint

def startSonicPiListener():
    asyncio.run(initSonicPi())
    print("Waiting for Sonic Pi hearbeat.")
    time.sleep(5)
    if SPheartbeats > 0:
        print("Sonic Pi has started.")
    else:
        print("Sonic Pi has not started.")


app.router.add_static('/static', 'static')
app.router.add_get('/', index)
app.router.add_get('/controls', getControls)
app.router.add_get('/profiles', profiles)
app.router.add_get('/newProfile', newProfile)
app.router.add_get('/loadNextLoop', loadNextLoop)
app.router.add_get('/loop/{id}',getLoop)
app.router.add_get('/getSP',getSP)

if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        futures.append(executor.submit(startSonicPiListener))
        futures.append(executor.submit(startServer))
    for future in concurrent.futures.as_completed(futures):
        print(future.result())
    