import os
import sys
import subprocess
import time
import shutil
import logging

from builder.utils import validateSerial, mkdir_recursive, PLATFORM_EXEC_FILE_POSTFIX, get_env_path

SCRIPT_FOLDER = os.path.dirname(__file__)

RESULT_FOLDER = 'SyncExtPack/'
INSTALLER_DLL_PATH = os.path.join(SCRIPT_FOLDER, './FullPack/UpdateInstaller.dll')

# All tools are in the environment/ folder — no system PATH search
ENV_FOLDER = os.path.join(SCRIPT_FOLDER, 'environment')
XML_BACKUP_PATH = os.path.join(ENV_FOLDER, 'Installer.xml.bak')
CONFIG_BACKUP_PATH = os.path.join(ENV_FOLDER, 'SecureSWF.ssp4.bak')
SECURE_SWF_JAR_PATH = os.path.join(ENV_FOLDER, 'secureSWF.jar')

# Java: on Linux use wrapper script, on Windows use JRE's java.exe directly
if PLATFORM_EXEC_FILE_POSTFIX:
	JAVA_PATH = os.path.join(ENV_FOLDER, 'jre-windows', 'bin', 'java.exe')
else:
	JAVA_PATH = os.path.join(ENV_FOLDER, 'java')

XML_FILENAME = 'Installer.xml'
CONFIG_FILENAME = 'SecureSWF.ssp4'
NORMAL_SWF_FILENAME = 'Installer.swf'
SECURED_SWF_FILENAME = 'secure_Installer.swf'
BUILD_RESULT_FILENAME = 'Installer.jpg'

XML_APIM_FORMAT = 	'<PushData>\n                <items>\n\
                  <StackInteger value="%s"/>\n\
                  <StackInteger value="%s"/>\n\
                  <StackInteger value="%s"/>\n\
                  <StackInteger value="%s"/>\n\
                  <StackInteger value="%s"/>\n\
                  <StackInteger value="%s"/>\n\
                  <StackInteger value="%s"/>\n\
                  <StackInteger value="%s"/>\n\
                  <StackInteger value="8"/>\n\
                </items>\n              </PushData>'

class PackCompiler(object):

	def __init__(self):
		self.__serial = None
		self.__garbage = []

	def start(self, serial, work_dir='.'):
		self.__serial = serial
		self.__buildFolder = os.path.join(work_dir, 'SyncExtPack', serial, '')
		self.__resultFolder = os.path.join(self.__buildFolder, RESULT_FOLDER)
		mkdir_recursive(self.__resultFolder)
		self.__buildInstaller()

	def cleanup(self):
		for filePath in self.__garbage:
			os.remove(filePath)

	def __getEncryptedSerial(self):
		res = []
		i = 0
		for ch in self.__serial:
			factor = 2 if i % 2 == 0 else 3
			res.append(ord(ch) * factor)
			i = i + 1
		return tuple(res[::-1])

	def __prepareInstallerSrc(self):
		with open(XML_BACKUP_PATH, 'r') as f:
			srcFile = f.read()
		encrSerial = XML_APIM_FORMAT % self.__getEncryptedSerial()
		srcFile = srcFile.replace('<<APIM>>', encrSerial)
		resultPath = os.path.join(self.__buildFolder, XML_FILENAME)
		with open(resultPath, 'w') as f:
			f.write(srcFile)
		return resultPath

	def __prepareSecureConfig(self, swfPath):
		with open(CONFIG_BACKUP_PATH, 'r') as f:
			srcFile = f.read()
		swfPath = os.path.abspath(swfPath).replace('\\', '/')
		srcFile = srcFile.replace(NORMAL_SWF_FILENAME, swfPath)
		resultPath = os.path.join(self.__buildFolder, CONFIG_FILENAME)
		with open(resultPath, 'w') as f:
			f.write(srcFile)
		return resultPath

	def __buildInstaller(self):
		xmlPath = self.__prepareInstallerSrc()
		resultPath = os.path.join(self.__buildFolder, NORMAL_SWF_FILENAME)

		swfmillPath = get_env_path('swfmill')
		subprocess.call([swfmillPath, 'xml2swf', xmlPath, resultPath])

		configPath = self.__prepareSecureConfig(resultPath)
		subprocess.call([JAVA_PATH, '-Xmx1024m', '-jar', SECURE_SWF_JAR_PATH, 'run', 'secureSWF4', configPath])

		securedPath = os.path.join(self.__buildFolder, SECURED_SWF_FILENAME)
		buildResultPath = os.path.join(self.__resultFolder, BUILD_RESULT_FILENAME)
		shutil.move(securedPath, buildResultPath)
		shutil.copy(INSTALLER_DLL_PATH, self.__resultFolder)
		self.__garbage.extend([resultPath, configPath, xmlPath])

def main():
	logging.basicConfig(filename='builder.log', level=logging.INFO, format='%(asctime)s: %(levelname)s: %(message)s')
	logging.info('Building installer...')

	apimSerial = sys.argv[1].upper()
	if validateSerial(apimSerial):
		packCompiler = PackCompiler()
		packCompiler.start(apimSerial)
		packCompiler.cleanup()
	else:
		logging.error('Installer build failed. APIM serial number is invalid!')

	logging.info('Building installer done!')

if __name__ == '__main__':
	main()
