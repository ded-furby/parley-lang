"""Bundled templates and metadata for Parley Workflows."""

WORKFLOW_TEMPLATES = {
    "clean-text": {
        "description": "Trim lines and remove blank rows from a text file.",
        "sample": "  first useful line  \n\nsecond useful line\n",
        "expected": "first useful line\nsecond useful line",
    },
    "log-summary": {
        "description": "Count log levels and collect error lines in Markdown.",
        "sample": (
            "INFO service started\n"
            "WARN cache is cold\n"
            "ERROR could not reach upstream\n"
            "INFO retry succeeded\n"
        ),
        "expected": (
            "# Log summary\n\n"
            "- Errors: 1\n"
            "- Warnings: 1\n"
            "- Info: 2\n\n"
            "## Error lines\n\n"
            "- ERROR could not reach upstream"
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
        "expected": (
            "# Checklist report\n\n"
            "- Total: 3\n"
            "- Complete: 1\n"
            "- Open: 2\n\n"
            "## Still open\n\n"
            "- - [ ] update changelog\n"
            "- - [ ] publish release"
        ),
    },
}
