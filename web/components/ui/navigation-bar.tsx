"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

type Ctx = {
  visible: boolean;
  show: () => void;
  hide: () => void;
};

const NavigationProgressContext = createContext<Ctx | null>(null);

export function useNavigationProgress() {
  const ctx = useContext(NavigationProgressContext);
  if (!ctx) {
    throw new Error("useNavigationProgress must be used within NavigationProgressProvider");
  }
  return ctx;
}

export function NavigationProgressProvider({ children }: { children: ReactNode }) {
  const [visible, setVisible] = useState(false);
  const show = useCallback(() => setVisible(true), []);
  const hide = useCallback(() => setVisible(false), []);

  useEffect(() => {
    if (!visible) return;
    // Safety backstop: auto-hide after 8s if hide() is never called
    // (navigation error, unmounted consumer, etc.). Not a loading-complete signal.
    const id = window.setTimeout(hide, 8000);
    return () => window.clearTimeout(id);
  }, [visible, hide]);

  const value = useMemo(() => ({ visible, show, hide }), [visible, show, hide]);

  return (
    <NavigationProgressContext.Provider value={value}>
      {children}
      <NavigationBar />
    </NavigationProgressContext.Provider>
  );
}

function NavigationBar() {
  const { visible } = useNavigationProgress();
  if (!visible) return null;
  return (
    <div
      aria-hidden="true"
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        height: 3,
        background: "#1f242b",
        zIndex: 9999,
        overflow: "hidden",
      }}
    >
      <div className="nav-bar-fill" />
      <style href="nav-bar" precedence="default">{`
        .nav-bar-fill {
          position: absolute;
          top: 0; bottom: 0; left: -40%;
          width: 40%;
          background: linear-gradient(90deg, transparent, #3DFF7A 60%, transparent);
          box-shadow: 0 0 12px #3DFF7A88;
          animation: nav-slide 1.4s cubic-bezier(.65,.05,.36,1) infinite;
        }
        @keyframes nav-slide { to { left: 100%; } }
        @media (prefers-reduced-motion: reduce) {
          .nav-bar-fill {
            animation: none;
            left: 30%;
          }
        }
      `}</style>
    </div>
  );
}
