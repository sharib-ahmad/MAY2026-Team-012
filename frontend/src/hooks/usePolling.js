import { useEffect, useLayoutEffect, useRef } from "react";

/** Poll on an interval so lists update without manual refresh. */
export function usePolling(callback, intervalMs = 15000) {
  const callbackRef = useRef(callback);

  useLayoutEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  useEffect(() => {
    const id = setInterval(() => callbackRef.current(), intervalMs);
    return () => clearInterval(id);
  }, [intervalMs]);
}
