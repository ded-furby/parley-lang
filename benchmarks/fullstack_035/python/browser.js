const readinessScore = (
  testsPassed,
  testsTotal,
  checklistDone,
  checklistTotal,
  packageReady,
) => {
  let score = 0;
  if (testsTotal > 0 && testsPassed === testsTotal) score += 60;
  if (checklistTotal > 0 && checklistDone === checklistTotal) score += 30;
  if (packageReady) score += 10;
  return BigInt(score);
};

export async function loadParley() {
  return { readiness_score: readinessScore };
}
