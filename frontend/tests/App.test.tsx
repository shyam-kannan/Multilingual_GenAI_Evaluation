import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import App from "../src/App";

const mockOverview = {
  locale_stats: {
    "en-US": { total_runs: 0, pass_rate: 0, avg_quality: 0, avg_hallucination: 0 },
    "es-MX": { total_runs: 0, pass_rate: 0, avg_quality: 0, avg_hallucination: 0 },
    "ar-SA": { total_runs: 0, pass_rate: 0, avg_quality: 0, avg_hallucination: 0 },
    "ja-JP": { total_runs: 0, pass_rate: 0, avg_quality: 0, avg_hallucination: 0 },
  },
  total_runs: 0,
  total_prompts: 0,
  recent_runs: [],
};

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn((url: string) => {
      if (url.includes("/dashboard/overview")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve(mockOverview),
        });
      }
      if (url.includes("/dashboard/ci-history")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve([]),
        });
      }
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve([]),
      });
    })
  );
});

describe("App", () => {
  it("renders the layout with nav", () => {
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>
    );
    expect(screen.getByText("Eval Gateway")).toBeTruthy();
    expect(screen.getByText("Overview")).toBeTruthy();
  });

  it("renders overview page by default", async () => {
    render(
      <MemoryRouter initialEntries={["/"]}>
        <App />
      </MemoryRouter>
    );
    await waitFor(() => {
      expect(screen.getByText("Evaluation Overview")).toBeTruthy();
    });
  });

  it("renders CI History page heading", async () => {
    render(
      <MemoryRouter initialEntries={["/ci"]}>
        <App />
      </MemoryRouter>
    );
    await waitFor(() => {
      expect(screen.getByText("No CI runs yet.")).toBeTruthy();
    });
  });
});
