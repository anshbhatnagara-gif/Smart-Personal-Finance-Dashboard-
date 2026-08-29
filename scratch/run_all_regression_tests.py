"""Execute the complete 13-suite multi-phase regression suite with real-time output."""

import subprocess
import sys
import os

TEST_FILES = [
    "scratch/phase_2_2_test.py",
    "scratch/phase_2_3_test.py",
    "scratch/phase_2_4_test.py",
    "scratch/phase_2_5_test.py",
    "scratch/phase_3_1_test.py",
    "scratch/phase_3_2_test.py",
    "scratch/phase_3_3_test.py",
    "scratch/phase_3_4_intelligence_test.py",
    "scratch/phase_3_5_proactive_insights_test.py",
    "scratch/phase_3_6_goal_planning_test.py",
    "scratch/phase_3_7_forecasting_risk_test.py",
    "scratch/phase_3_8_automation_test.py",
    "scratch/phase_3_9_intelligence_final_test.py"
]

def main():
    print("=" * 80, flush=True)
    print("EXECUTING FULL 13-SUITE MULTI-PHASE REGRESSION TEST HARNESS", flush=True)
    print("=" * 80, flush=True)

    total_suites = len(TEST_FILES)
    passed_suites = 0
    failed_suites = 0

    for idx, test_file in enumerate(TEST_FILES, 1):
        print(f"\n[{idx}/{total_suites}] Running {test_file} ...", flush=True)
        res = subprocess.run([sys.executable, test_file], capture_output=True, text=True)
        
        if res.returncode == 0:
            passed_suites += 1
            print(f"  --> PASS: {test_file}", flush=True)
        else:
            failed_suites += 1
            print(f"  --> FAIL: {test_file}", flush=True)
            print("  Output:\n", res.stdout[-800:] if res.stdout else "", flush=True)
            print("  Error:\n", res.stderr[-800:] if res.stderr else "", flush=True)

    print("\n" + "=" * 80, flush=True)
    print(f"REGRESSION SCORECARD: {passed_suites}/{total_suites} SUITES PASSED", flush=True)
    print("=" * 80, flush=True)

    if failed_suites > 0:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
