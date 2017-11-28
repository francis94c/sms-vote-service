# noinspection PyUnresolvedReferences
import serial
import urllib2
import time
import string

IN_PI = True
try:
    # noinspection PyUnresolvedReferences
    import RPi.GPIO as GPIO  # If running on windows, RPi.GPIO will not exist and will throw an exception
except ImportError:
    print("This service is not running on a Raspberry Pi")
    IN_PI = False

SERVICE = 11  # Service LED Pin.
VOTE = 12  # Voting LED Pin
DELAY = 1  # Communication Delay

if IN_PI:  # Set GPIO Pins appropriately id Running in Raspberry Pi.
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)

if IN_PI:
    API = "http://127.0.0.1/index.php/SMSVoteAPI/"  # CodeIgniter API URL when Running in Raspberry Pi
else:
    API = "http://127.0.0.1/sms-vote-web-app/index.php/SMSVoteAPI/"  # CodeIgniter API URL when Running in Windows.

connected = False
ready = False


def ci_action(function):  # Function that performs codeIgniter API calls via URL.
    return urllib2.urlopen(API + function).read()


ci_action("flagModuleConnection/0")
ci_action("flagModuleReady/0")

usb = serial.Serial("COM39", 115200, timeout=35)

while ready is False:
    time.sleep(DELAY)
    response = usb.readline()
    if "SMS-VOTE:v" in response:
        usb.write(b"OK\r\n")
        connected = True
        ci_action("flagModuleConnection/1")
        print("Module Connected")
        response = ""
    elif "READY" in response:
        print("Module Ready")
        ready = True
        ci_action("flagModuleReady/1")


def query_votes(com_port):
    com_port.write(b"QUERY VOTES\r\n")
    print("Querying Votes")
    try:
        usb_response = com_port.readline()
        if len(usb_response) > 1:
            return True
        return False
    except serial.serialutil.SerialException:
        return False


def get_votes(com_port):
    com_port.write(b"GET VOTES\r\n")
    print("Checking Votes")
    module_response = com_port.readline()
    if "NO VOTES" in module_response:
        return ""
    elif module_response is None:
        return "X"
    else:
        return module_response


def clear_read_smses(com_port):
    com_port.write(b"CLEAR READ SMSES\r\n")
    module_response = com_port.readline()
    if "OK" in module_response:
        return True
    return False


while True:
    if query_votes(usb):
        votes = get_votes(usb)
        if len(votes) > 1:
            votes = votes[:votes.rindex(";")]
            entries = votes.split(";")
            for entry in entries:
                data = entry.split("-")
                codes = data[2].split()
                data[1] = string.replace(data[1], "+234", "0")
                if len(codes[0]) == 4:
                    print("Received Voting Entry")
                    url_string = "vote/" + data[1] + "/" + "/".join(codes)
                    print(ci_action(url_string))
                    print("Voted For " + data[1])
        votes = ""
        clear_read_smses(usb)
