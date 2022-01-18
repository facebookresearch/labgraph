/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew tap facebook/fb
brew update && brew upgrade
brew install watchman ant buck
mv /usr/local/Cellar/buck/2021.01.12.01_1/ /usr/local/Cellar/buck/2021.01.12.01
brew link buck

