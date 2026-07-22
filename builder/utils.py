import os
import sys
from datetime import datetime, timedelta

SERIAL_NUM_LENGTH = 8
SERILA_NUM_RESTRICTED_CHARS = ('O',)

PLATFORM_EXEC_FILE_POSTFIX = ''
if sys.platform.startswith('win'):
	PLATFORM_EXEC_FILE_POSTFIX = '.exe'

SCRIPT_FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FOLDER = os.path.join(SCRIPT_FOLDER, 'environment')


def get_env_path(name):
	"""Get a tool path from the environment/ folder.

	Always looks inside environment/, never searches the system PATH.
	On Windows, appends .exe to the name.
	"""
	candidate = os.path.join(ENV_FOLDER, name + PLATFORM_EXEC_FILE_POSTFIX)
	if not os.path.isfile(candidate):
		raise FileNotFoundError(
			f'Required tool not found in environment/: {name}{PLATFORM_EXEC_FILE_POSTFIX}\n'
			f'Expected at: {candidate}'
		)
	return candidate


def mkdir_recursive(path):
	sub_path = os.path.dirname(path)
	if not os.path.exists(sub_path):
		mkdir_recursive(sub_path)
	if not os.path.exists(path):
		os.mkdir(path)

def getMagicNum(date=None):
	curDate = date if date is not None else datetime.utcnow()
	timestamp = (curDate - datetime(1970, 1, 1)).total_seconds()
	monthSeconds = 60 * 60 * 24 * 30
	magicNum = int((timestamp / monthSeconds) - 0.48)
	return magicNum

def getValidThruDate():
	curDate = datetime.utcnow()
	curMagic = getMagicNum(curDate)
	for i in range(60):
		td = timedelta(days=i)
		testDate = curDate + td
		if getMagicNum(testDate) != curMagic:
			validDate = curDate + timedelta(days=i - 1)
			for i in range(12 * 60 * 60):
				td = timedelta(seconds=i)
				testDate = validDate + td
				if getMagicNum(testDate) != curMagic:
					return validDate + timedelta(seconds=i - 1)

def validateSerial(serialNum):
	if len(serialNum) != SERIAL_NUM_LENGTH:
		return False

	for char in SERILA_NUM_RESTRICTED_CHARS:
		if char in serialNum:
			return False

	return True
