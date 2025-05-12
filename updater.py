import os
import shutil
import zipfile
import requests
from pathlib import Path

########################### CHANGE ME ##############################
ROOT_DIR = Path(__file__).absolute().parent

# add root to system path and get version from root __init__
os.sys.path.append(ROOT_DIR.parent.as_posix())
from version import __version__

VERSION_URL = 'https://raw.githubusercontent.com/3D-Printing-for-Microfluidics/3d_slice_viewer/main/version.py'
ZIP_URL = 'https://api.github.com/repos/3D-Printing-for-Microfluidics/3d_slice_viewer/zipball'
####################################################################

def update():
    print("Updating...")

    # get github auth token from remote server
    try:
        with requests.get(SERVER_URL) as f:
            token = str(f.text).strip()
    except:
        print("\tFailed to connect to auth server.")
        return

    # check the latest version number
    currentVersion = __version__
    with requests.get(VERSION_URL) as f:
        _code = f.text
        exec(_code, globals())
        latestVersion = __version__

    if currentVersion == latestVersion:
        print("\tThis is the latest version.")
        return

    # clean root directory
    for f in ROOT_DIR.glob('*'):
        if f.name != "env" and f.name != ".git":
            if f.is_dir():
                shutil.rmtree(f)
            else:
                os.remove(f)

    # download the new version of code
    filename = ROOT_DIR / Path('update.zip')
    with requests.get(ZIP_URL) as f:
        open(filename, 'wb').write(f.content)

    # unzip downloaded file and extract them to root directory
    with zipfile.ZipFile(filename, 'r') as zf:
        folder = zf.namelist()[0]
        zf.extractall(path=ROOT_DIR)
        for f in (ROOT_DIR / folder).glob('*'):
            if f.is_dir():
                shutil.copytree(f, (ROOT_DIR / f.name))
            else:
                shutil.copy(f, ROOT_DIR)
        # remove downloaded files
        shutil.rmtree(ROOT_DIR / folder)
    if filename.exists():
        os.remove(filename)

    print(f"\tProgram updated to {latestVersion}. Restart to finish update.")
