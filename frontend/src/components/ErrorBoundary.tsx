"use client";

/**
 * React Error Boundary — prevents white-screen crashes in production.
 *
 * Wraps route segments. Shows a bilingual (EN/AR) fallback UI
 * with retry capability instead of crashing the entire app.
 */

import React, { Component, type ErrorInfo, type ReactNode } from "react";

interface ErrorBoundaryProps {
  children: ReactNode;
  /** Optional fallback component */
  fallback?: ReactNode;
  /** Section name for error reporting */
  section?: string;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Log to console in development, would send to monitoring in production
    console.error(
      `[ErrorBoundary${this.props.section ? ` — ${this.props.section}` : ""}]`,
      error,
      errorInfo.componentStack
    );
  }

  handleRetry = (): void => {
    this.setState({ hasError: false, error: null });
  };

  render(): ReactNode {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="flex items-center justify-center min-h-[200px] p-6">
          <div className="bg-red-50 border border-red-200 rounded-xl p-8 max-w-md w-full text-center">
            <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-6 h-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-red-800 mb-1">
              Something went wrong
            </h3>
            <p className="text-sm text-red-600 mb-1" dir="rtl">
              حدث خطأ غير متوقع
            </p>
            {this.props.section && (
              <p className="text-xs text-red-400 mb-4">
                Section: {this.props.section}
              </p>
            )}
            {this.state.error && (
              <p className="text-xs text-red-500 bg-red-100 rounded p-2 mb-4 font-mono break-all">
                {this.state.error.message}
              </p>
            )}
            <button
              onClick={this.handleRetry}
              className="px-6 py-2 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700 transition-colors"
            >
              Retry / إعادة المحاولة
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

/**
 * Next.js error.tsx boundary — for route-level error handling.
 * Export this as default from any route's error.tsx file.
 */
export function RouteErrorFallback({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="min-h-screen bg-io-bg flex items-center justify-center p-6">
      <div className="bg-white border border-red-200 rounded-2xl p-10 max-w-lg w-full text-center shadow-lg">
        <div className="w-16 h-16 bg-red-50 rounded-full flex items-center justify-center mx-auto mb-6">
          <svg className="w-8 h-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
        </div>
        <h2 className="text-xl font-bold text-io-primary mb-2">
          Pipeline Error
        </h2>
        <p className="text-sm text-io-secondary mb-1">
          An unexpected error occurred while processing your request.
        </p>
        <p className="text-sm text-io-secondary mb-6" dir="rtl">
          حدث خطأ غير متوقع أثناء معالجة طلبك
        </p>
        {error.message && (
          <div className="bg-io-bg border border-io-border rounded-lg p-3 mb-6">
            <p className="text-xs text-io-secondary font-mono break-all">{error.message}</p>
          </div>
        )}
        <div className="flex gap-3 justify-center">
          <button
            onClick={reset}
            className="px-6 py-2.5 bg-io-accent text-white rounded-lg text-sm font-semibold hover:bg-blue-800 transition-colors"
          >
            Try Again / إعادة المحاولة
          </button>
          <a
            href="/"
            className="px-6 py-2.5 border border-io-border text-io-secondary rounded-lg text-sm font-medium hover:bg-io-bg transition-colors"
          >
            Home / الرئيسية
          </a>
        </div>
      </div>
    </div>
  );
}
