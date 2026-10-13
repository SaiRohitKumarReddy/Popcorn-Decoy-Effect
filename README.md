# Movie Snack Choice: The Popcorn Decoy Effect

**An interactive behavioral-economics classroom experiment built with Streamlit and Google Sheets.**

Students make two hypothetical popcorn-purchasing decisions: first from a two-size menu, then from a three-size menu. The instructor can examine whether introducing a closely priced **Medium** option changes the share of students who choose **Large**.

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B?logo=streamlit&logoColor=white)
![Google Sheets](https://img.shields.io/badge/Storage-Google%20Sheets-34A853?logo=googlesheets&logoColor=white)
![Version](https://img.shields.io/badge/App%20version-3.3.0-243B5A)

> **Current implementation (v3.3.0):** Every student completes **both** scenarios in sequence. Responses are stored in **Google Sheets**. This replaces an older prototype README that described randomized Group A/B assignment, name-based duplicate blocking, and local CSV storage; those are **not** features of the supplied version.

### Contents

- [Overview](#overview)
- [The experiment](#the-experiment)
- [Features](#features)
- [Technology stack](#technology-stack)
- [Repository structure](#repository-structure)
- [Installation and local setup](#installation-and-local-setup)
- [Data schema](#data-schema)
- [Deploying to Streamlit Community Cloud](#deploying-to-streamlit-community-cloud)
- [Recommended classroom workflow](#recommended-classroom-workflow)
- [Privacy and security](#privacy-and-security)
- [Current limitations and design considerations](#current-limitations-and-design-considerations)
- [Troubleshooting](#troubleshooting)
- [Possible extensions](#possible-extensions)

## Overview

In standard economic models, a consumer's choice between two options should be evaluated using their attributes and preferences. Behavioral economics also studies **context effects**: how the presentation of an additional alternative can influence perceived value.

This application explores the *decoy effect* through a movie-theatre popcorn menu. Every student completes both scenarios in a fixed order; the professor can then compare responses using a dashboard. The project is intended for interactive teaching and exploratory demonstrations, **not** for establishing a causal effect or conducting a randomized controlled trial.

### Learning objectives

After completing the exercise, students should be able to:

1. Explain how **reference alternatives and price framing** may affect perceived value.
2. Distinguish a descriptive shift in choice shares from evidence of **causation**.
3. Calculate a **paired-sample choice share** and its change in **percentage points**.
4. Discuss limitations from a fixed scenario order, self-selection, and hypothetical purchases.

## The experiment

| Popcorn option | Scenario 1 | Scenario 2 | Displayed size |
| --- | ---: | ---: | --- |
| Small | ₹150 | ₹150 | 6-11 cups |
| Medium | Not offered | **₹290** | 12-15 cups |
| Large | ₹300 | ₹300 | 16-20+ cups |
| Don't Know | Available | Available | - |

- **Scenario 1 - Baseline:** students choose among Small, Large, or Don't Know.
- **Scenario 2 - Medium introduced:** students see the same choices plus Medium, priced just ₹10 below Large.
- **Teaching question:** does the appearance of Medium change the rate at which students select Large?

**Important economic nuance:** Medium is an *intended* decoy in this demonstration. It is **not strictly dominated** by Large on both price and quantity, because Medium is ₹10 cheaper. Consequently, the exercise demonstrates a possible **choice-context or price-framing effect**, rather than a textbook proof of asymmetric dominance.

### Measuring the result

The dashboard uses only students who **completed both scenarios** to calculate the paired Large-choice rates:

$$
\text{Large choice rate in Scenario 1} = \frac{\text{Completed students choosing Large in Scenario 1}}{\text{Students completing both scenarios}} \times 100
$$

$$
\text{Large choice rate in Scenario 2} = \frac{\text{Completed students choosing Large in Scenario 2}}{\text{Students completing both scenarios}} \times 100
$$

$$
\Delta = \text{Scenario 2 rate} - \text{Scenario 1 rate}
$$

The dashboard displays **\(\Delta\) in percentage points**, not as a relative percentage increase.

For example, if 8 of 20 completed students choose Large in Scenario 1 and 13 choose Large in Scenario 2, the rates are 40% and 65%, respectively, giving a **+25 percentage-point** difference. This is an illustrative example, not an observed result from the application.

Because every participant sees Scenario 1 before Scenario 2, differences may also reflect order, learning, demand, or other response effects. No random assignment, inferential hypothesis test, or adjustment for these effects is implemented.

## Features

### Student mode

- Clean, responsive movie-snack interface with self-contained SVG popcorn illustrations.
- Name-entry screen and personalized on-screen greeting.
- Two sequential choice scenarios with an explicit transition between them.
- Selectable options, visible selection state, and an explicit **Submit Response** action.
- A **Don't Know** option in both scenarios.
- Session-state handling that keeps navigation and option selection fast without reading Google Sheets on each interaction.
- Saves Scenario 1 when submitted, then updates the same Google Sheet row after Scenario 2.
- Completion screen once both answers have been submitted.

### Professor mode

- Password-protected access using Streamlit secrets.
- Totals for recorded participants, Scenario 1 submissions, Scenario 2 submissions, and incomplete responses.
- Per-scenario response counts, percentages, and horizontal comparison bars.
- Paired Large-choice comparison and the percentage-point difference.
- **Refresh Results** to load updated Google Sheets data on demand.
- **Download CSV** to export the current response records.
- **Reveal Experiment** to display the design and rationale.
- **Reset Experiment**, with a confirmation step, to clear submitted records while retaining the column headers.

> The dashboard uses **manual refresh**, not automatic polling. The student experience and the dashboard share a Google Sheet, but results update when the professor refreshes or opens the dashboard.

### What the instructor dashboard reports

| Measure | Source / interpretation |
| --- | --- |
| Total Students | Number of nonempty response records in the worksheet; not necessarily unique people |
| Scenario 1 Submitted | Records with a first-scenario answer |
| Scenario 2 Submitted | Records with a second-scenario answer |
| In Progress | Records that do not yet have answers to both scenarios |
| Scenario response distributions | Counts and percentages using the total submitted for that scenario |
| Decoy Effect Result | Change in **Large** choice share across the **same completed set** of participants |

The scenario distribution cards and the paired result can have different denominators: the former include all submitted answers, while the latter restricts the comparison to complete pairs. **Don't Know** is included in each denominator as a valid response choice.

## Technology stack

| Component | Technology | Purpose |
| --- | --- | --- |
| User interface | Streamlit | Student and professor modes |
| Charts and visuals | HTML, CSS, inline SVG | Styled selection cards and dashboard bars |
| Storage | Google Sheets | Persist submitted responses |
| Sheets integration | `gspread` | Read, append, and update worksheet rows |
| Authentication to Google | `google-auth` | Service-account credentials |
| Concurrency handling | Python `threading.RLock` | Serialize worksheet operations in one app process |
| Transient-error handling | Retry with backoff | Retry certain API and network failures |

The dependency file also lists `pandas` and `portalocker`; neither is imported by the current `Popcorn_Decoy.py` entry point.

## Repository structure

```text
Popcorn-Decoy-Effect-main/
|-- Popcorn_Decoy.py       # Streamlit application (student + professor)
|-- requirements.txt       # Python dependencies
|-- .gitignore             # Excludes local secrets and generated files
`-- README.md              # Project documentation
```

The `.streamlit/secrets.toml` file described below is **local configuration** and should not be committed.

## Requirements

- **Python 3.10 or newer**, with `pip`.
- A Google Cloud project and a Google service account.
- An editable Google Sheets spreadsheet with a response worksheet.
- Google Sheets API access (the app also requests a Google Drive OAuth scope).
- Access to create Streamlit secrets locally or in your deployment environment.

## Installation and local setup

### 1. Get the project

Clone your own GitHub repository or download and extract its ZIP, then navigate into the project directory.

```bash
git clone https://github.com/YOUR_USERNAME/Popcorn-Decoy-Effect.git
cd Popcorn-Decoy-Effect
```

Replace `YOUR_USERNAME` and the repository name if your GitHub URL differs.

### 2. Create an environment and install the dependencies

**Windows (PowerShell):**

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### 3. Configure Google Sheets

1. In [Google Cloud Console](https://console.cloud.google.com/), create or select a project.
2. Enable the **Google Sheets API** and **Google Drive API** for the project.
3. Create a service account and generate a JSON key for it. Keep that key private.
4. Create a Google spreadsheet and add a worksheet, for example `Responses`.
5. **Share the spreadsheet with the service account's `client_email` as an Editor.**
6. Copy the spreadsheet ID from the URL: `https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit`.

**Initialize the worksheet before collecting student answers.** The expected first row is the eight headers shown in [Data schema](#data-schema), in exactly that order. You can fill them manually, or open the professor dashboard once while the worksheet is completely empty so the app initializes them. If students submit to an empty sheet before the header exists, the first response may occupy row 1 and subsequent dashboard reads will reject the header.

### 4. Add Streamlit secrets

Create `.streamlit/secrets.toml` in the project directory. Use the values from your own Google service-account JSON and spreadsheet; all entries below are **placeholders**.

```toml
[professor]
password = "REPLACE_WITH_A_STRONG_PROFESSOR_PASSWORD"

[google_sheet]
spreadsheet_id = "YOUR_SPREADSHEET_ID"
worksheet_name = "Responses"

[gcp_service_account]
type = "service_account"
project_id = "YOUR_GOOGLE_CLOUD_PROJECT_ID"
private_key_id = "YOUR_PRIVATE_KEY_ID"
private_key = "-----BEGIN PRIVATE KEY-----\nYOUR_PRIVATE_KEY\n-----END PRIVATE KEY-----\n"
client_email = "YOUR_SERVICE_ACCOUNT@YOUR_PROJECT.iam.gserviceaccount.com"
client_id = "YOUR_CLIENT_ID"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/YOUR_SERVICE_ACCOUNT"
```

Keep the key's actual `private_key` value intact; either escaped `\n` sequences or real newlines are handled by the application. Copy any other values from the original service-account JSON instead of inventing them.

**Never commit `.streamlit/secrets.toml` or the service-account JSON file to GitHub.** `.streamlit/secrets.toml` is already in the project's `.gitignore`; the `.gitignore` only excludes JSON files matching a particular filename pattern, so verify that any credentials file you create is also excluded before committing.

### 5. Run the app

```bash
streamlit run Popcorn_Decoy.py
```

Open the local address displayed by Streamlit (usually [http://localhost:8501](http://localhost:8501)). Choose **Student Mode** to complete the experiment or **Professor Mode** to log in with the password configured in secrets.

## Data schema

The Google worksheet has eight columns. The professor's CSV export uses the same format.

| Column | Field | Description |
| --- | --- | --- |
| A | `name_key` | Reserved; **blank for new records** |
| B | `name` | Reserved; **blank for new records** |
| C | `scenario_1_choice` | `Small`, `Large`, or `Don't Know` |
| D | `scenario_2_choice` | `Small`, `Medium`, `Large`, or `Don't Know` |
| E | `status` | `scenario_1_submitted` or `completed` |
| F | `created_at` | Timestamp created in app session |
| G | `scenario_1_submitted_at` | Time Scenario 1 was submitted |
| H | `scenario_2_submitted_at` | Time Scenario 2 was submitted |

Timestamps are generated using **Asia/Kolkata (IST)** and stored as ISO-style strings.

### How a response is stored

```text
Student enters name  --> kept in Streamlit session only
           |
           v
Select Scenario 1 --> Submit --> append one Google Sheets row
           |
           v
Select Scenario 2 --> Submit --> update that same row
           |
           v
Professor dashboard --> read records --> aggregate and export
```

New response rows are **anonymous in Google Sheets**: the application deliberately leaves `name_key` and `name` empty even though students type a name to receive a personalized greeting. The saved row number is remembered in the current Streamlit session so the second answer can update the correct row. The student path normally performs two writes and no full-sheet reads for a completed experiment.

### Schema initialization: do this before inviting students

This step is important because the student flow is optimized for write-only submissions: **it does not validate or initialize headers** when recording Scenario 1. Start with a completely empty worksheet and open the professor dashboard once, or add the exact eight headers manually before the first student submission.

If the header is missing and a response has already occupied the first row, **do not overwrite the row without preserving the student's data**. Export or back up the spreadsheet first, then repair the row layout and headers.

## Deploying to Streamlit Community Cloud

1. Push the project source, `requirements.txt`, `.gitignore`, and this README to GitHub **without any secrets**.
2. In [Streamlit Community Cloud](https://share.streamlit.io/), create an app from your GitHub repository.
3. Set the application entry point to **`Popcorn_Decoy.py`**.
4. Add your valid TOML configuration from `.streamlit/secrets.toml` in the app's **Secrets** settings.
5. Confirm the service account has Editor access to the configured Google Sheet.
6. Deploy, open Professor Mode to verify connectivity and initialize headers if required, and test one complete student flow.

Streamlit Community Cloud settings and availability can change; follow the current deployment prompts.

## Recommended classroom workflow

1. Prepare and test the worksheet, and verify the professor login.
2. Ask students to open the deployed URL and enter a name.
3. Let each student select and submit Scenario 1, then continue to Scenario 2.
4. Open Professor Mode, click **Refresh Results**, and discuss the distributions and paired Large-choice difference.
5. Download the CSV if you need a copy of the outcomes **before** resetting the experiment.

## Privacy and security

- **Names stay in Streamlit session state.** Students provide a name for the interface greeting, but new worksheet records explicitly keep `name_key` and `name` blank.
- **Responses are not necessarily anonymous to the hosting platform.** Hosting infrastructure and Google services may process access data; do not promise full anonymity beyond the specific spreadsheet fields.
- **Safeguard credentials.** Never publish a real `secrets.toml`, service-account JSON key, spreadsheet edit link with unintended permissions, or professor password. If a key is accidentally committed, revoke/rotate it and remove it from Git history.
- **Limit spreadsheet sharing.** Grant the service-account email Editor access and avoid making the response spreadsheet publicly editable. Restrict access to downloaded CSV files.
- **Destructive controls are authenticated, not audited.** The professor dashboard has a shared password, but there is no individual administrator identity log. Download the CSV or create a spreadsheet backup before reset.
- **Classroom consent.** Tell students that their choices and timestamps are saved to the configured Google Sheet, even though their entered names are not.

## Current limitations and design considerations

- **Names are session-only.** They are not written to the spreadsheet and cannot be used to find previous submissions. A lost browser session cannot reliably resume an in-progress response, and a new session may submit another row.
- **No randomized groups.** Every participant sees the same two scenarios in the same order, so this is a within-person classroom comparison, not a randomized A/B experiment.
- **No statistical-inference module.** The dashboard presents descriptive counts, percentages, and percentage-point differences; it does not compute confidence intervals or significance tests.
- **One-process concurrency control.** Google Sheets operations use a process-wide lock and retry certain temporary failures. The lock is not distributed across independent deployments or replicas; Google Sheets is suitable for small classroom exercises, not as a replacement for a transactional database at scale.
- **Shared-password administration.** Professor access is based on one password in Streamlit secrets, not individual accounts or granular permissions.
- **Manual dashboard refresh.** Results are not automatically refreshed in the background.
- **Reset is destructive.** Confirming Reset Experiment clears worksheet data in columns A-H from row 2 onward; download the CSV first if you want an archive.

## Troubleshooting

| Issue | What to check |
| --- | --- |
| `KeyError` or missing secrets | The TOML file contains `[gcp_service_account]`, `[google_sheet]`, and `[professor]` with the exact key names above |
| Google `SpreadsheetNotFound` / permission errors | The spreadsheet ID is correct and the sheet is shared with the service-account email as Editor |
| Worksheet not found | `worksheet_name` exactly matches the worksheet tab name |
| Header mismatch | Row 1 contains the eight schema fields in the expected order |
| Professor login fails | `[professor].password` is configured correctly; restart if secrets were just changed |
| Scenario 2 cannot update | The original session may have been lost after Scenario 1; see the session-only limitation above |
| Results look outdated | Click **Refresh Results** in Professor Mode |

## Developer checks

The archive contains **no automated test suite**. For a basic source-code syntax check from the repository root, run:

```bash
python -m py_compile Popcorn_Decoy.py
```

For a real integration test, use a **separate test spreadsheet**: initialize headers, submit both scenarios, check that the second answer updates the first row, open Professor Mode, verify the paired comparison and CSV export, and confirm reset clears data while keeping headers. Such a test will write to and clear the configured worksheet.

