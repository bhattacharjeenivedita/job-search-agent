# 🤖 Job Search Agent

A Python-based automation agent that searches multiple job portals every morning and compiles a personalised list of matching job listings — built from scratch as a hands-on learning project.

---

## 💡 Why I Built This

As a data & analytics professional actively looking for new opportunities, I found myself spending too much time manually checking multiple job portals every day. So I built a tool to do it for me.

This project is also my first step into Python development and GitHub — built entirely from scratch.

---

## ✨ Features

- 🔍 **Multi-portal search** — searches StepStone, with LinkedIn and Xing coming soon
- ⚙️ **Fully configurable** — set your own keywords, locations, and languages in one file
- 📬 **Daily email digest** — automatically sends a curated list of jobs every morning *(coming soon)*
- 💾 **Saves results** — exports all found jobs to a dated JSON file for tracking
- 🔒 **Secure by design** — sensitive credentials stored in `.env`, never exposed on GitHub

---

## 🗂️ Project Structure

```
job-search-agent/
│
├── config/
│   └── settings.py        # Your job search criteria (keywords, locations, portals)
│
├── src/
│   └── job_agent.py       # Main agent script
│
├── output/                # Daily results saved here (local only, not on GitHub)
├── .env                   # Private credentials (local only, not on GitHub)
├── .gitignore             # Keeps secrets and clutter off GitHub
└── README.md              # You are here!
```

---

## 🚀 Getting Started

Follow these steps to run the agent on your own machine.

### 1. Clone the repository

```bash
git clone https://github.com/bhattacharjeenivedita/job-search-agent.git
cd job-search-agent
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac / Linux
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up your private credentials

Create a `.env` file in the root folder:

```
YOUR_EMAIL=your.email@gmail.com
EMAIL_PASSWORD=your_app_password_here
YOUR_NAME=Your Name
```

> ⚠️ Never share this file or commit it to GitHub.

### 5. Configure your search criteria

Edit `config/settings.py` to set your own keywords, locations, and portals:

```python
KEYWORDS = ["Data Analyst", "Business Intelligence", "Python Developer"]
LOCATIONS = ["Stuttgart", "Berlin", "Remote"]
LANGUAGES = ["English", "German"]
```

### 6. Run the agent

```bash
python src/job_agent.py
```

Results will be printed in the terminal and saved to the `output/` folder.

---

## 🛣️ Roadmap

This project is actively being developed. Planned features:

- [ ] Add LinkedIn job search
- [ ] Add Xing job search
- [ ] Daily email digest with formatted HTML email
- [ ] Deduplication — avoid seeing the same job twice
- [ ] Scoring system — rank jobs by how well they match your profile
- [ ] Web dashboard to view and manage results
- [ ] Deploy online so others can use it too

---

## 🛠️ Built With

- [Python 3.13](https://www.python.org/)
- [Requests](https://docs.python-requests.org/) — fetching web pages
- [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) — parsing HTML
- [python-dotenv](https://pypi.org/project/python-dotenv/) — secure credential management
- [Schedule](https://schedule.readthedocs.io/) — task scheduling

---

## 👤 About Me

I'm a data & analytics professional currently open to new opportunities in Germany. This project reflects my approach to problem-solving — when I face a challenge, I build a solution.

Feel free to connect with me on [LinkedIn](https://www.linkedin.com/in/niveditabjee11/) or reach out via GitHub!

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).