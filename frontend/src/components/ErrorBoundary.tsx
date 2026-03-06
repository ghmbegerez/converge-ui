import { Component } from "react";
import type { ErrorInfo, ReactNode } from "react";

type Props = {
  children: ReactNode;
  fallback?: ReactNode;
  pageName?: string;
};

type State = {
  hasError: boolean;
  error: Error | null;
};

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error(
      `[ErrorBoundary] ${this.props.pageName ?? "unknown"}: ${error.message}`,
      { error, componentStack: info.componentStack },
    );
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }
      return (
        <div className="card" style={{ margin: "2rem", padding: "2rem" }}>
          <h2>Something went wrong</h2>
          <p>
            The <strong>{this.props.pageName ?? "page"}</strong> encountered an
            unexpected error. Try refreshing or navigating to another page.
          </p>
          <pre style={{ fontSize: "0.8rem", opacity: 0.7, marginTop: "1rem" }}>
            {this.state.error?.message}
          </pre>
          <button
            style={{ marginTop: "1rem" }}
            onClick={() => this.setState({ hasError: false, error: null })}
          >
            Try again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
