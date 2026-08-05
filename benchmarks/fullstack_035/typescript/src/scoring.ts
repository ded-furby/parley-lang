export type ReleaseInput = {
  version: string;
  tests_passed: number;
  tests_total: number;
  checklist_done: number;
  checklist_total: number;
  package_ready: boolean;
};

export type ReleaseAssessment = {
  version: string;
  ready: boolean;
  score: number;
  verdict: string;
  blockers: string[];
};

export function readinessScore(release: ReleaseInput): number {
  let score = 0;
  if (release.tests_total > 0 && release.tests_passed === release.tests_total) score += 60;
  if (release.checklist_total > 0 && release.checklist_done === release.checklist_total) score += 30;
  if (release.package_ready) score += 10;
  return score;
}

export function assessRelease(release: ReleaseInput): ReleaseAssessment {
  const blockers: string[] = [];
  if (release.tests_total <= 0) blockers.push("No test run was supplied.");
  else if (release.tests_passed !== release.tests_total) {
    blockers.push("The test suite is not fully passing.");
  }
  if (release.checklist_total <= 0) blockers.push("No release checklist was supplied.");
  else if (release.checklist_done !== release.checklist_total) {
    blockers.push("The release checklist is incomplete.");
  }
  if (!release.package_ready) blockers.push("The package artifact is not ready.");
  const score = readinessScore(release);
  const ready = score === 100;
  return {
    version: release.version,
    ready,
    score,
    verdict: ready
      ? "Ready — every declared release gate passed."
      : "Blocked — resolve the remaining release evidence.",
    blockers,
  };
}

export async function loadParley() {
  return {
    readiness_score: (
      testsPassed: number,
      testsTotal: number,
      checklistDone: number,
      checklistTotal: number,
      packageReady: boolean,
    ) => BigInt(readinessScore({
      version: "browser",
      tests_passed: testsPassed,
      tests_total: testsTotal,
      checklist_done: checklistDone,
      checklist_total: checklistTotal,
      package_ready: packageReady,
    })),
  };
}
