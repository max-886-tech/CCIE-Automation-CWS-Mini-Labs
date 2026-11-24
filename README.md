# CCIE Automation CWS Mini Labs

Two independent practice tasks for the Linux Candidate Workstation (CWS). The labs use local JSON fixtures and run offline under a regular user account.

| Task | Tools on the v1.1 CWS | Suggested time |
| --- | --- | --- |
| 01 VRF Route Change Planner | Python 3.9 standard library | 25 minutes |
| 02 CI Release Gate | Bash 5.0 and jq 1.6 | 20 minutes |

## Start a task

1. Open `QUESTION.md` in the task directory and read the requirements.
2. Work in `preconfig/`. It contains runnable starter files, sample inputs under `fixtures/`, and a verifier. The verifier exposes unfinished behavior before you implement the TODOs.
3. Run the verifier named in the question. `TASK_STEPS.md` explains the implementation and the expected results. `final_solution/` has the completed files and its own copy of the same fixtures and verifier.

From the extracted `CCIE-Automation-CWS-Mini-Labs` directory, use `cd 01-vrf-route-plan/preconfig` or `cd 02-ci-release-gate/preconfig` to begin.

The tool versions follow Cisco’s published [CCIE Automation v1.1 equipment and software list](https://learningcontent.cisco.com/documents/marketing/exam-topics/CCIE_Automation_equipment_list_v1.1.pdf).
