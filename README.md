# Duke Treadmill Score

### [Open the Live Application →](https://abusuraihsakhri.github.io/duke-treadmill-score/)

A standalone browser calculator and Python CLI/API implementation of the **Duke Treadmill Score (DTS)** for prognostic stratification following exercise ECG. The browser calculator needs no server and works offline.

## Clinical definition

**DTS = exercise duration (minutes) − 5 × maximum net ST-segment deviation (mm) − 4 × treadmill angina index.**

The original score uses exercise duration on the **standard Bruce protocol** (or an appropriately converted equivalent). Angina index: 0 = none; 1 = non-limiting; 2 = exercise-limiting.

| Score | Prognostic stratum |
| --- | --- |
| ≥ +5 | Low |
| −10 to < +5 | Moderate |
| < −10 | High |

These categories do not establish coronary artery disease or independently determine management. Interpretation depends on the clinical context, test quality, and population studied.

**Reference:** Mark DB et al. Prognostic value of a treadmill exercise score in outpatients with suspected coronary artery disease. *N Engl J Med.* 1991;325:849–853. [doi:10.1056/NEJM199109193251204](https://doi.org/10.1056/NEJM199109193251204).

## Browser calculator

Open **web/index.html** directly in a current browser. Enter exercise duration, maximal ST deviation, and angina index; select **Calculate score**. The score, arithmetic breakdown, and category appear immediately. **Download CSV result** exports only numeric inputs and the score.

The browser application uses HTML and JavaScript, makes no API requests, saves nothing to browser storage, and requires no external scripts. The same static files can be hosted on GitHub Pages using the deployment job in .github/workflows/ci.yml. GitHub Pages must be enabled with **GitHub Actions** as the publishing source.

## Python CLI

Core score and CSV batch scoring need only Python 3.10+ (standard library):

~~~bash
python duke.py single --exercise-minutes 9 --st-deviation-mm 1 --angina-index 1
python duke.py single --json '{"exercise_minutes":9,"st_deviation_mm":1,"angina_index":1}'
python duke.py batch --input sample.csv --output results.csv
~~~

The single example yields **0 (moderate)**. CSV requires headers **exercise_minutes**, **st_deviation_mm**, and **angina_index**; additional columns are retained. All measurements must be finite and non-negative, and angina index must be 0, 1, or 2. Missing values cause errors rather than assuming zero. Spreadsheet formula-like cells in passthrough columns are neutralized on CSV export.

## Local API

~~~bash
python -m pip install -r requirements.txt
python cli.py serve --host 127.0.0.1 --port 8000
~~~

The API serves the same browser application at http://127.0.0.1:8000/ and provides the clinical score endpoint:

~~~bash
curl -s http://127.0.0.1:8000/api/duke \
  -H 'Content-Type: application/json' \
  -d '{"exercise_minutes":9,"st_deviation_mm":1,"angina_index":1}'
~~~

Current API schemas are generated automatically at **/openapi.json** and interactive documentation is served at **/docs**.

### Separate legacy task-audit demonstration

The existing generic worker/audit subsystem remains available through **cli.py audit/chat/batch/verify-audit** and endpoints **/api/audit**, **/api/chat**, **/api/audit/logs**, and **/metrics**. Its generic QC thresholds and alerts are **not Duke Treadmill Score calculations** and have not been clinically validated. The chat responder returns demonstration text, not a medical assessment.

### Docker

~~~bash
docker compose up --build
~~~

Compose exposes port 8000 only on 127.0.0.1 by default. The API has no authentication and must not be publicly exposed without additional controls.

## Tests

~~~bash
python -m pip install -r requirements.txt
python -m pytest -q
node --test web/calculator.test.cjs
~~~

CI tests Python 3.10–3.12 and Node.js 22, then attempts GitHub Pages publishing after a successful push to master.

## Privacy and limitations

- The static calculator computes locally, without uploads, external JavaScript, or persistent storage.
- The optional API and CLI process local inputs; the legacy audit demonstration stores its registry and audit trail in process memory.
- Legacy regex identifier detection is **not comprehensive de-identification** and does not establish HIPAA compliance. Do not enter identifiable patient data.
- Audit records use HMAC-SHA256 signatures while the process is running. The generated key and trail are not persistently stored.
- The application has not undergone independent clinical software validation and is intended for education and research, not autonomous clinical decision-making.

## Technology and license

Python 3.10+, FastAPI/Pydantic for the optional API, and standard HTML/JavaScript for the browser interface. Compatible with current Chromium, Firefox, and Safari browsers. [MIT License](LICENSE).
