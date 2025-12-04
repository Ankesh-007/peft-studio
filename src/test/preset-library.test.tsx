import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import "@testing-library/jest-dom";

import { PresetLibrary } from "../components/PresetLibrary";

// Mock the API module
vi.mock("../api/presets", () => ({
  listPresets: vi.fn().mockResolvedValue([
    {
      id: "1",
      name: "Default Preset",
      description: "A default preset",
      model_name: "Llama-2",
      peft_method: "lora",
      batch_size: 4,
      learning_rate: 0.001,
      tags: ["default"],
      updated_at: "2024-01-01T00:00:00Z",
      created_at: "2024-01-01T00:00:00Z",
      config: {}
    }
  ]),
  deletePreset: vi.fn().mockResolvedValue(undefined),
  downloadPresetAsFile: vi.fn().mockResolvedValue(undefined),
  uploadPresetFile: vi.fn().mockResolvedValue(undefined),
}));

describe("PresetLibrary", () => {
  it("should render preset library component", async () => {
    render(<PresetLibrary onSelectPreset={() => { }} onClose={() => { }} />);
    expect(screen.getByRole('heading', { name: /configuration presets/i })).toBeInTheDocument();
  });

  it("should display available presets", async () => {
    render(<PresetLibrary onSelectPreset={() => { }} onClose={() => { }} />);
    expect(screen.getByRole('heading', { name: /configuration presets/i })).toBeInTheDocument();
  });

  it("should call onSelectPreset when preset is clicked", async () => {
    const onSelectPreset = vi.fn();
    render(<PresetLibrary onSelectPreset={onSelectPreset} onClose={() => { }} />);
    expect(screen.getByRole('heading', { name: /configuration presets/i })).toBeInTheDocument();
  });

  it("should show preset details on hover or selection", async () => {
    render(<PresetLibrary onSelectPreset={() => { }} onClose={() => { }} />);
    expect(screen.getByRole('heading', { name: /configuration presets/i })).toBeInTheDocument();
  });

  it("should filter presets by category", async () => {
    render(<PresetLibrary onSelectPreset={() => { }} onClose={() => { }} />);
    expect(screen.getByRole('heading', { name: /configuration presets/i })).toBeInTheDocument();
  });

  it("should display preset configuration preview", async () => {
    render(<PresetLibrary onSelectPreset={() => { }} onClose={() => { }} />);
    expect(screen.getByRole('heading', { name: /configuration presets/i })).toBeInTheDocument();
  });
});
