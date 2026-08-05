use serde::{Deserialize, Serialize};

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ReleaseInput {
    pub version: String,
    pub tests_passed: i64,
    pub tests_total: i64,
    pub checklist_done: i64,
    pub checklist_total: i64,
    pub package_ready: bool,
}

#[derive(Serialize)]
pub struct ReleaseAssessment {
    pub version: String,
    pub ready: bool,
    pub score: i64,
    pub verdict: String,
    pub blockers: Vec<String>,
}

pub fn readiness_score(
    tests_passed: i64,
    tests_total: i64,
    checklist_done: i64,
    checklist_total: i64,
    package_ready: bool,
) -> i64 {
    let mut score = 0;
    if tests_total > 0 && tests_passed == tests_total {
        score += 60;
    }
    if checklist_total > 0 && checklist_done == checklist_total {
        score += 30;
    }
    if package_ready {
        score += 10;
    }
    score
}

pub fn assess_release(release: ReleaseInput) -> ReleaseAssessment {
    let mut blockers = Vec::new();
    if release.tests_total <= 0 {
        blockers.push("No test run was supplied.".into());
    } else if release.tests_passed != release.tests_total {
        blockers.push("The test suite is not fully passing.".into());
    }
    if release.checklist_total <= 0 {
        blockers.push("No release checklist was supplied.".into());
    } else if release.checklist_done != release.checklist_total {
        blockers.push("The release checklist is incomplete.".into());
    }
    if !release.package_ready {
        blockers.push("The package artifact is not ready.".into());
    }
    let score = readiness_score(
        release.tests_passed,
        release.tests_total,
        release.checklist_done,
        release.checklist_total,
        release.package_ready,
    );
    let ready = score == 100;
    let verdict = if ready {
        "Ready — every declared release gate passed."
    } else {
        "Blocked — resolve the remaining release evidence."
    };
    ReleaseAssessment {
        version: release.version,
        ready,
        score,
        verdict: verdict.into(),
        blockers,
    }
}

#[unsafe(no_mangle)]
pub extern "C" fn parley_readiness_score(
    tests_passed: i64,
    tests_total: i64,
    checklist_done: i64,
    checklist_total: i64,
    package_ready: i32,
) -> i64 {
    readiness_score(
        tests_passed,
        tests_total,
        checklist_done,
        checklist_total,
        package_ready != 0,
    )
}
