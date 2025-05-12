from viewer_design import ViewerApp
from updater import update

def main():
    app = ViewerApp()
    app.run()

if __name__ == "__main__":
    # Check for updates before starting the app
    update()
    # Start the app
    main()
