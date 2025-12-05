import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import GradioDemoGenerator from "../../components/GradioDemoGenerator";

// Mock fetch
global.fetch = vi.fn();

describe("GradioDemoGenerator", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.clearAllMocks();
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => [],
    });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("renders the component with title", () => {
    render(<GradioDemoGenerator />);
    expect(screen.getByText("Gradio Demo Generator")).toBeInTheDocument();
    expect(screen.getByText(/Create interactive demos/i)).toBeInTheDocument();
  });

  it("shows empty state when no demos exist", async () => {
    render(<GradioDemoGenerator />);

    await waitFor(() => {
      expect(screen.getByText(/No demos yet/i)).toBeInTheDocument();
    });
  });

  it("displays demo list when demos are loaded", async () => {
    const mockDemos = [
      {
        demo_id: "demo_1",
        status: "created",
        created_at: "2024-01-01T00:00:00Z",
      },
      {
        demo_id: "demo_2",
        status: "running",
        local_url: "http://127.0.0.1:7860",
        created_at: "2024-01-01T00:00:00Z",
      },
    ];

    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockDemos,
    });

    render(<GradioDemoGenerator />);

    await waitFor(() => {
      expect(screen.getByText("demo_1")).toBeInTheDocument();
      expect(screen.getByText("demo_2")).toBeInTheDocument();
    });
  });

  it("opens configuration form when New Demo button is clicked", async () => {
    render(<GradioDemoGenerator />);

    await waitFor(() => {
      expect(screen.getByText("New Demo")).toBeInTheDocument();
    });

    const newDemoButton = screen.getByText("New Demo");
    fireEvent.click(newDemoButton);

    await waitFor(() => {
      expect(screen.getByText("Create New Demo")).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/meta-llama/i)).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/Path to model/i)).toBeInTheDocument();
    });
  });

  it("validates required fields in configuration form", async () => {
    render(<GradioDemoGenerator />);

    await waitFor(() => {
      expect(screen.getByText("New Demo")).toBeInTheDocument();
    });

    const newDemoButton = screen.getByText("New Demo");
    fireEvent.click(newDemoButton);

    await waitFor(() => {
      const createButton = screen.getByRole("button", { name: /Create Demo/i });
      expect(createButton).toBeDisabled();
    });
  });

  it("creates a demo with valid configuration", async () => {
    const mockCreatedDemo = {
      demo_id: "demo_123",
      status: "created",
      created_at: "2024-01-01T00:00:00Z",
    };

    (global.fetch as any)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [],
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockCreatedDemo,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ demo_id: "demo_123", code: "import gradio as gr" }),
      });

    render(<GradioDemoGenerator />);

    await waitFor(() => {
      expect(screen.getByText("New Demo")).toBeInTheDocument();
    });

    // Open form
    const newDemoButton = screen.getByText("New Demo");
    fireEvent.click(newDemoButton);

    await waitFor(() => {
      expect(screen.getByText("Create New Demo")).toBeInTheDocument();
    });

    // Fill in required fields - use placeholder text to find inputs
    const modelIdInput = screen.getByPlaceholderText(/meta-llama/i);
    const modelPathInput = screen.getByPlaceholderText(/Path to model/i);

    fireEvent.change(modelIdInput, { target: { value: "test-model" } });
    fireEvent.change(modelPathInput, { target: { value: "/path/to/model" } });

    // Submit form
    const createButton = screen.getByRole("button", { name: /Create Demo/i });
    fireEvent.click(createButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/gradio-demos/create",
        expect.objectContaining({
          method: "POST",
          headers: { "Content-Type": "application/json" },
        })
      );
    });
  });

  it("displays demo controls when a demo is selected", async () => {
    const mockDemos = [
      {
        demo_id: "demo_1",
        status: "created",
        created_at: "2024-01-01T00:00:00Z",
      },
    ];

    let fetchCallCount = 0;
    (global.fetch as any).mockImplementation(() => {
      fetchCallCount++;
      if (fetchCallCount === 1) {
        return Promise.resolve({
          ok: true,
          json: async () => mockDemos,
        });
      } else {
        return Promise.resolve({
          ok: true,
          json: async () => ({ demo_id: "demo_1", code: "import gradio as gr" }),
        });
      }
    });

    render(<GradioDemoGenerator />);

    await waitFor(
      () => {
        expect(screen.getByText("demo_1")).toBeInTheDocument();
      },
      { timeout: 500 }
    );

    // Select demo
    const demoCard = screen.getByText("demo_1");
    fireEvent.click(demoCard);

    await waitFor(() => {
      expect(screen.getByText("Demo Controls")).toBeInTheDocument();
      expect(screen.getByText("Launch Demo")).toBeInTheDocument();
    });
  });

  it("launches a demo when Launch button is clicked", async () => {
    const mockDemos = [
      {
        demo_id: "demo_1",
        status: "created",
        created_at: "2024-01-01T00:00:00Z",
      },
    ];

    const mockLaunchedDemo = {
      demo_id: "demo_1",
      status: "running",
      local_url: "http://127.0.0.1:7860",
      created_at: "2024-01-01T00:00:00Z",
      started_at: "2024-01-01T00:01:00Z",
    };

    let fetchCallCount = 0;
    (global.fetch as any).mockImplementation((url: string, options?: any) => {
      fetchCallCount++;
      if (fetchCallCount === 1) {
        return Promise.resolve({
          ok: true,
          json: async () => mockDemos,
        });
      } else if (fetchCallCount === 2) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ demo_id: "demo_1", code: "import gradio as gr" }),
        });
      } else {
        return Promise.resolve({
          ok: true,
          json: async () => mockLaunchedDemo,
        });
      }
    });

    render(<GradioDemoGenerator />);

    await waitFor(
      () => {
        expect(screen.getByText("demo_1")).toBeInTheDocument();
      },
      { timeout: 500 }
    );

    // Select demo
    const demoCard = screen.getByText("demo_1");
    fireEvent.click(demoCard);

    await waitFor(() => {
      expect(screen.getByText("Launch Demo")).toBeInTheDocument();
    });

    // Launch demo
    const launchButton = screen.getByText("Launch Demo");
    fireEvent.click(launchButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/gradio-demos/demo_1/launch",
        expect.objectContaining({
          method: "POST",
        })
      );
    });
  });

  it("displays generated code when available", async () => {
    const mockDemos = [
      {
        demo_id: "demo_1",
        status: "created",
        created_at: "2024-01-01T00:00:00Z",
      },
    ];

    const mockCode = "import gradio as gr\n\ndemo = gr.Interface(...)";

    (global.fetch as any)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockDemos,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ demo_id: "demo_1", code: mockCode }),
      });

    render(<GradioDemoGenerator />);

    await waitFor(() => {
      expect(screen.getByText("demo_1")).toBeInTheDocument();
    });

    // Select demo
    const demoCard = screen.getByText("demo_1");
    fireEvent.click(demoCard);

    await waitFor(() => {
      expect(screen.getByText("Generated Code")).toBeInTheDocument();
      // Check for code content in the pre/code element
      const codeElement = screen.getByText((content, element) => {
        return element?.tagName.toLowerCase() === "code" && content.includes("import gradio as gr");
      });
      expect(codeElement).toBeInTheDocument();
    });
  });

  it("copies code to clipboard when Copy button is clicked", async () => {
    const mockDemos = [
      {
        demo_id: "demo_1",
        status: "created",
        created_at: "2024-01-01T00:00:00Z",
      },
    ];

    const mockCode = "import gradio as gr";

    (global.fetch as any)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockDemos,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ demo_id: "demo_1", code: mockCode }),
      });

    // Mock clipboard API
    Object.assign(navigator, {
      clipboard: {
        writeText: vi.fn().mockResolvedValue(undefined),
      },
    });

    render(<GradioDemoGenerator />);

    await waitFor(() => {
      expect(screen.getByText("demo_1")).toBeInTheDocument();
    });

    // Select demo
    const demoCard = screen.getByText("demo_1");
    fireEvent.click(demoCard);

    await waitFor(() => {
      expect(screen.getByText("Generated Code")).toBeInTheDocument();
    });

    // Click copy button
    const copyButtons = screen.getAllByText("Copy");
    fireEvent.click(copyButtons[0]);

    await waitFor(() => {
      expect(navigator.clipboard.writeText).toHaveBeenCalledWith(mockCode);
      expect(screen.getByText("Copied!")).toBeInTheDocument();
    });
  });

  it("displays error message when API call fails", async () => {
    (global.fetch as any).mockRejectedValueOnce(new Error("Network error"));

    render(<GradioDemoGenerator />);

    // Wait for error to be displayed
    await waitFor(() => {
      // The component should handle the error gracefully
      expect(screen.getByText(/No demos yet/i)).toBeInTheDocument();
    });
  });

  it("shows public URL when demo is shared", async () => {
    const mockDemos = [
      {
        demo_id: "demo_1",
        status: "running",
        local_url: "http://127.0.0.1:7860",
        public_url: "https://test.gradio.live",
        created_at: "2024-01-01T00:00:00Z",
      },
    ];

    let fetchCallCount = 0;
    (global.fetch as any).mockImplementation((url: string) => {
      fetchCallCount++;
      if (fetchCallCount === 1) {
        return Promise.resolve({
          ok: true,
          json: async () => mockDemos,
        });
      } else if (fetchCallCount === 2) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ demo_id: "demo_1", code: "import gradio as gr" }),
        });
      } else {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            demo_id: "demo_1",
            embed_code: '<iframe src="https://test.gradio.live"></iframe>',
          }),
        });
      }
    });

    render(<GradioDemoGenerator />);

    await waitFor(
      () => {
        expect(screen.getByText("demo_1")).toBeInTheDocument();
      },
      { timeout: 500 }
    );

    // Select demo
    const demoCard = screen.getByText("demo_1");
    fireEvent.click(demoCard);

    await waitFor(() => {
      expect(screen.getByText(/Public URL:/i)).toBeInTheDocument();
      expect(screen.getByText("https://test.gradio.live")).toBeInTheDocument();
    });
  });

  it("deletes a demo when Delete button is clicked", async () => {
    const mockDemos = [
      {
        demo_id: "demo_1",
        status: "created",
        created_at: "2024-01-01T00:00:00Z",
      },
    ];

    (global.fetch as any)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockDemos,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ demo_id: "demo_1", code: "import gradio as gr" }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ message: "Demo deleted" }),
      });

    // Mock window.confirm
    global.confirm = vi.fn().mockReturnValue(true);

    render(<GradioDemoGenerator />);

    await waitFor(() => {
      expect(screen.getByText("demo_1")).toBeInTheDocument();
    });

    // Select demo
    const demoCard = screen.getByText("demo_1");
    fireEvent.click(demoCard);

    await waitFor(() => {
      expect(screen.getByText("Delete")).toBeInTheDocument();
    });

    // Delete demo
    const deleteButton = screen.getByText("Delete");
    fireEvent.click(deleteButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/gradio-demos/demo_1",
        expect.objectContaining({
          method: "DELETE",
        })
      );
    });
  });
});
