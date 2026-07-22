#!/usr/bin/env python3
"""Verify all environment/ paths resolve correctly."""
import os, sys
sys.argv = ['build_installer.py', 'TESTTEST']

from builder.utils import validateSerial, mkdir_recursive, PLATFORM_EXEC_FILE_POSTFIX, get_env_path
from builder.packer import BUILD_FOLDER_FMT

SCRIPT_FOLDER = os.path.dirname(os.path.abspath('build_installer.py'))
ENV_FOLDER = os.path.join(SCRIPT_FOLDER, 'environment')

XML_BACKUP_PATH = os.path.join(ENV_FOLDER, 'Installer.xml.bak')
CONFIG_BACKUP_PATH = os.path.join(ENV_FOLDER, 'SecureSWF.ssp4.bak')
SECURE_SWF_JAR_PATH = os.path.join(ENV_FOLDER, 'secureSWF.jar')

if PLATFORM_EXEC_FILE_POSTFIX:
    JAVA_PATH = os.path.join(ENV_FOLDER, 'jre-windows', 'bin', 'java.exe')
else:
    JAVA_PATH = os.path.join(ENV_FOLDER, 'java')

swfmillPath = get_env_path('swfmill')

from builder.packer import CRYPTO_PACK_PATH

paths = {
    'XML_BACKUP': XML_BACKUP_PATH,
    'CONFIG_BACKUP': CONFIG_BACKUP_PATH,
    'SECURE_SWF_JAR': SECURE_SWF_JAR_PATH,
    'JAVA': JAVA_PATH,
    'SWFMILL': swfmillPath,
    'CRYPTO_PACK': CRYPTO_PACK_PATH,
    'INSTALLER_DLL': os.path.join(SCRIPT_FOLDER, 'FullPack', 'UpdateInstaller.dll'),
}

print('=== Path verification ===')
all_ok = True
for name, path in paths.items():
    exists = os.path.exists(path)
    if not exists:
        all_ok = False
    print(f'  {name:20s} exists={exists}  {path}')

print()
print('ALL OK' if all_ok else 'SOME FILES MISSING')
