## Install
### Clone the project
```bash
git clone https://github.com/mrn3088/tutor.git
```
### Create virtual environment
```bash
python3 -m venv venv
source venv/bin/activate # on linux/macos
venv\Scripts\activate # on windows
```
### Install requirements
```bash
mkdir db
mkdir document
pip install -r requirements.txt
```
### Install and start mongodb
#### MacOS
```bash
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community
```
#### Linux
```bash
sudo apt-get install -y mongodb-org
sudo systemctl start mongod
```
#### Windows
Please follow the instructions [here](https://docs.mongodb.com/manual/tutorial/install-mongodb-on-windows/).
### Set OPENAI_API_KEY
```bash
echo "OPENAI_API_KEY=YOUR_API_KEY" > .env
```
### Run
```bash
streamlit run app.py
```