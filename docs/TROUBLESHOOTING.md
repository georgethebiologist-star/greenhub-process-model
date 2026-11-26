# Troubleshooting

## Python or Node.js was not found

Install CPython 3.12.x and Node.js 24.x with Corepack from the official links in the [user guide](USER_GUIDE.md). On Windows, enable **Add python.exe to PATH** in the Python installer, then close and reopen PowerShell.

## PowerShell will not run the launcher

Open PowerShell in `Model` and use `powershell -ExecutionPolicy Bypass -File .\launch.ps1`. This applies the bypass to that launch command only; follow any organization-managed device policy.

## Dependency installation fails

Check the internet connection and rerun `launch.ps1`; package installation is safe to repeat. Review `%TEMP%\GreenHub\logs\api.log` and `ui.log`. Python packages install into `.venv`, not the system Python. To retry setup, close GreenHub first and remove only the project's `.venv` folder, then launch again.

## Browser page does not load or API is unavailable

Keep the launcher window open. If ports 3000 or 8000 are already in use, stop the other application using them and restart GreenHub. Check both launcher logs under `%TEMP%\GreenHub\logs`. The UI forwards scientific requests to the Python service; a UI page alone does not mean the model API is ready.

## A run reports warnings or incomplete results

Warnings are model evidence and should not be hidden. Check the run assumptions and validation report, plus [model limitations](model_limitations.md), [scientific assumptions](scientific_assumptions.md), and the related stage methodology. A successful HTTP response does not imply experimental or industrial validation.

## Restarting

Press Ctrl+C in the PowerShell window used to launch GreenHub, wait for it to return to the prompt, then run the launcher again. If a service exited unexpectedly, inspect the log files before restarting.
