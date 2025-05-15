from viewer_design import ViewerApp
from updater import update
import os

def main():
    app = ViewerApp()
    app.run()

if __name__ == "__main__":
    # Check for updates before starting the app
    status = update()
    if status == 1:
        print("Starting the app...")
        main()
    elif status == 0:
        os.system('pause')
        exit(0)