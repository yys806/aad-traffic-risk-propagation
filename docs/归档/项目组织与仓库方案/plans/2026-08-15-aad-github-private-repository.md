# AAD GitHub Private Repository Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Turn D:/shen/TJU/AAD into a filtered Git repository and publish the approved code, paper, and project documentation to the private GitHub repository aad-traffic-risk-propagation.

**Architecture:** Use the AAD root as the local repository so code, paper sources, handoff files, and project navigation share one history. Keep local literature PDFs, raw data, generated outputs, caches, temporary files, credentials, and the read-only DRIFT project outside version control through explicit ignore rules and staged-path audits.

**Tech Stack:** Git 2.50.1, PowerShell, Python/pytest, GitHub web UI through the authenticated browser session, Markdown and LaTeX project files.

---

### Task 1: Establish a safe pre-initialization baseline

**Files:** Read D:/shen/TJU/AAD/.gitignore, the approved design spec, and read-only D:/shen/TJU/DRIFT.

- [ ] **Step 1: Confirm AAD is not already a Git worktree**

Run:

~~~powershell
git -C 'D:/shen/TJU/AAD' rev-parse --is-inside-work-tree
~~~

Expected: exit code 128 with not a git repository. If it reports a repository, stop and inspect it before changing anything.

- [ ] **Step 2: Capture protected AAD hashes**

Run:

~~~powershell
Get-FileHash -Algorithm SHA256 -LiteralPath 'D:/shen/TJU/AAD/paper/主论文/main.tex','D:/shen/TJU/AAD/paper/主论文/main.pdf','D:/shen/TJU/AAD/docs/superpowers/specs/2026-08-14-frozen-nc-results-structure.md'
~~~

Expected: main.tex SHA-256 5F05B18CEFC6BD3A8A543EC81DDC248BCB81D3B81381A5466D24CF4CAAE4671D; main.pdf SHA-256 B0F46EE8D8F71ECEB8E0E5D5B888208A537C35126C2BCC5CDDD66A75125D5FA0; frozen Results specification SHA-256 4E5A10BDF786DBAD5B633461577CFC2390A26C2944D431EF133715EB283E7A63.

- [ ] **Step 3: Capture the DRIFT read-only baseline**

Run:

~~~powershell
git -C 'D:/shen/TJU/DRIFT' rev-parse HEAD
git -C 'D:/shen/TJU/DRIFT' status --short
~~~

Expected: HEAD 58397fb2834e238d5d4d5e72d0307f1d09674b48 and no status entries. Do not initialize, stage, commit, or push anything in DRIFT.

### Task 2: Define the repository filter

**Files:** Modify D:/shen/TJU/AAD/.gitignore.

- [ ] **Step 1: Append explicit exclusions without deleting existing rules**

Append:

~~~gitignore
.venv/
venv/
env/
.env
.env.*
*.pem
*.key
__pycache__/
.pytest_cache/
*.py[cod]
node_modules/
literature/
code/outputs/
code/real_data/**/*.csv
code/real_data/**/*.json
code/real_data/**/*.jsonl
code/real_data/**/*.zip
code/real_data/**/*.parquet
code/real_data/**/*.sqlite
docs/research/**/datasets/
docs/research/**/nc_papers/
docs/research/**/dataset_papers/
tmp/
*.log
paper/**/build/
paper/**/validation/
paper/**/*.aux
paper/**/*.bbl
paper/**/*.blg
paper/**/*.fls
paper/**/*.fdb_latexmk
paper/**/*.log
paper/**/*.out
paper/**/*.synctex.gz
~~~

Do not ignore paper PDF, DOCX, or TEX files; they are approved for backup.

- [ ] **Step 2: Validate representative paths**

Run git check-ignore -v for one path under literature, one under code/outputs, one under tmp, and confirm that code/src/riskprop/events.py and paper/主论文/main.tex are not ignored.

### Task 3: Initialize AAD and audit the candidate set

