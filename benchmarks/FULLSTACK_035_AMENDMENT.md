# Protocol amendment 035-r2

The first unmeasured correctness smoke on 2026-08-05 exposed one protocol
transcription error before a complete four-language result existed. Frozen
Parley v0.4.0 returned the documented 415 error code
`json_content_type_required`; `fullstack_035_cases.json` had incorrectly assumed
the new name `unsupported_media_type`.

Evidence from the stopped smoke:

```json
{
  "case": "wrong_media_type",
  "status": 415,
  "actual_error": "json_content_type_required",
  "incorrect_expected_error": "unsupported_media_type",
  "parley_browser_case": "pass"
}
```

The smoke stopped when TypeScript could not resolve packages from the temporary
build directory. It did not produce a result file, source-token verdict,
performance measurement, Rust judgment, or complete four-language comparison.

Revision 2 changes only the `wrong_media_type.expected_error` value to match the
already-frozen product contract. No status, input, success value, task, metric,
gate, Parley source, compiler source, or instruction changed. All baselines must
return the same corrected code. The original commit and case hash remain in git
history; the amended hash is recorded in the protocol before measured execution.
