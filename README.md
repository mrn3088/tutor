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
### Set OPENAI_API_KEY
```bash
echo "OPENAI_API_KEY=YOUR_API_KEY" > .env
```
### Run
```bash
streamlit run app.py
```