**Files:** Create D:/shen/TJU/AAD/.git; modify only the Git index.

- [ ] **Step 1: Initialize the local repository**

From D:/shen/TJU/AAD run:

~~~powershell
git init -b main
git config user.name "AAD Research Maintainer"
git config user.email "aad-maintainer@users.noreply.github.com"
~~~

Expected: new repository on branch main; no remote yet.

- [ ] **Step 2: Stage the approved allowlist**

Run:

~~~powershell
git add -- .gitignore README.md '毕业设计与论文课题固化.md' '类超距作用理论整理_2026-08-08.md' '下一周对话交接_2026-07-29.md' '新对话完整交接_2026-08-15.md' docs code paper tests
~~~

This explicit allowlist must be used; do not run git add ..

- [ ] **Step 3: Reject forbidden staged paths**

Inspect git diff --cached --name-only and fail if any staged path starts with literature/, code/outputs/, tmp/, .pytest_cache/, or __pycache__/.

- [ ] **Step 4: Reject oversized or secret-named staged files**

Inspect staged file sizes and fail if any file is 90 MB or larger, or if a staged path ends in .env, .pem, or .key. Run git diff --cached --check and require exit code 0.

### Task 4: Run tests and create the initial commit

**Files:** Create local Git history only.

- [ ] **Step 1: Run AAD tests**

From D:/shen/TJU/AAD/code run:

~~~powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -m pytest -q -p no:cacheprovider
~~~

Expected: 75 passed.

- [ ] **Step 2: Run SPMD tests**

From D:/shen/TJU/AAD run:

~~~powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -m pytest -q -p no:cacheprovider tests/real_data/spmd
~~~

Expected: 4 passed.

- [ ] **Step 3: Create and verify the first commit**

Run:

~~~powershell
git commit -m "chore: establish AAD research repository"
git log -1 --oneline --decorate
git status --short
~~~

Expected: one root commit on main, clean status, and no forbidden path in git ls-tree -r --name-only HEAD.

### Task 5: Create and push the GitHub Private remote

**Files:** External GitHub repository aad-traffic-risk-propagation; local .git/config remote entry.

- [ ] **Step 1: Run the web-access prerequisite check**

Run:

~~~powershell
node "C:/Users/Lenovo/.codex/skills/web-access/scripts/check-deps.mjs"
~~~

Expected: exit code 0. If login or browser setup is required, stop and report the exact instruction.

- [ ] **Step 2: Create the remote through the authenticated browser**

Open https://github.com/new in a new background tab without touching existing tabs. Verify the intended owner, set repository name aad-traffic-risk-propagation, set Private, and choose not to initialize README, .gitignore, or license. Stop if the name is occupied or the owner is unexpected.

- [ ] **Step 3: Add the exact GitHub URL and push**

Run from D:/shen/TJU/AAD:

Run git remote add origin followed by the exact HTTPS clone URL displayed by GitHub, then run:

~~~powershell
git push -u origin main
~~~

Never embed tokens in the URL.

### Task 6: Verify and record repository management

**Files:** Verify local Git, GitHub page, protected AAD hashes, and read-only DRIFT.

- [ ] **Step 1: Verify local and remote commit identity**

Run git rev-parse HEAD, git rev-parse origin/main, and git status --short --branch; require equal commit IDs and clean main...origin/main.

- [ ] **Step 2: Verify the GitHub page**

Confirm Private visibility, default main branch, presence of code/, paper/, docs/, and approved root files, and absence of literature/, code/outputs/, tmp/, and raw data.

- [ ] **Step 3: Recheck protected hashes and DRIFT**

Repeat Task 1 Steps 2 and 3; all hashes and the DRIFT HEAD/status must match the baseline.

- [ ] **Step 4: Record the remote in docs/项目导航.md**

Append the repository name, Private visibility, and the rule that literature, raw data, outputs, and DRIFT remain outside Git. Commit and push this documentation-only change, then repeat Step 1.

No worktree or commit operation is performed in DRIFT.
