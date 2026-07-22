import os
import sys
import time
import shutil
import logging

APP_LIST_PATH = 'APP_LIST.txt'
RESULT_FOLDER_NAME = 'SyncExtPack'
NAME_FORMAT = 'SyncExtPack_%s'

def cleanupResult(resultDir):
	shutil.rmtree(resultDir)

def getPackageName(apimSerial, resultDir):
	result = NAME_FORMAT % apimSerial
	appListPath = os.path.join(resultDir, str(apimSerial), APP_LIST_PATH)
	if os.path.exists(appListPath):
		with open(appListPath, 'r') as f:
			appsList = [app.strip() for app in f.readlines()]
			result += '_' + '_'.join(appsList)
	return result

def genArchive(apimSerial, work_dir='.'):
	baseDir = os.path.join(work_dir, 'SyncExtPack')
	arcName = getPackageName(apimSerial, baseDir)
	arcBasePath = os.path.join(work_dir, arcName)
	logging.info('Result file name: %s' % arcName)
	resultDir = os.path.join(baseDir, str(apimSerial))
	archiveName = shutil.make_archive(arcBasePath, 'zip', resultDir, RESULT_FOLDER_NAME)
	return resultDir, archiveName

def main():
	logging.basicConfig(filename='builder.log', level=logging.INFO, format='%(asctime)s: %(levelname)s: %(message)s')
	logging.info('Generating result archive...')

	apimSerial = sys.argv[1].upper()
	resultDir, _ = genArchive(apimSerial)
	time.sleep(0.1)
	cleanupResult(resultDir)
	logging.info('Generating result archive done!')

if __name__ == '__main__':
	main()