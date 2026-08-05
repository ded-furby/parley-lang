"""Bundled templates and metadata for Parley Workflows."""

WORKFLOW_TEMPLATES = {
    "clean-text": {
        "description": "Trim lines and remove blank rows from a text file.",
        "sample": "  first useful line  \n\nsecond useful line\n",
    },
    "log-summary": {
        "description": "Count log levels and collect error lines in Markdown.",
        "sample": (
            "INFO service started\n"
            "WARN cache is cold\n"
            "ERROR could not reach upstream\n"
            "INFO retry succeeded\n"
        ),
    },
    "checklist-report": {
        "description": "Summarize completed and open Markdown checklist items.",
        "sample": (
            "# Release checklist\n\n"
            "- [x] run tests\n"
            "- [ ] update changelog\n"
            "- [ ] publish release\n"
        ),
    },
}

