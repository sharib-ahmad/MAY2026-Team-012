import { useEffect, useLayoutEffect, useRef } from "react";

/** Re-run a loader whenever the tab/window regains focus, so data that
 *  changed while the user was away (e.g. in another tab) shows up without
 *  a manual reload. */
export function useRefreshOnFocus(callback) {
  const callbackRef = useRef(callback);

  useLayoutEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  useEffect(() => {
    const onFocus = () => callbackRef.current();
    window.addEventListener("focus", onFocus);
    return () => window.removeEventListener("focus", onFocus);
  }, []);
}
