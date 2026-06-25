import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import LocaleBadge from "../src/components/LocaleBadge";
import EvalResultCard from "../src/components/EvalResultCard";
import CIRunRow from "../src/components/CIRunRow";
import type { CIRun } from "../src/types";

describe("LocaleBadge", () => {
  it("renders locale with pass rate", () => {
    render(<LocaleBadge locale="en-US" passRate={0.85} />);
    expect(screen.getByText("en-US: 85%")).toBeTruthy();
  });

  it("renders locale without pass rate when -1", () => {
    render(<LocaleBadge locale="ar-SA" passRate={-1} />);
    expect(screen.getByText("ar-SA")).toBeTruthy();
  });

  it("applies correct color for each locale", () => {
    const { container } = render(
      <LocaleBadge locale="ja-JP" passRate={0.5} />
    );
    expect(container.querySelector(".bg-red-100")).toBeTruthy();
  });
});

describe("EvalResultCard", () => {
  it("renders pass state", () => {
    render(
      <EvalResultCard
        title="Quality"
        passed={true}
        score={0.85}
        reasoning="Good response"
      />
    );
    expect(screen.getByText("Quality")).toBeTruthy();
    expect(screen.getByText("PASS")).toBeTruthy();
    expect(screen.getByText("85.0%")).toBeTruthy();
    expect(screen.getByText("Good response")).toBeTruthy();
  });

  it("renders fail state", () => {
    render(
      <EvalResultCard
        title="Moderation"
        passed={false}
        reasoning="Harmful content detected"
      />
    );
    expect(screen.getByText("FAIL")).toBeTruthy();
    expect(screen.getByText("Harmful content detected")).toBeTruthy();
  });

  it("renders details JSON when provided", () => {
    render(
      <EvalResultCard
        title="World Readiness"
        passed={true}
        reasoning="All checks passed"
        details={{ script: "ok", rtl: "ok" }}
      />
    );
    expect(screen.getByText(/"script"/)).toBeTruthy();
  });
});

describe("CIRunRow", () => {
  const mockRun: CIRun = {
    id: "abc12345-1234-1234-1234-123456789abc",
    prompt_id: "p1",
    candidate_version_id: "v1",
    baseline_version_id: null,
    status: "passed",
    regressions: [],
    details: {},
    created_at: "2025-01-01T00:00:00",
  };

  it("renders passed status", () => {
    const { container } = render(
      <table>
        <tbody>
          <CIRunRow run={mockRun} />
        </tbody>
      </table>
    );
    expect(screen.getByText("PASSED")).toBeTruthy();
    expect(screen.getByText("0 regression(s)")).toBeTruthy();
  });

  it("renders failed status with regressions", () => {
    const failedRun: CIRun = {
      ...mockRun,
      status: "failed",
      regressions: [
        {
          locale: "en-US",
          metric: "quality",
          baseline: 0.9,
          candidate: 0.5,
          delta: -0.4,
        },
      ],
    };
    render(
      <table>
        <tbody>
          <CIRunRow run={failedRun} />
        </tbody>
      </table>
    );
    expect(screen.getByText("FAILED")).toBeTruthy();
    expect(screen.getByText("1 regression(s)")).toBeTruthy();
  });
});
